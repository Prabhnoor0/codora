"""
repo_intel.py — Live repository intelligence endpoints.

All endpoints work WITHOUT requiring a prior Celery analysis job —
they fetch data directly from GitHub + LLM in real time.
Designed to complement the existing /api/repositories/* (Celery-heavy) endpoints.

New endpoints:
  GET  /api/intel/{owner}/{repo}/explain          — Full repo explainer
  GET  /api/intel/{owner}/{repo}/subsystems       — Cluster files into subsystems
  GET  /api/intel/{owner}/{repo}/walkthrough      — Guided tour plan
  GET  /api/intel/{owner}/{repo}/learning-path    — Personalized learning roadmap
  GET  /api/intel/{owner}/{repo}/file-explain     — Explain any file/function
  POST /api/intel/{owner}/{repo}/predict-files    — Affected file predictor
  GET  /api/intel/{owner}/{repo}/readiness        — Contribution readiness for an issue
  POST /api/intel/{owner}/{repo}/pr-review        — AI PR reviewer
  GET  /api/intel/{owner}/{repo}/knowledge-gaps   — What user needs to learn for this repo
"""
import asyncio
import json
import re
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from routers.deps import get_current_user
from services.github_service import GitHubService
from services.llm_service import get_llm_service

router = APIRouter()
log = structlog.get_logger()

# ─── Helpers ────────────────────────────────────────────────────────────────

async def _fetch_repo_context(github: GitHubService, owner: str, repo: str):
    """Gather core repo data concurrently."""
    results = await asyncio.gather(
        github.get_repo(owner, repo),
        github.get_repo_languages(owner, repo),
        github.get_readme(owner, repo),
        github.get_file_tree(owner, repo),
        return_exceptions=True,
    )
    repo_data = results[0] if not isinstance(results[0], Exception) else {}
    languages  = results[1] if not isinstance(results[1], Exception) else {}
    readme     = results[2] if not isinstance(results[2], Exception) else ""
    file_tree  = results[3] if not isinstance(results[3], Exception) else []
    return repo_data, languages, readme, file_tree


def _file_tree_summary(file_tree: list, max_files: int = 120) -> str:
    if not file_tree:
        return "No file tree available."
    paths = [f.get("path", "") for f in file_tree if f.get("type") == "blob"][:max_files]
    return "\n".join(paths)


# ─── 1. Repository Explainer ─────────────────────────────────────────────────

@router.get("/{owner}/{repo}/tree")
async def get_repo_tree(
    owner: str,
    repo: str,
    current_user=Depends(get_current_user),
):
    """Return the raw file tree to render a clickable file explorer on the frontend."""
    github = GitHubService(current_user.github_access_token)
    try:
        tree = await github.get_file_tree(owner, repo)
        # Filter to blobs only (files) to keep it simple, or keep trees for folders
        files = [f.get("path") for f in tree if f.get("type") == "blob"]
        return {"files": files}
    except Exception as e:
        log.warning("Failed to fetch file tree", error=str(e))
        return {"files": []}

