"""
Main repository analysis Celery task pipeline.
Orchestrates: fetch → parse → embed → graph → analyze → issue analysis.
"""
import asyncio
from datetime import datetime
import structlog

from celery_app import celery_app

log = structlog.get_logger()


@celery_app.task(bind=True, name="tasks.analyze_repo.full_analysis", queue="analysis")
def full_analysis(self, repo_id: str, owner: str, repo_name: str, github_token: str = None):
    """
    Full repository analysis pipeline. Called when a user submits a repo URL.
    Runs as a Celery background task.
    """
    asyncio.run(_run_full_analysis(self, repo_id, owner, repo_name, github_token))


async def _run_full_analysis(task, repo_id: str, owner: str, repo_name: str, github_token: str = None):
    """Async implementation of the analysis pipeline."""
    from database import AsyncSessionLocal
    from models.repository import Repository, AnalysisStatus
    from models.issue import Issue
    from services.github_service import GitHubService
    from services.agent_service import get_agent_service
    from services.rag_service import get_rag_service
    from services.graph_service import get_graph_service
    from sqlalchemy import select

    github = GitHubService(github_token)
    agent = get_agent_service()
    rag = get_rag_service()
    graph = get_graph_service()

    async def update_progress(stage: str, progress: int):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Repository).where(Repository.id == repo_id))
            repo = result.scalar_one_or_none()
            if repo:
                repo.analysis_stage = stage
                repo.analysis_progress = progress
                repo.analysis_status = AnalysisStatus.RUNNING
                await db.commit()
        task.update_state(state="PROGRESS", meta={"stage": stage, "progress": progress})
        log.info("Analysis progress", stage=stage, progress=progress, repo=f"{owner}/{repo_name}")

    try:
        # ── Stage 1: Fetch repository data ─────────────────
        await update_progress("Fetching repository data", 5)
        repo_data, languages, readme, file_tree_data = await asyncio.gather(
            github.get_repo(owner, repo_name),
            github.get_repo_languages(owner, repo_name),
            github.get_readme(owner, repo_name),
            github.get_repo_tree(owner, repo_name),
        )

        file_tree = file_tree_data.get("tree", [])
        code_files = [f for f in file_tree if f.get("type") == "blob" and _is_code_file(f.get("path", ""))]

        # ── Stage 2: LLM Architecture Analysis ────────────
        await update_progress("Analyzing architecture", 20)
        analysis = await agent.analyze_repository(repo_data, readme, file_tree, languages)

        # ── Stage 3: Generate subsystems ──────────────────
        await update_progress("Identifying subsystems", 35)
        if not analysis.get("subsystems"):
            analysis["subsystems"] = await agent.generate_subsystems(repo_data, file_tree, readme or "")

        # ── Stage 4: Save initial analysis results ─────────
        await update_progress("Saving analysis", 40)
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Repository).where(Repository.id == repo_id))
            repo = result.scalar_one_or_none()
            if repo:
                repo.purpose = analysis.get("purpose")
                repo.tech_stack = analysis.get("tech_stack")
                repo.architecture_summary = analysis.get("architecture_summary")
                repo.main_modules = analysis.get("main_modules")
                repo.subsystems = analysis.get("subsystems")
                repo.architecture_diagram = {
                    "nodes": analysis.get("architecture_nodes", []),
                    "edges": analysis.get("architecture_edges", []),
                }
                repo.difficulty_level = analysis.get("difficulty_level", "intermediate")
                repo.contribution_areas = analysis.get("contribution_opportunities")
                repo.learning_prerequisites = analysis.get("learning_prerequisites")
                repo.file_tree = {"tree": file_tree[:500]}  # Store first 500 entries
                await db.commit()

        # ── Stage 5: Build Neo4j graph ─────────────────────
        await update_progress("Building knowledge graph", 50)
        await graph.upsert_repository(repo_id, f"{owner}/{repo_name}", {
            "description": repo_data.get("description", ""),
            "stars": repo_data.get("stargazers_count", 0),
            "language": repo_data.get("language", ""),
        })

        for f in file_tree[:300]:  # Index first 300 files
            if f.get("type") == "blob":
                await graph.upsert_file(
                    repo_id, f"{owner}/{repo_name}",
                    f.get("path", ""), _get_file_type(f.get("path", "")), f.get("size", 0)
                )

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Repository).where(Repository.id == repo_id))
            repo = result.scalar_one_or_none()
            if repo:
                repo.graph_built = True
                await db.commit()

        # ── Stage 6: Index README into Qdrant ─────────────
        await update_progress("Indexing documentation", 60)
        if readme:
            await rag.index_document(repo_id, "README.md", readme, {"repo": f"{owner}/{repo_name}"})

        # ── Stage 7: Index key code files ─────────────────
        await update_progress("Indexing codebase", 70)
        files_to_index = code_files[:50]  # Index up to 50 code files
        for i, file_info in enumerate(files_to_index):
            try:
                content = await github.get_file_content(owner, repo_name, file_info["path"])
                if content and len(content) > 50:
                    await rag.index_file(repo_id, file_info["path"], content, {"repo": f"{owner}/{repo_name}"})
            except Exception as e:
                log.warning("Failed to index file", path=file_info["path"], error=str(e))

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Repository).where(Repository.id == repo_id))
            repo = result.scalar_one_or_none()
            if repo:
                repo.embeddings_indexed = True
                await db.commit()

        # ── Stage 8: Analyze issues ────────────────────────
        await update_progress("Analyzing issues", 85)
        try:
            raw_issues = await github.get_issues(owner, repo_name, state="open", per_page=30)
            async with AsyncSessionLocal() as db:
                for raw in raw_issues[:20]:
                    issue = Issue(
                        repository_id=repo_id,
                        github_issue_id=raw["id"],
                        number=raw["number"],
                        title=raw["title"],
                        body=raw.get("body", ""),
                        state=raw.get("state", "open"),
                        labels=[l["name"] for l in raw.get("labels", [])],
                        comments_count=raw.get("comments", 0),
                        github_url=raw.get("html_url", ""),
                        github_created_at=datetime.fromisoformat(raw["created_at"].replace("Z", "+00:00")),
                        difficulty=_predict_difficulty(raw),
                        required_skills=_extract_required_skills(raw, analysis.get("tech_stack", [])),
                    )
                    db.add(issue)
                await db.commit()

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Repository).where(Repository.id == repo_id))
                repo = result.scalar_one_or_none()
                if repo:
                    repo.issues_analyzed = True
                    await db.commit()
        except Exception as e:
            log.warning("Issue analysis failed", error=str(e))

        # ── Stage 9: Complete ──────────────────────────────
        await update_progress("Completed", 100)
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Repository).where(Repository.id == repo_id))
            repo = result.scalar_one_or_none()
            if repo:
                repo.analysis_status = AnalysisStatus.COMPLETED
                repo.last_analyzed = datetime.utcnow()
                await db.commit()

        log.info("Analysis complete", repo=f"{owner}/{repo_name}")

    except Exception as e:
        log.error("Analysis failed", repo=f"{owner}/{repo_name}", error=str(e))
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Repository).where(Repository.id == repo_id))
            repo = result.scalar_one_or_none()
            if repo:
                repo.analysis_status = AnalysisStatus.FAILED
                await db.commit()
        raise


