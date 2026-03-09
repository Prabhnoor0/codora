"""
Neo4j Knowledge Graph service.
Manages repository graph, developer graph, and complex queries.
"""
from typing import Optional
import structlog

from neo4j_client import get_driver

log = structlog.get_logger()


class GraphService:

    # ── Repository Graph ──────────────────────────────────────
    async def upsert_repository(self, repo_id: str, full_name: str, metadata: dict):
        async with get_driver().session() as session:
            await session.run("""
                MERGE (r:Repository {full_name: $full_name})
                SET r.repo_id = $repo_id,
                    r.description = $description,
                    r.stars = $stars,
                    r.language = $language,
                    r.updated_at = datetime()
            """, full_name=full_name, repo_id=repo_id, **metadata)

    async def upsert_file(self, repo_id: str, full_name: str, file_path: str, file_type: str, size: int = 0):
        async with get_driver().session() as session:
            await session.run("""
                MERGE (f:File {repo_id: $repo_id, path: $file_path})
                SET f.type = $file_type, f.size = $size
                WITH f
                MATCH (r:Repository {full_name: $full_name})
                MERGE (r)-[:HAS_FILE]->(f)
            """, repo_id=repo_id, full_name=full_name, file_path=file_path,
                              file_type=file_type, size=size)

    async def upsert_function(self, repo_id: str, file_path: str, fn_name: str, line_start: int, line_end: int):
        async with get_driver().session() as session:
            await session.run("""
                MERGE (fn:Function {repo_id: $repo_id, file_path: $file_path, name: $fn_name})
                SET fn.line_start = $line_start, fn.line_end = $line_end
                WITH fn
                MATCH (f:File {repo_id: $repo_id, path: $file_path})
                MERGE (f)-[:CONTAINS]->(fn)
            """, repo_id=repo_id, file_path=file_path, fn_name=fn_name,
                              line_start=line_start, line_end=line_end)

    async def add_import(self, repo_id: str, from_path: str, to_path: str):
        async with get_driver().session() as session:
            await session.run("""
                MATCH (a:File {repo_id: $repo_id, path: $from_path})
                MATCH (b:File {repo_id: $repo_id, path: $to_path})
                MERGE (a)-[:IMPORTS]->(b)
            """, repo_id=repo_id, from_path=from_path, to_path=to_path)

    async def add_function_call(self, repo_id: str, caller: str, callee: str, file_path: str):
        async with get_driver().session() as session:
            await session.run("""
                MERGE (a:Function {repo_id: $repo_id, name: $caller})
                MERGE (b:Function {repo_id: $repo_id, name: $callee})
                MERGE (a)-[:CALLS {file: $file_path}]->(b)
            """, repo_id=repo_id, caller=caller, callee=callee, file_path=file_path)

    async def link_issue_to_files(self, repo_id: str, issue_number: int, file_paths: list[str]):
        async with get_driver().session() as session:
            for path in file_paths:
                await session.run("""
                    MERGE (i:Issue {repo_id: $repo_id, number: $issue_number})
                    MATCH (f:File {repo_id: $repo_id, path: $path})
                    MERGE (i)-[:TOUCHES]->(f)
                """, repo_id=repo_id, issue_number=issue_number, path=path)

    # ── Developer Graph ───────────────────────────────────────
    async def upsert_developer(self, github_id: int, login: str, metadata: dict):
        async with get_driver().session() as session:
            await session.run("""
                MERGE (d:Developer {github_id: $github_id})
                SET d.login = $login,
                    d.avatar_url = $avatar_url,
                    d.updated_at = datetime()
            """, github_id=github_id, login=login, **metadata)

    async def add_skill(self, github_id: int, skill: str, level: float):
        async with get_driver().session() as session:
            await session.run("""
                MERGE (s:Skill {name: $skill})
                MATCH (d:Developer {github_id: $github_id})
                MERGE (d)-[r:KNOWS]->(s)
                SET r.level = $level, r.updated_at = datetime()
            """, github_id=github_id, skill=skill, level=level)

    async def add_technology(self, github_id: int, tech: str, percentage: float):
        async with get_driver().session() as session:
            await session.run("""
                MERGE (t:Technology {name: $tech})
                MATCH (d:Developer {github_id: $github_id})
                MERGE (d)-[r:USES]->(t)
                SET r.percentage = $percentage
            """, github_id=github_id, tech=tech, percentage=percentage)

    async def track_repo_visit(self, github_id: int, full_name: str):
        async with get_driver().session() as session:
            await session.run("""
                MATCH (d:Developer {github_id: $github_id})
                MERGE (r:Repository {full_name: $full_name})
                MERGE (d)-[v:EXPLORED]->(r)
                SET v.last_visited = datetime(),
                    v.count = coalesce(v.count, 0) + 1
            """, github_id=github_id, full_name=full_name)

    async def track_learning_progress(self, github_id: int, concept: str, repo_full_name: str):
        async with get_driver().session() as session:
            await session.run("""
                MATCH (d:Developer {github_id: $github_id})
                MERGE (c:Concept {name: $concept})
                MERGE (d)-[l:LEARNED]->(c)
                SET l.repo = $repo_full_name, l.timestamp = datetime()
            """, github_id=github_id, concept=concept, repo_full_name=repo_full_name)

    # ── Queries ───────────────────────────────────────────────
    async def get_developer_skills(self, github_id: int) -> list[dict]:
        async with get_driver().session() as session:
            result = await session.run("""
                MATCH (d:Developer {github_id: $github_id})-[r:KNOWS]->(s:Skill)
                RETURN s.name AS skill, r.level AS level
                ORDER BY r.level DESC
            """, github_id=github_id)
            return [dict(r) async for r in result]

    async def get_repo_files_for_issue(self, repo_id: str, issue_number: int) -> list[str]:
        async with get_driver().session() as session:
            result = await session.run("""
                MATCH (i:Issue {repo_id: $repo_id, number: $issue_number})-[:TOUCHES]->(f:File)
                RETURN f.path AS path
            """, repo_id=repo_id, issue_number=issue_number)
            return [r["path"] async for r in result]

    async def get_related_files(self, repo_id: str, file_path: str, depth: int = 2) -> list[dict]:
        """Get files connected via imports within N hops."""
        async with get_driver().session() as session:
            result = await session.run("""
                MATCH (start:File {repo_id: $repo_id, path: $file_path})
                MATCH (start)-[:IMPORTS*1..$depth]-(related:File)
                WHERE related.path <> $file_path
                RETURN DISTINCT related.path AS path, related.type AS type
                LIMIT 20
            """, repo_id=repo_id, file_path=file_path, depth=depth)
            return [dict(r) async for r in result]

    async def get_developer_knowledge_graph(self, github_id: int) -> dict:
        """Return full developer graph for visualization."""
        async with get_driver().session() as session:
            # Nodes
            skills = await self.get_developer_skills(github_id)

            result = await session.run("""
                MATCH (d:Developer {github_id: $github_id})-[r]->(n)
                RETURN type(r) AS rel_type, labels(n)[0] AS node_type, n.name AS name,
                       properties(r) AS rel_props
                LIMIT 100
            """, github_id=github_id)
            edges = [dict(r) async for r in result]

        return {"skills": skills, "connections": edges}

    async def get_repo_architecture(self, repo_id: str) -> dict:
        """Return repository graph structure for diagram generation."""
        async with get_driver().session() as session:
            result = await session.run("""
                MATCH (f:File {repo_id: $repo_id})
                OPTIONAL MATCH (f)-[:IMPORTS]->(dep:File {repo_id: $repo_id})
                RETURN f.path AS file, collect(dep.path) AS imports
                LIMIT 200
            """, repo_id=repo_id)
            files = [dict(r) async for r in result]

        return {"files": files}


# Singleton
_graph_service: Optional[GraphService] = None


def get_graph_service() -> GraphService:
    global _graph_service
    if _graph_service is None:
        _graph_service = GraphService()
    return _graph_service