@router.get("/{owner}/{repo}/explain")
async def explain_repository(
    owner: str,
    repo: str,
    current_user=Depends(get_current_user),
):
    """
    Full repository explainer: purpose, tech stack, architecture,
    main components, difficulty, required knowledge, contribution areas.
    """
    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()

    repo_data, languages, readme, file_tree = await _fetch_repo_context(github, owner, repo)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")

    tree_summary = _file_tree_summary(file_tree)
    lang_list = ", ".join(f"{k} ({v:.0f}%)" for k, v in
                          sorted(languages.items(), key=lambda x: -x[1])[:8]) if languages else "Unknown"

    system = """You are an expert, highly patient code educator. Your audience is a complete beginner.
You MUST hold their hand and explain everything in extreme detail. Do NOT give 1-liner descriptions.
Return JSON:
{
  "purpose": "Extremely detailed, multi-paragraph explanation (at least 3-4 paragraphs) of what this project does, why it exists, and how it helps developers.",
  "tech_stack": ["Technology1", "Technology2", ...],
  "architecture_summary": "Extremely detailed, multi-paragraph explanation of the architecture. Explain it simply as if they are a beginner.",
  "main_components": [{"name": "ComponentName", "role": "Highly detailed explanation of what this component does and why it exists", "files": ["file1.ts", "file2.ts"]}],
  "difficulty": "beginner|intermediate|advanced",
  "required_knowledge": ["Concept1", "Concept2", ...],
  "contribution_areas": [{"area": "AreaName", "description": "what needs work", "good_for": "beginners|intermediate|advanced"}],
  "quick_facts": {"stars": 0, "main_language": "Python", "license": "MIT", "last_active": "active"}
}
Return ONLY valid JSON. No markdown fences."""

    user_prompt = f"""Repository: {owner}/{repo}
Description: {repo_data.get('description', 'N/A')}
Stars: {repo_data.get('stargazers_count', 0)} | Forks: {repo_data.get('forks_count', 0)}
Languages: {lang_list}
Topics: {', '.join(repo_data.get('topics', []))}
Open Issues: {repo_data.get('open_issues_count', 0)}

README (first 3000 chars):
{(readme or '')[:3000]}

File tree (first 120 files):
{tree_summary[:4000]}"""

    try:
        result = await llm.complete_json(system, user_prompt)
        result["full_name"] = f"{owner}/{repo}"
        result["html_url"] = repo_data.get("html_url", f"https://github.com/{owner}/{repo}")
        result["stars"] = repo_data.get("stargazers_count", 0)
        result["forks"] = repo_data.get("forks_count", 0)
        result["languages"] = languages
        return result
    except Exception as e:
        log.warning("Repo explain LLM failed", error=str(e))

    # Fallback
    return {
        "full_name": f"{owner}/{repo}",
        "purpose": repo_data.get("description", ""),
        "tech_stack": list(languages.keys()),
        "architecture_summary": "",
        "main_components": [],
        "difficulty": "intermediate",
        "required_knowledge": list(languages.keys()),
        "contribution_areas": [],
        "html_url": repo_data.get("html_url", ""),
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "languages": languages,
    }


# ─── 2. Subsystems (Code Knowledge Graph Clusters) ───────────────────────────

@router.get("/{owner}/{repo}/subsystems")
async def get_subsystems(
    owner: str,
    repo: str,
    current_user=Depends(get_current_user),
):
    """
    Cluster the file tree into named subsystems (Auth, DB, API, etc.)
    with file lists, key concepts, and complexity ratings.
    """
    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()

    repo_data, languages, readme, file_tree = await _fetch_repo_context(github, owner, repo)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")

    tree_summary = _file_tree_summary(file_tree, max_files=200)

    system = """You are a code architecture expert. Cluster the given file tree into logical subsystems.
Return a JSON array of subsystems:
[
  {
    "name": "SubsystemName",
    "description": "What this subsystem handles (1-2 sentences)",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "files": ["path/to/file1.ts", "path/to/file2.ts"],
    "complexity": "low|medium|high",
    "color": "#hex_color",
    "entry_point": "main file to start reading",
    "depends_on": ["OtherSubsystem"]
  }
]
Group by domain (Auth, Database, API, UI, Utils, etc). Return 4-10 subsystems. JSON only."""

    user_prompt = f"""Repository: {owner}/{repo}
Languages: {', '.join(languages.keys())}
Description: {repo_data.get('description', '')}

File tree:
{tree_summary[:5000]}

README excerpt:
{(readme or '')[:1500]}"""

    try:
        # Note: complete_json returns dict, but this prompt returns an array, so we must wrap it or parse raw
        raw = await llm.complete(system, user_prompt)
        clean = re.sub(r'```json\s*|\s*```', '', raw).strip()
        match = re.search(r'\[.*\]', clean, re.DOTALL)
        if match:
            return {"subsystems": json.loads(match.group()), "total": None}
    except Exception as e:
        log.warning("Subsystems LLM failed", error=str(e))

    return {"subsystems": [], "total": 0}


# ─── 3. Repository Walkthrough ────────────────────────────────────────────────

