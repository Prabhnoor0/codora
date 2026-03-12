"""Project discovery and analysis router."""
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import structlog

from database import get_db
from routers.deps import get_current_user
from services.github_service import GitHubService
from services.llm_service import get_llm_service

router = APIRouter()
log = structlog.get_logger()

SKILL_TO_TOPICS = {
    "Python": ["python", "django", "flask", "fastapi", "ml", "data-science"],
    "JavaScript": ["javascript", "nodejs", "react", "vue", "nextjs"],
    "TypeScript": ["typescript", "angular", "react", "nextjs"],
    "Go": ["golang", "go", "cli", "kubernetes", "docker"],
    "Rust": ["rust", "systems", "wasm", "cli"],
    "Java": ["java", "spring", "android", "gradle"],
    "C++": ["cpp", "systems", "game-development", "embedded"],
    "Ruby": ["ruby", "rails", "gem"],
    "PHP": ["php", "laravel", "wordpress"],
    "Swift": ["swift", "ios", "macos"],
    "Kotlin": ["kotlin", "android"],
    "Dart": ["dart", "flutter"],
}

BEGINNER_FRIENDLY_ORGS = [
    "facebook", "microsoft", "google", "mozilla", "apache",
    "django", "pallets", "psf", "torvalds", "hashicorp",
    "kubernetes", "docker", "grafana", "elastic", "vercel",
]


def _skill_match_score(repo_languages: dict, repo_topics: list, user_skills: list, user_level: str, skill_vector: dict = None) -> int:
    """Return 0-100 skill match. Weighted by commit-frequency (skill_vector) if available."""
    if not user_skills and not skill_vector:
        return 50
    {k.lower(): v for k, v in repo_languages.items()}
    total_repo_bytes = sum(repo_languages.values()) or 1
    topic_set = {t.lower() for t in repo_topics}

    score = 0.0
    weight_total = 0.0

    # Score per repo language weighted by its share of the codebase
    for lang, lang_bytes in repo_languages.items():
        repo_weight = lang_bytes / total_repo_bytes  # how important is this lang to the repo
        user_score = 0.0

        # Check if user knows this language (skill_vector gives 0-1 proficiency)
        if skill_vector:
            user_score = skill_vector.get(lang, 0.0)
            # partial match via topic
            if user_score == 0:
                related = SKILL_TO_TOPICS.get(lang, [])
                if any(r in topic_set for r in related):
                    user_score = 0.3
        else:
            # fallback: binary match
            if lang in (user_skills or []):
                user_score = 0.8
            else:
                related = SKILL_TO_TOPICS.get(lang, [])
                if any(r in topic_set for r in related):
                    user_score = 0.3

        score += repo_weight * user_score
        weight_total += repo_weight

    final = score / weight_total if weight_total else 0.0
    return min(100, int(final * 100))


def _difficulty_label(stars: int, open_issues: int, languages_count: int, user_level: str) -> str:
    score = 0
    if stars > 50000: score += 2
    elif stars > 5000: score += 1
    
    if open_issues > 1000: score += 2
    elif open_issues > 200: score += 1

    if languages_count > 6: score += 2
    elif languages_count > 3: score += 1

    # Level offset (if user is advanced, things seem easier)
    level_boost = {"beginner": 1, "intermediate": 0, "advanced": -1}.get(user_level, 0)
    score += level_boost

    if score <= 1: return "Easy"
    if score <= 3: return "Medium"
    return "Hard"


