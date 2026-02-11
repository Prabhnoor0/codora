"""
GitHub API client — async, rate-limit aware, cached.
"""
import httpx
import json
from typing import Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

from config import settings
from redis_client import cache_get, cache_set

log = structlog.get_logger()

GITHUB_API = "https://api.github.com"


class GitHubService:
    def __init__(self, access_token: Optional[str] = None):
        token = access_token or settings.GITHUB_PAT
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _get(self, path: str, params: dict = None) -> Any:
        cache_key = f"gh:{path}:{json.dumps(params or {}, sort_keys=True)}"
        cached = await cache_get(cache_key)
        if cached:
            return json.loads(cached)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{GITHUB_API}{path}", headers=self.headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            await cache_set(cache_key, json.dumps(data), ttl=300)
            return data

    # ── User ──────────────────────────────────────────────────
    async def get_user(self, username: str) -> dict:
        return await self._get(f"/users/{username}")

    async def get_current_user(self) -> dict:
        return await self._get("/user")

    async def get_user_repos(self, username: str, per_page: int = 100) -> list[dict]:
        return await self._get(f"/users/{username}/repos", {"per_page": per_page, "sort": "updated"})

    async def get_user_events(self, username: str, per_page: int = 100) -> list[dict]:
        return await self._get(f"/users/{username}/events/public", {"per_page": per_page})

    async def get_user_starred(self, username: str, per_page: int = 30) -> list[dict]:
        return await self._get(f"/users/{username}/starred", {"per_page": per_page})

    # ── Repository ────────────────────────────────────────────
    async def get_repo(self, owner: str, repo: str) -> dict:
        return await self._get(f"/repos/{owner}/{repo}")

    async def get_repo_languages(self, owner: str, repo: str) -> dict:
        return await self._get(f"/repos/{owner}/{repo}/languages")

    async def get_repo_topics(self, owner: str, repo: str) -> dict:
        return await self._get(f"/repos/{owner}/{repo}/topics")

    async def get_repo_tree(self, owner: str, repo: str, branch: str = "HEAD") -> dict:
        return await self._get(f"/repos/{owner}/{repo}/git/trees/{branch}", {"recursive": "true"})

    async def get_file_tree(self, owner: str, repo: str) -> list:
        """Return flat file list [{path, type, size}] ready for LLM context."""
        try:
            data = await self.get_repo_tree(owner, repo)
            if isinstance(data, dict) and "tree" in data:
                return [
                    {"path": item["path"], "type": item.get("type", "blob"), "size": item.get("size", 0)}
                    for item in data["tree"]
                    if item.get("type") != "tree"
                ]
        except Exception as e:
            log.warning("get_file_tree failed", error=str(e))
        return []

    async def get_file_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        try:
            data = await self._get(f"/repos/{owner}/{repo}/contents/{path}")
            import base64
            if isinstance(data, dict) and data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        except Exception as e:
            log.warning("Failed to fetch file", path=path, error=str(e))
        return None

    async def get_readme(self, owner: str, repo: str) -> Optional[str]:
        return await self.get_file_content(owner, repo, "README.md") or \
               await self.get_file_content(owner, repo, "readme.md")

    async def get_package_json(self, owner: str, repo: str) -> Optional[dict]:
        content = await self.get_file_content(owner, repo, "package.json")
        if content:
            try:
                return json.loads(content)
            except Exception:
                pass
        return None

    async def get_commits(self, owner: str, repo: str, per_page: int = 30) -> list[dict]:
        return await self._get(f"/repos/{owner}/{repo}/commits", {"per_page": per_page})

    # ── Issues ────────────────────────────────────────────────
    async def get_issues(self, owner: str, repo: str, state: str = "open", per_page: int = 50) -> list[dict]:
        return await self._get(
            f"/repos/{owner}/{repo}/issues",
            {"state": state, "per_page": per_page, "sort": "updated"}
        )

    async def get_issue(self, owner: str, repo: str, number: int) -> dict:
        return await self._get(f"/repos/{owner}/{repo}/issues/{number}")

    async def get_issue_comments(self, owner: str, repo: str, number: int) -> list[dict]:
        return await self._get(f"/repos/{owner}/{repo}/issues/{number}/comments")

    # ── Pull Requests ─────────────────────────────────────────
    async def get_pr(self, owner: str, repo: str, number: int) -> dict:
        return await self._get(f"/repos/{owner}/{repo}/pulls/{number}")

    async def get_pr_files(self, owner: str, repo: str, number: int) -> list[dict]:
        return await self._get(f"/repos/{owner}/{repo}/pulls/{number}/files")

    async def get_pr_diff(self, owner: str, repo: str, number: int) -> str:
        """Fetch unified diff for a PR."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
            resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{number}", headers=headers)
            resp.raise_for_status()
            return resp.text

    # ── User contribution analysis ────────────────────────────
    async def build_developer_profile(self, username: str) -> dict:
        """Aggregate all GitHub data into a developer profile."""
        user, repos, events = await self._gather_profile_data(username)

        # Language aggregation
        lang_bytes: dict[str, int] = {}
        for repo in repos[:20]:
            if repo.get("language"):
                lang_bytes[repo["language"]] = lang_bytes.get(repo["language"], 0) + (repo.get("size", 0))

        total_bytes = sum(lang_bytes.values()) or 1
        language_breakdown = {k: round(v / total_bytes * 100, 1) for k, v in
                               sorted(lang_bytes.items(), key=lambda x: -x[1])[:10]}

        # Topic aggregation
        all_topics = []
        for repo in repos:
            all_topics.extend(repo.get("topics", []))
        from collections import Counter
        topic_counts = Counter(all_topics)

        # Commit/PR counts from events
        commits = sum(1 for e in events if e.get("type") == "PushEvent")
        prs = sum(1 for e in events if e.get("type") == "PullRequestEvent")

        top_languages = list(language_breakdown.keys())[:5]

        return {
            "username": username,
            "top_languages": top_languages,
            "language_breakdown": language_breakdown,
            "top_topics": [t for t, _ in topic_counts.most_common(15)],
            "total_repos": len(repos),
            "total_stars": sum(r.get("stargazers_count", 0) for r in repos),
            "recent_commits": commits,
            "recent_prs": prs,
            "repos": [
                {"name": r["name"], "language": r.get("language"), "stars": r.get("stargazers_count", 0)}
                for r in repos[:20]
            ],
        }

    async def _gather_profile_data(self, username: str):
        import asyncio
        user, repos, events = await asyncio.gather(
            self.get_user(username),
            self.get_user_repos(username),
            self.get_user_events(username),
        )
        return user, repos, events