@router.get("/{owner}/{repo}/walkthrough")
async def get_walkthrough(
    owner: str,
    repo: str,
    current_user=Depends(get_current_user),
):
    """
    'Teach me this repo' — a Google-Maps-style guided tour through the codebase.
    Returns ordered stops covering key components in logical learning order.
    """
    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()

    repo_data, languages, readme, file_tree = await _fetch_repo_context(github, owner, repo)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")

    user_level = current_user.expertise_level or "intermediate"
    user_langs = current_user.top_languages or []
    tree_summary = _file_tree_summary(file_tree, max_files=100)

    system = """You are an expert code educator. Create a highly detailed, step-by-step guided walkthrough of this repository.
Think of it as 'Google Maps for code': ordered stops that cover the codebase in the most logical learning sequence.
CRITICAL: You MUST write massive, extremely detailed descriptions for every single stop. Assume the reader is a complete beginner. Hold their hand and explain the technical concepts deeply. Do NOT write 1-sentence summaries.

Return JSON:
{
  "title": "Understanding {repo_name}",
  "estimated_hours": 4,
  "stops": [
    {
      "stop": 1,
      "type": "concept|file|diagram|issue",
      "title": "Stop title",
      "description": "MASSIVE, extremely detailed explanation (at least 150 words) of exactly what the learner will study here, how it works, and why it's important.",
      "resource": "MUST be a valid URL (e.g. official docs, Wikipedia, or a raw github file link)",
      "key_takeaway": "A thorough, 2-3 sentence explanation of the most important lesson from this stop",
      "time_minutes": 15
    }
  ]
}
Include 6-10 stops ordered from high-level (README, architecture) to specific (key files, example issue).
Return JSON only."""

    user_prompt = f"""Repository: {owner}/{repo}
Description: {repo_data.get('description', '')}
Languages: {', '.join(languages.keys())}
Developer level: {user_level}
Developer knows: {', '.join(user_langs[:5]) if user_langs else 'general programming'}

File tree:
{tree_summary[:4000]}

README:
{(readme or '')[:2000]}"""

    try:
        result = await llm.complete_json(system, user_prompt)
        result["repo"] = f"{owner}/{repo}"
        result["repo_url"] = repo_data.get("html_url", "")
        return result
    except Exception as e:
        log.warning("Walkthrough LLM failed", error=str(e))

    raise HTTPException(status_code=500, detail="Could not generate walkthrough")


# ─── 4. Personalized Learning Path ───────────────────────────────────────────

@router.get("/{owner}/{repo}/learning-path")
async def get_learning_path(
    owner: str,
    repo: str,
    current_user=Depends(get_current_user),
):
    """
    Generate a personalized day-by-day learning roadmap.
    Based on the user's skill profile + repo structure.
    """
    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()

    repo_data, languages, readme, file_tree = await _fetch_repo_context(github, owner, repo)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")

    user_level = current_user.expertise_level or "beginner"
    user_langs = current_user.top_languages or []
    skill_vector = current_user.skill_vector or {}
    tree_summary = _file_tree_summary(file_tree, max_files=80)

    # Identify skill gaps
    repo_lang_set = set(languages.keys())
    user_lang_set = set(user_langs)
    gaps = list(repo_lang_set - user_lang_set)

    system = """You are a personalized code education expert. Create a realistic day-by-day learning plan.
CRITICAL: You MUST hold the user's hand. Write extremely detailed task descriptions. Assume they are a complete beginner.

Return JSON:
{
  "title": "7-Day Guide to Contributing to {repo}",
  "total_days": 7,
  "skill_gaps": ["gap1", "gap2"],
  "prep_hours": 2,
  "days": [
    {
      "day": 1,
      "theme": "Theme title",
      "goal": "Detailed explanation of what you'll be able to do after today",
      "tasks": [
        {"task": "Extremely detailed, multi-sentence task description explaining exactly what they need to do, step-by-step, and why", "resource": "MUST be a valid URL (official docs, tutorial, etc.)", "time_minutes": 30}
      ],
      "milestone": "What to have completed by end of day"
    }
  ],
  "first_contribution": "Recommended first issue type or area"
}
Tailor difficulty to the developer's level. JSON only."""

    user_prompt = f"""Repository: {owner}/{repo}
Languages used: {', '.join(languages.keys())}
Description: {repo_data.get('description', '')}

Developer profile:
- Level: {user_level}
- Known languages: {', '.join(user_langs[:8]) if user_langs else 'General programming'}
- Skill gaps for this repo: {', '.join(gaps[:5]) if gaps else 'None identified'}

File structure:
{tree_summary[:3000]}

README excerpt:
{(readme or '')[:2000]}"""

    try:
        result = await llm.complete_json(system, user_prompt)
        result["repo"] = f"{owner}/{repo}"
        result["skill_gaps"] = result.get("skill_gaps", gaps[:5])
        return result
    except Exception as e:
        log.warning("Learning path LLM failed", error=str(e))

    raise HTTPException(status_code=500, detail="Could not generate learning path")