def _is_code_file(path: str) -> bool:
    extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
                  ".cpp", ".c", ".h", ".rb", ".php", ".swift", ".kt", ".scala"}
    return any(path.endswith(ext) for ext in extensions)


def _get_file_type(path: str) -> str:
    if path.endswith((".py",)): return "python"
    if path.endswith((".js", ".jsx")): return "javascript"
    if path.endswith((".ts", ".tsx")): return "typescript"
    if path.endswith((".go",)): return "go"
    if path.endswith((".rs",)): return "rust"
    if path.endswith((".md",)): return "markdown"
    return "other"


def _predict_difficulty(issue: dict) -> str:
    """Simple heuristic difficulty prediction."""
    labels = [l["name"].lower() for l in issue.get("labels", [])]
    if any(l in labels for l in ["good first issue", "easy", "beginner", "starter"]):
        return "easy"
    if any(l in labels for l in ["hard", "complex", "expert", "advanced"]):
        return "hard"
    # Heuristic: longer issues are usually harder
    body_len = len(issue.get("body") or "")
    if body_len > 2000:
        return "hard"
    if body_len > 500:
        return "medium"
    return "easy"


def _extract_required_skills(issue: dict, tech_stack: list) -> list[str]:
    """Extract likely required skills from issue labels and body."""
    skills = set()
    body = (issue.get("body") or "").lower()
    title = issue.get("title", "").lower()
    text = f"{title} {body}"

    skill_keywords = {
        "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
        "react": "React", "vue": "Vue.js", "docker": "Docker",
        "kubernetes": "Kubernetes", "sql": "SQL", "api": "REST APIs",
        "authentication": "Authentication", "testing": "Testing",
        "database": "Database", "redis": "Redis", "graphql": "GraphQL",
    }
    for keyword, skill in skill_keywords.items():
        if keyword in text:
            skills.add(skill)

    # Add relevant tech stack items
    for tech in tech_stack[:3]:
        skills.add(tech)

    return list(skills)[:8]