@router.get("/projects")
async def discover_projects(
    limit: int = 18,
    page: int = 1,
    difficulty: Optional[str] = None,
    language: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Discover open source projects matched to user skills."""
    github = GitHubService(current_user.github_access_token)
    user_skills = list(current_user.top_languages or [])
    user_level = current_user.expertise_level or "beginner"
    skill_vector = current_user.skill_vector or {}

    # Option B: repos that explicitly have good-first-issues in user's languages
    search_langs = [language] if language else (user_skills[:2] if user_skills else ["Python"])
    lang_query = " ".join(f"language:{lbl}" for lbl in search_langs[:2])
    
    from datetime import datetime, timedelta
    recent_date = (datetime.utcnow() - timedelta(days=60)).strftime("%Y-%m-%d")
    query = f"{lang_query} good-first-issues:>1 stars:>50 pushed:>{recent_date} is:public"

    try:
        results = await github._get("/search/repositories", {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": limit,
            "page": page,
        })
        repos = results.get("items", [])
    except Exception as e:
        log.warning("GitHub search failed", error=str(e))
        repos = []

    projects = []
    for repo in repos:
        try:
            lang_data = await github.get_repo_languages(repo["owner"]["login"], repo["name"])
        except Exception:
            lang_data = {repo.get("language", "Unknown"): 1} if repo.get("language") else {}

        topics = repo.get("topics", [])
        match_pct = _skill_match_score(lang_data, topics, user_skills, user_level, skill_vector)
        diff = _difficulty_label(
            repo.get("stargazers_count", 0),
            repo.get("open_issues_count", 0),
            len(lang_data),
            user_level,
        )

        if difficulty and diff.lower() != difficulty.lower():
            continue

        projects.append({
            "owner": repo["owner"]["login"],
            "name": repo["name"],
            "full_name": repo["full_name"],
            "description": repo.get("description") or "No description provided.",
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "open_issues": repo.get("open_issues_count", 0),
            "language": repo.get("language"),
            "languages": list(lang_data.keys())[:5],
            "topics": topics[:6],
            "skill_match": match_pct,
            "difficulty": diff,
            "avatar_url": repo["owner"].get("avatar_url"),
            "html_url": repo.get("html_url"),
            "good_first_issues_url": f"https://github.com/{repo['full_name']}/contribute",
        })

    projects.sort(key=lambda x: (-x["skill_match"], -x["stars"]))
    return {
        "projects": projects, 
        "user_skills": user_skills,
        "page": page,
        "has_more": len(repos) == limit
    }


@router.get("/projects/{owner}/{repo}")
async def get_project_detail(
    owner: str,
    repo: str,
    current_user=Depends(get_current_user),
):
    """Get full project analysis with architecture diagram and skill match."""
    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()
    user_skills = list(current_user.top_languages or [])
    user_level = current_user.expertise_level or "beginner"
    skill_vector = current_user.skill_vector or {}

    repo_data, lang_data, readme = await asyncio.gather(
        github.get_repo(owner, repo),
        github.get_repo_languages(owner, repo),
        github.get_readme(owner, repo),
        return_exceptions=True,
    )
    if isinstance(repo_data, Exception):
        raise HTTPException(status_code=404, detail="Repository not found")

    if isinstance(lang_data, Exception): lang_data = {}
    if isinstance(readme, Exception): readme = None

    topics = repo_data.get("topics", [])
    match_pct = _skill_match_score(lang_data, topics, user_skills, user_level, skill_vector)
    diff = _difficulty_label(
        repo_data.get("stargazers_count", 0),
        repo_data.get("open_issues_count", 0),
        len(lang_data),
        user_level,
    )

    import re

    ctx = f"""Repository: {owner}/{repo}
Languages: {', '.join(list(lang_data.keys())[:8])}
Topics: {', '.join(topics[:10])}
Stars: {repo_data.get('stargazers_count', 0)}

README (truncated):
{(readme or '')[:2500]}"""

    # Call 1: JSON metadata (summary, tech, getting_started)
    try:
        parsed = await llm.complete_json(
            "You are a senior open source engineer. Return ONLY valid JSON.",
            f"""{ctx}

Return a JSON object with:
{{
  "summary": "Extremely detailed, multi-paragraph plain-English description of what this project does, why it exists, and its core concepts. Assume the reader is a complete beginner. Hold their hand and explain it fully.",
  "tech_breakdown": [{{"name": "Tech Name", "role": "Highly detailed explanation of what this tech does in the project and why it's used"}}],
  "getting_started": ["step 1", "step 2", "step 3", "step 4"]
}}"""
        )
        ai_summary = parsed.get("summary", repo_data.get("description", ""))
        tech_breakdown = parsed.get("tech_breakdown", [])
        getting_started = parsed.get("getting_started", [])
    except Exception as e:
        log.warning("LLM metadata failed", error=str(e))
        ai_summary = repo_data.get("description", "")
        tech_breakdown = [{"name": l, "role": "Primary Language"} for lbl in list(lang_data.keys())[:4]]
        getting_started = ["Fork and clone the repository", "Read the README and CONTRIBUTING guide", "Run the dev environment locally", "Browse open issues labelled 'good first issue'"]

    # Call 2: Mermaid diagram as plain text (NOT embedded in JSON to avoid escaping issues)
    try:
        diagram_resp = await llm.complete(
            "You output ONLY Mermaid diagram code. No explanation, no markdown fences, no backticks.",
            f"""{ctx}

Generate a Mermaid graph LR diagram showing the real architecture of this project.
- Use 6-10 nodes based on the actual components (e.g. Frontend, Auth, API, DB, Cache, CLI, Tests)
- Use --> for connections with short labels where helpful
- Node names must be simple identifiers: no quotes, no brackets with special chars
- Output ONLY the raw Mermaid code starting with 'graph LR'""",
        )
        # Strip any accidental fences
        mermaid_diagram = re.sub(r'```[a-z]*\n?|\n?```', '', diagram_resp).strip()
        if not mermaid_diagram.startswith("graph"):
            raise ValueError("Bad diagram")
    except Exception as e:
        log.warning("LLM diagram failed", error=str(e))
        langs = list(lang_data.keys())[:4]
        mermaid_diagram = "graph LR\n" + "\n".join(
            [f"  {chr(65+i)}[\"{lbl}\"]" for i, lbl in enumerate(langs)] +
            [f"  A --> {chr(65+i)}" for i in range(1, len(langs))]
        ) if langs else "graph LR\n  A[\"Project\"] --> B[\"Codebase\"]"


    # Get recent issues and filter
    try:
        issues_raw = await github.get_issues(owner, repo, state="open", per_page=30)
        # Filter out PRs
        issues_only = [i for i in issues_raw if not i.get("pull_request")]
        
        # Try to find beginner friendly ones
        beginner_issues = [
            i for i in issues_only
            if any(lbl["name"].lower() in ["good first issue", "beginner", "easy", "help wanted", "starter"] for lbl in i.get("labels", []))
        ]
        
        # We will return the first 15 issues, marking beginner friendly ones
        recent_issues = issues_only[:15]
        
        formatted_issues = []
        for i in recent_issues:
            is_easy = i in beginner_issues
            formatted_issues.append({
                "number": i["number"],
                "title": i["title"],
                "body": (i.get("body") or "")[:150] + "...",
                "labels": [lbl["name"] for lbl in i.get("labels", [])][:3],
                "comments": i.get("comments", 0),
                "difficulty": "Easy" if is_easy else "Medium",
                "html_url": i.get("html_url")
            })
    except Exception as e:
        log.warning("Issues fetch failed", error=str(e))
        formatted_issues = []

    # Skill breakdown for the user
    user_skill_match_detail = []
    for lang, bytes_count in list(lang_data.items())[:8]:
        total = sum(lang_data.values()) or 1
        pct = round(bytes_count / total * 100, 1)
        user_has = lang in (user_skills or [])
        user_skill_match_detail.append({"lang": lang, "repo_pct": pct, "user_has": user_has})

    return {
        "owner": owner,
        "name": repo,
        "full_name": f"{owner}/{repo}",
        "description": repo_data.get("description") or "",
        "ai_summary": ai_summary,
        "stars": repo_data.get("stargazers_count", 0),
        "forks": repo_data.get("forks_count", 0),
        "open_issues": repo_data.get("open_issues_count", 0),
        "watchers": repo_data.get("watchers_count", 0),
        "language": repo_data.get("language"),
        "languages": lang_data,
        "topics": topics,
        "skill_match": match_pct,
        "difficulty": diff,
        "mermaid_diagram": mermaid_diagram,
        "recent_issues": formatted_issues,
        "tech_breakdown": tech_breakdown,
        "getting_started": getting_started,
        "good_first_issues": [],
        "skill_match_detail": user_skill_match_detail,
        "html_url": repo_data.get("html_url"),
        "avatar_url": f"https://github.com/{owner}.png",
        "license": repo_data.get("license", {}).get("name") if repo_data.get("license") else None,
        "created_at": repo_data.get("created_at"),
        "updated_at": repo_data.get("updated_at"),
    }


@router.get("/projects/{owner}/{repo}/issues/{number}")
async def get_issue_detail(
    owner: str,
    repo: str,
    number: int,
    current_user=Depends(get_current_user),
):
    """Get full issue analysis with related files and step-by-step guide."""
    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()

    issue, comments = await asyncio.gather(
        github.get_issue(owner, repo, number),
        github.get_issue_comments(owner, repo, number),
        return_exceptions=True,
    )
    if isinstance(issue, Exception):
        raise HTTPException(status_code=404, detail="Issue not found")
    if isinstance(comments, Exception):
        comments = []

    f"""Issue #{number}: {issue.get('title', '')}

{issue.get('body', 'No description.')}"""

    # Get AI analysis
    guide_steps = []
    related_concepts = []
    related_files = []

    try:
        prompt = f"""You are a senior open source contributor mentoring a new developer.

Repository: {owner}/{repo}
Issue #{number}: {issue.get('title', '')}

Issue body:
{(issue.get('body') or 'No description.')[:2000]}

User skills: {', '.join(current_user.top_languages or [])}
User level: {current_user.expertise_level or 'beginner'}

Provide a JSON response with:
1. "concepts_needed": array of 3-5 concepts/technologies the developer needs to understand first (strings)
2. "guide_steps": array of 5-7 step objects, each with "step" (number), "title" (string), "description" (string), "tip" (optional string)
3. "related_files": array of likely file paths that need to be modified (educated guesses, 3-5 items)
4. "estimated_time": string like "2-4 hours" or "1-2 days"
5. "difficulty": "Easy", "Medium", or "Hard"

Return only the JSON."""

        response = await llm.complete(
            "You are a senior open source contributor mentoring junior developers. Return only valid JSON.",
            prompt,
        )
        import json
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            guide_steps = parsed.get("guide_steps", [])
            related_concepts = parsed.get("concepts_needed", [])
            related_files = parsed.get("related_files", [])
            estimated_time = parsed.get("estimated_time", "Unknown")
            difficulty = parsed.get("difficulty", "Medium")
        else:
            estimated_time = "Unknown"
            difficulty = "Medium"
    except Exception as e:
        log.warning("Issue LLM analysis failed", error=str(e))
        estimated_time = "Unknown"
        difficulty = "Medium"

    return {
        "number": number,
        "title": issue.get("title"),
        "body": issue.get("body") or "",
        "state": issue.get("state"),
        "labels": [lbl["name"] for lbl in issue.get("labels", [])],
        "comments_count": issue.get("comments", 0),
        "created_at": issue.get("created_at"),
        "html_url": issue.get("html_url"),
        "author": issue.get("user", {}).get("login"),
        "recent_comments": [
            {"author": c["user"]["login"], "body": c["body"][:500], "created_at": c["created_at"]}
            for c in (comments[:3] if isinstance(comments, list) else [])
        ],
        "guide_steps": guide_steps,
        "concepts_needed": related_concepts,
        "related_files": related_files,
        "estimated_time": estimated_time,
        "difficulty": difficulty,
        "repo_owner": owner,
        "repo_name": repo,
    }


@router.post("/projects/{owner}/{repo}/issues/{number}/review-code")
async def review_code_submission(
    owner: str,
    repo: str,
    number: int,
    payload: dict,
    current_user=Depends(get_current_user),
):
    """
    AI reviews user's code fix for an issue.
    Returns: score (0-100), feedback, errors, suggestions, can_submit_pr (True if >=85).
    """
    user_code = payload.get("code", "").strip()
    file_path = payload.get("file_path", "")
    if not user_code:
        raise HTTPException(status_code=400, detail="code is required")

    github = GitHubService(current_user.github_access_token)
    llm = get_llm_service()
    try:
        issue = await github.get_issue(owner, repo, number)
    except Exception:
        raise HTTPException(status_code=404, detail="Issue not found")

    try:
        prompt = f"""You are a senior code reviewer evaluating a fix for GitHub issue #{number}.

Repository: {owner}/{repo}
Issue: {issue.get('title', '')}
Issue body: {(issue.get('body') or '')[:1500]}
File: {file_path or 'unknown'}

User's code:
```
{user_code[:4000]}
```

Respond with JSON only:
{{
  "score": <0-100 integer>,
  "summary": "<1-2 sentence verdict>",
  "what_works": ["<correct things>"],
  "errors": [{{"line": <int or null>, "issue": "<problem>", "fix": "<suggestion>"}}],
  "missing": ["<still missing to fully resolve>"],
  "suggestions": ["<improvement>"],
  "can_submit_pr": <true if score >= 85 else false>
}}"""
        import json
        import re
        response = await llm.complete(
            "You are a strict senior code reviewer. Return valid JSON only.",
            prompt,
        )
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            score = max(0, min(100, int(result.get("score", 0))))
            result["score"] = score
            result["can_submit_pr"] = score >= 85
            return result
    except Exception as e:
        log.warning("Code review failed", error=str(e))
    return {"score": 0, "summary": "Review failed.", "what_works": [], "errors": [], "missing": [], "suggestions": [], "can_submit_pr": False}


@router.post("/projects/{owner}/{repo}/issues/{number}/submit-pr")
async def submit_pull_request(
    owner: str,
    repo: str,
    number: int,
    payload: dict,
    current_user=Depends(get_current_user),
):
    """Create a GitHub PR with user's code. Requires review score >= 85."""
    user_code = payload.get("code", "").strip()
    file_path = payload.get("file_path", "").strip()
    review_score = int(payload.get("review_score", 0))
    commit_message = payload.get("commit_message", f"fix: resolve issue #{number}")
    pr_title = payload.get("pr_title", f"Fix: #{number}")
    pr_body = payload.get("pr_body", f"Resolves #{number}\n\nCreated with Codora assistance.")

    if review_score < 85:
        raise HTTPException(status_code=403, detail="Score must be >= 85 to submit PR")
    if not user_code or not file_path:
        raise HTTPException(status_code=400, detail="code and file_path are required")

    import base64
    import httpx
    token = current_user.github_access_token
    if not token:
        raise HTTPException(status_code=401, detail="No GitHub token")

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    base_api = "https://api.github.com"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            repo_info = (await client.get(f"{base_api}/repos/{owner}/{repo}", headers=headers)).json()
            default_branch = repo_info.get("default_branch", "main")
            ref = (await client.get(f"{base_api}/repos/{owner}/{repo}/git/ref/heads/{default_branch}", headers=headers)).json()
            base_sha = ref["object"]["sha"]
            branch_name = f"mentai/fix-{number}-{current_user.github_login}"
            await client.post(f"{base_api}/repos/{owner}/{repo}/git/refs", headers=headers, json={"ref": f"refs/heads/{branch_name}", "sha": base_sha})
            file_resp = await client.get(f"{base_api}/repos/{owner}/{repo}/contents/{file_path}", headers=headers)
            file_sha = file_resp.json().get("sha") if file_resp.status_code == 200 else None
            put_payload: dict = {"message": commit_message, "content": base64.b64encode(user_code.encode()).decode(), "branch": branch_name}
            if file_sha:
                put_payload["sha"] = file_sha
            (await client.put(f"{base_api}/repos/{owner}/{repo}/contents/{file_path}", headers=headers, json=put_payload)).raise_for_status()
            pr = (await client.post(f"{base_api}/repos/{owner}/{repo}/pulls", headers=headers, json={"title": pr_title, "body": pr_body, "head": branch_name, "base": default_branch})).json()
        return {"success": True, "pr_url": pr.get("html_url"), "pr_number": pr.get("number"), "branch": branch_name}
    except Exception as e:
        log.error("PR submission failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