# ─── 5. File / Function Explainer ─────────────────────────────────────────────

@router.get("/{owner}/{repo}/file-explain")
async def explain_file(
    owner: str,
    repo: str,
    path: str = Query(..., description="File path within the repo"),
    current_user=Depends(get_current_user),
):
    """
    AI-generated explanation of any file: purpose, functions list,
    interactions with other files, design patterns used.
    """
    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()

    content = await github.get_file_content(owner, repo, path)
    if not content:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    user_level = current_user.expertise_level or "intermediate"

    system = """You are an expert code educator. Explain this source file in extreme detail.
Return JSON:
{
  "purpose": "Detailed, 3-4 sentence description of the exact purpose of this file",
  "summary": "Comprehensive, multi-paragraph explanation of exactly how this file works, its logic, configurations, and core mechanics",
  "functions": [
    {
      "name": "functionName",
      "signature": "def function(args) -> ReturnType",
      "purpose": "What it does in plain English",
      "complexity": "simple|moderate|complex",
      "called_by": ["otherFunction"],
      "calls": ["dependencyFunction"]
    }
  ],
  "classes": [
    {"name": "ClassName", "purpose": "What it represents", "methods": ["method1", "method2"]}
  ],
  "imports": ["dependency1", "dependency2"],
  "design_patterns": ["pattern1"],
  "interactions": ["file1.ts", "file2.ts"],
  "beginner_explanation": "Provide a thorough, easy-to-understand breakdown for a junior developer (3-4 paragraphs)",
  "key_lines": [{"line": 42, "explanation": "Why this line matters"}]
}
JSON only, no markdown."""

    user_prompt = f"""File: {owner}/{repo}/{path}
Developer level: {user_level}

File content:
{content[:6000]}"""

    try:
        result = await llm.complete_json(system, user_prompt)
        result["file_path"] = path
        result["repo"] = f"{owner}/{repo}"
        result["github_url"] = f"https://github.com/{owner}/{repo}/blob/main/{path}"
        return result
    except Exception as e:
        log.warning("File explain LLM failed", error=str(e))

    raise HTTPException(status_code=500, detail="Could not explain file")


# ─── 6. Affected File Predictor ───────────────────────────────────────────────

@router.post("/{owner}/{repo}/predict-files")
async def predict_affected_files(
    owner: str,
    repo: str,
    payload: dict,
    current_user=Depends(get_current_user),
):
    """
    Given an issue description, predict which files are most likely to be modified.
    Returns files with confidence scores.
    """
    issue_title = payload.get("title", "")
    issue_body = payload.get("body", "")
    issue_labels = payload.get("labels", [])

    if not issue_title and not issue_body:
        raise HTTPException(status_code=400, detail="issue title or body is required")

    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()

    _, languages, readme, file_tree = await _fetch_repo_context(github, owner, repo)
    tree_summary = _file_tree_summary(file_tree, max_files=200)

    system = """You are an expert software engineer. Given an issue description and a repository file tree,
predict which files are most likely to need modification to resolve this issue.
Return JSON:
{
  "predictions": [
    {
      "file": "path/to/file.ts",
      "confidence": 0.88,
      "reason": "Why this file needs to change"
    }
  ],
  "affected_subsystems": ["Auth", "Database"],
  "change_scope": "small|medium|large",
  "explanation": "Brief explanation of what changes are needed overall"
}
Return 3-8 most likely files, sorted by confidence (highest first). JSON only."""

    user_prompt = f"""Repository: {owner}/{repo}
Issue title: {issue_title}
Issue body: {issue_body[:2000]}
Labels: {', '.join(issue_labels)}

File tree:
{tree_summary[:5000]}

README excerpt:
{(readme or '')[:1000]}"""

    try:
        result = await llm.complete_json(system, user_prompt)
        result["repo"] = f"{owner}/{repo}"
        return result
    except Exception as e:
        log.warning("File predictor LLM failed", error=str(e))

    raise HTTPException(status_code=500, detail="Could not predict affected files")


# ─── 7. Contribution Readiness Score ─────────────────────────────────────────

@router.get("/{owner}/{repo}/readiness")
async def get_contribution_readiness(
    owner: str,
    repo: str,
    issue_number: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
):
    """
    Calculate how ready the user is to contribute to this repo (or specific issue).
    Returns score 0-100, skill gaps, estimated prep time.
    """
    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()

    repo_data, languages, readme, _ = await _fetch_repo_context(github, owner, repo)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")

    issue_context = ""
    if issue_number:
        try:
            issue = await github.get_issue(owner, repo, issue_number)
            issue_context = f"""
Specific issue #{issue_number}: {issue.get('title', '')}
{(issue.get('body') or '')[:1000]}
Labels: {', '.join(l['name'] for l in issue.get('labels', []))}"""
        except Exception:
            pass

    user_skills = current_user.top_languages or []
    user_level = current_user.expertise_level or "beginner"
    skill_vector = current_user.skill_vector or {}

    repo_langs = list(languages.keys())
    user_lang_set = set(s.lower() for s in user_skills)
    matching = [l for l in repo_langs if l.lower() in user_lang_set]
    missing = [l for l in repo_langs if l.lower() not in user_lang_set]

    system = """You are a developer readiness assessor. Evaluate how ready this developer is to contribute.
Return JSON:
{
  "readiness_score": 72,
  "verdict": "Almost ready",
  "strengths": ["Skill or knowledge that helps"],
  "gaps": [
    {"skill": "Redux", "importance": "high|medium|low", "learn_hours": 4, "resource": "redux.js.org"}
  ],
  "recommended_issues": ["good-first-issue", "documentation"],
  "estimated_prep_hours": 6,
  "personalized_message": "Encouraging, specific message to this developer",
  "first_step": "Concrete first action to take right now"
}
JSON only."""

    user_prompt = f"""Repository: {owner}/{repo}
Languages: {', '.join(repo_langs)}
Description: {repo_data.get('description', '')}
Difficulty topics: {', '.join(repo_data.get('topics', [])[:10])}

Developer profile:
- Skill level: {user_level}
- Known languages: {', '.join(user_skills[:10]) if user_skills else 'None listed'}
- Languages matching repo: {', '.join(matching) if matching else 'None'}
- Language gaps: {', '.join(missing[:5]) if missing else 'None'}
{issue_context}"""

    try:
        result = await llm.complete_json(system, user_prompt)
        result["repo"] = f"{owner}/{repo}"
        result["matching_languages"] = matching
        result["missing_languages"] = missing[:5]
        if issue_number:
            result["issue_number"] = issue_number
        return result
    except Exception as e:
        log.warning("Readiness LLM failed", error=str(e))

    # Basic fallback
    base_score = min(100, len(matching) * 25 + (30 if user_level == "intermediate" else 50 if user_level == "advanced" else 10))
    return {
        "readiness_score": base_score,
        "verdict": "Needs preparation" if base_score < 50 else "Ready",
        "strengths": matching,
        "gaps": [{"skill": l, "importance": "high", "learn_hours": 8} for l in missing[:3]],
        "matching_languages": matching,
        "missing_languages": missing[:5],
        "repo": f"{owner}/{repo}",
    }


# ─── 8. PR Reviewer ───────────────────────────────────────────────────────────

@router.post("/{owner}/{repo}/pr-review")
async def review_pull_request(
    owner: str,
    repo: str,
    payload: dict,
    current_user=Depends(get_current_user),
):
    """
    AI-powered PR review: bugs, security issues, performance, style, architecture.
    Accepts a PR number OR a raw diff string.
    """
    pr_number = payload.get("pr_number")
    diff = payload.get("diff", "")
    pr_title = payload.get("title", "")

    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()

    # Fetch diff from GitHub if pr_number given
    if pr_number and not diff:
        try:
            pr_data = await github._get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
            pr_title = pr_data.get("title", "")
            diff_resp = await github._get(
                f"/repos/{owner}/{repo}/pulls/{pr_number}/files"
            )
            if isinstance(diff_resp, list):
                diff = "\n\n".join(
                    f"File: {f.get('filename')}\n{f.get('patch', '')}"
                    for f in diff_resp[:15]
                )
        except Exception as e:
            log.warning("PR fetch failed", error=str(e))

    if not diff:
        raise HTTPException(status_code=400, detail="pr_number or diff is required")

    system = """You are a meticulous senior code reviewer. Review this pull request diff carefully.
Return JSON:
{
  "overall_verdict": "approve|request_changes|comment",
  "summary": "2-3 sentence overall assessment",
  "score": 85,
  "issues": [
    {
      "severity": "critical|major|minor|suggestion",
      "file": "path/to/file.ts",
      "line": 42,
      "type": "bug|security|performance|style|architecture",
      "description": "What is wrong",
      "fix": "How to fix it",
      "code_example": "Optional better code"
    }
  ],
  "positives": ["Good thing about the PR"],
  "security_flags": ["Security concern if any"],
  "performance_flags": ["Performance concern if any"],
  "suggested_tests": ["Test case to add"]
}
Be specific, cite actual code from the diff. JSON only."""

    user_prompt = f"""Repository: {owner}/{repo}
PR Title: {pr_title}
PR #{pr_number or 'N/A'}

Diff:
{diff[:8000]}"""

    try:
        result = await llm.complete_json(system, user_prompt)
        result["repo"] = f"{owner}/{repo}"
        if pr_number:
            result["pr_number"] = pr_number
            result["pr_url"] = f"https://github.com/{owner}/{repo}/pull/{pr_number}"
        return result
    except Exception as e:
        log.warning("PR review LLM failed", error=str(e))

    raise HTTPException(status_code=500, detail="PR review failed")


# ─── 9. Knowledge Gaps (Personalized Gap Analysis) ───────────────────────────

@router.get("/{owner}/{repo}/knowledge-gaps")
async def get_knowledge_gaps(
    owner: str,
    repo: str,
    current_user=Depends(get_current_user),
):
    """
    What does this specific user need to learn to contribute to this repo?
    Returns a structured learning plan bridging their current skills to the repo's needs.
    """
    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()

    repo_data, languages, readme, _ = await _fetch_repo_context(github, owner, repo)
    if not repo_data:
        raise HTTPException(status_code=404, detail="Repository not found")

    user_skills = current_user.top_languages or []
    user_level = current_user.expertise_level or "beginner"
    skill_vector = current_user.skill_vector or {}

    system = """You are a personalized learning advisor. Identify exactly what this developer needs to learn.
Return JSON:
{
  "strengths": [{"skill": "Python", "confidence": "high", "relevant": true}],
  "gaps": [
    {
      "skill": "Docker",
      "priority": "high|medium|low",
      "context": "Used for deployment in this repo",
      "learn_time_hours": 4,
      "resources": [
        {"title": "Resource title", "url": "MUST be a REAL, VALID URL (e.g. https://react.dev, Wikipedia, etc.). Do not hallucinate dead links.", "type": "tutorial|docs|course"}
      ]
    }
  ],
  "overall_readiness": 65,
  "recommended_path": "Short description of ideal learning order",
  "quick_wins": ["Thing you can contribute to right now without learning anything new"]
}
JSON only."""

    user_prompt = f"""Repository: {owner}/{repo}
Languages: {', '.join(languages.keys())}
Topics: {', '.join(repo_data.get('topics', [])[:10])}
Description: {repo_data.get('description', '')}

README excerpt:
{(readme or '')[:1500]}

Developer:
- Level: {user_level}
- Languages: {', '.join(user_skills[:10]) if user_skills else 'None'}
- Skill vector: {json.dumps({k: v for k, v in list((skill_vector or {}).items())[:10]})}"""

    try:
        result = await llm.complete_json(system, user_prompt)
        result["repo"] = f"{owner}/{repo}"
        return result
    except Exception as e:
        log.warning("Knowledge gaps LLM failed", error=str(e))

    raise HTTPException(status_code=500, detail="Could not analyze knowledge gaps")
