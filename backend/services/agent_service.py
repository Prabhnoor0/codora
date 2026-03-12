"""
Multi-Agent LLM Orchestration System using LangGraph.
Implements 6 specialized agents: RepositoryAnalyst, CodeExplainer,
MentorAgent, IssueTutor, PRReviewer, RecommendationAgent.
"""
import json
from typing import Optional, AsyncGenerator
import structlog

from services.llm_service import get_llm_service
from services.rag_service import get_rag_service
from services.graph_service import get_graph_service

log = structlog.get_logger()


# ── System Prompts ────────────────────────────────────────────

REPO_ANALYST_PROMPT = """You are a Senior Software Architect and Repository Analyst specializing in open source projects.
Your task is to analyze codebases and generate clear, actionable architectural insights.
Focus on: system architecture, key modules, data flows, design patterns, and contribution opportunities.
Always structure your analysis to help a developer understand and contribute to the codebase quickly.
Be specific, technical, and accurate. Never hallucinate file names or functions."""

CODE_EXPLAINER_PROMPT = """You are an expert code educator who can explain any codebase to developers at any skill level.
You receive code context from the repository and explain it clearly.
For each explanation: state the purpose, describe key functions/classes, identify design patterns, explain data flow.
Provide BOTH a beginner explanation and an advanced technical explanation.
Always reference actual code from the context provided. Never make up code."""

MENTOR_PROMPT = """You are an experienced open source mentor helping developers contribute to repositories.
You have full context of the repository's architecture, code, and documentation.
Answer questions about: where to implement features, which files to study, how systems work, architectural decisions.
Always ground answers in the actual repository code provided as context.
Be encouraging, specific, and actionable. Provide code examples when helpful."""

ISSUE_TUTOR_PROMPT = """You are an Issue Tutor that transforms GitHub issues into structured learning experiences.
For each issue: identify required concepts, find relevant code in the repository, suggest learning path.
Structure your response to help a developer go from "I don't know where to start" to "I can implement this".
Include: concept explanations, relevant files to study, similar patterns in the codebase, implementation hints."""

PR_REVIEWER_PROMPT = """You are an expert code reviewer with deep knowledge of software engineering best practices.
Review pull request diffs for: bugs, security vulnerabilities, performance issues, style violations, architectural problems.
For each issue: specify the file, line number (if available), severity (critical/major/minor), explanation, and suggested fix.
Be constructive, specific, and educational. Also highlight positive aspects of the PR."""

RECOMMENDATION_PROMPT = """You are a Contribution Recommendation Agent that matches developers to suitable issues.
Based on developer skills, experience level, and repository context, recommend the most appropriate issues.
Explain WHY each issue is recommended and what the developer will learn from it.
Calculate a readiness score and identify any skill gaps to bridge."""


class AgentService:
    def __init__(self):
        self.llm = get_llm_service()
        self.rag = get_rag_service()
        self.graph = get_graph_service()

    # ── Repository Analyst ────────────────────────────────────
    async def analyze_repository(
        self,
        repo_data: dict,
        readme: Optional[str] = None,
        file_tree: Optional[list] = None,
        languages: Optional[dict] = None,
    ) -> dict:
        """Generate comprehensive repository analysis."""

        file_tree_summary = "\n".join(
            [f"  {f['path']}" for f in (file_tree or [])[:100]]
        )
        lang_summary = json.dumps(languages or {})

        user_prompt = f"""Analyze this repository and provide a structured JSON response.

Repository: {repo_data.get('full_name')}
Description: {repo_data.get('description', 'N/A')}
Stars: {repo_data.get('stargazers_count', 0)}
Languages: {lang_summary}

README (first 3000 chars):
{(readme or 'Not available')[:3000]}

File Tree (sample):
{file_tree_summary}

Return JSON with EXACTLY this structure:
{{
  "purpose": "One paragraph describing what this project does",
  "tech_stack": ["list", "of", "technologies"],
  "architecture_type": "microservices|monolith|library|framework|tool",
  "architecture_summary": "Paragraph describing the architecture",
  "main_modules": [
    {{"name": "ModuleName", "path": "src/module", "description": "What it does", "key_files": ["file1", "file2"]}}
  ],
  "subsystems": [
    {{
      "name": "Authentication",
      "description": "Handles user login, OAuth, JWT",
      "files": ["auth/login.py", "auth/oauth.py"],
      "complexity": "medium",
      "color": "#6366f1"
    }}
  ],
  "difficulty_level": "beginner|intermediate|advanced|expert",
  "contribution_opportunities": [
    {{"area": "Documentation", "description": "...", "difficulty": "easy"}}
  ],
  "learning_prerequisites": ["Python", "REST APIs", "PostgreSQL"],
  "architecture_nodes": [
    {{"id": "api", "label": "API Layer", "type": "service", "x": 100, "y": 100}},
    {{"id": "db", "label": "Database", "type": "database", "x": 300, "y": 200}}
  ],
  "architecture_edges": [
    {{"source": "api", "target": "db", "label": "queries"}}
  ]
}}"""

        result = await self.llm.complete_json(REPO_ANALYST_PROMPT, user_prompt)
        return result

    async def generate_subsystems(self, repo_data: dict, file_tree: list, readme: str) -> list[dict]:
        """Identify logical subsystems from file structure."""
        file_paths = [f["path"] for f in file_tree if f.get("type") == "blob"][:200]

        user_prompt = f"""Repository: {repo_data.get('full_name')}

File paths:
{chr(10).join(file_paths)}

README excerpt:
{readme[:2000]}

Group these files into logical SUBSYSTEMS (like Auth, Payments, Database, API, etc.).
Return JSON array:
[
  {{
    "name": "Authentication",
    "description": "Handles user authentication, OAuth, JWT tokens",
    "files": ["auth/login.py", "middleware/auth.py"],
    "key_concepts": ["OAuth 2.0", "JWT", "Sessions"],
    "complexity": "medium",
    "color": "#8b5cf6",
    "icon": "shield"
  }}
]

Create 5-12 subsystems. Only use files that exist in the provided list."""

        return await self.llm.complete_json(REPO_ANALYST_PROMPT, user_prompt)

    # ── Code Explainer ────────────────────────────────────────
    async def explain_file(self, repo_id: str, file_path: str, content: str, user_level: str = "intermediate") -> dict:
        """Explain a specific file using RAG context."""
        related = await self.rag.search_code(repo_id, f"related to {file_path}", top_k=3)
        related_context = "\n".join([f"--- {r['file_path']} ---\n{r['content'][:500]}" for r in related])

        user_prompt = f"""Explain this file from the repository:

File: {file_path}
Developer Level: {user_level}

=== File Content ===
{content[:4000]}

=== Related Files Context ===
{related_context}

Return JSON:
{{
  "purpose": "What this file does in one sentence",
  "summary": "Detailed paragraph explanation",
  "functions": [
    {{"name": "functionName", "signature": "def func(args)", "purpose": "what it does", "complexity": "simple|moderate|complex"}}
  ],
  "classes": [
    {{"name": "ClassName", "purpose": "what it represents", "key_methods": ["method1", "method2"]}}
  ],
  "design_patterns": ["Singleton", "Factory"],
  "dependencies": ["imported_module1", "imported_module2"],
  "data_flow": "How data enters and exits this file",
  "related_files": ["{file_path}"],
  "beginner_explanation": "Simple explanation for newcomers",
  "advanced_explanation": "Deep technical explanation for experts",
  "contribution_tips": "How a developer could improve or extend this"
}}"""

        return await self.llm.complete_json(CODE_EXPLAINER_PROMPT, user_prompt)

    # ── Mentor Agent ──────────────────────────────────────────
    async def mentor_chat(
        self,
        repo_id: str,
        repo_full_name: str,
        question: str,
        conversation_history: list[dict],
        developer_profile: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """Repository-aware streaming mentor chat."""
        # Get relevant context from RAG
        rag_context = await self.rag.build_rag_context(repo_id, question, max_tokens=2000)

        # Build conversation history string
        history_str = "\n".join([
            f"{msg['role'].upper()}: {msg['content'][:500]}"
            for msg in conversation_history[-6:]
        ])

        dev_context = ""
        if developer_profile:
            dev_context = f"""
Developer Profile:
- Skill level: {developer_profile.get('expertise_level', 'unknown')}
- Top languages: {', '.join(developer_profile.get('top_languages', [])[:3])}
- Experience: {developer_profile.get('expertise_level', 'intermediate')}
"""

        system = MENTOR_PROMPT + f"\n\nYou are helping with repository: {repo_full_name}"

        user_prompt = f"""{dev_context}

=== Repository Code Context ===
{rag_context or 'No specific context retrieved for this question.'}

=== Conversation History ===
{history_str}

=== Developer Question ===
{question}

Provide a helpful, specific answer based on the actual repository code above.
When referencing files or functions, use their exact names from the context."""

        async for chunk in self.llm.stream(system, user_prompt):
            yield chunk

    # ── Issue Tutor ───────────────────────────────────────────
    async def tutor_issue(self, repo_id: str, repo_full_name: str, issue: dict, developer_profile: Optional[dict] = None) -> dict:
        """Convert a GitHub issue into a structured learning experience."""
        # Find relevant files for this issue
        relevant_files = await self.rag.find_similar_files(
            repo_id, f"{issue.get('title')} {issue.get('body', '')[:500]}", top_k=8
        )
        rag_context = await self.rag.build_rag_context(
            repo_id, f"{issue.get('title')} {issue.get('body', '')[:300]}", max_tokens=2000
        )

        dev_level = developer_profile.get("expertise_level", "intermediate") if developer_profile else "intermediate"

        user_prompt = f"""Convert this GitHub issue into a learning experience for a {dev_level} developer.

Repository: {repo_full_name}
Issue #{issue.get('number')}: {issue.get('title')}
Labels: {', '.join([lbl.get('name', '') for lbl in (issue.get('labels') or [])])}
Issue Body:
{(issue.get('body') or '')[:2000]}

Relevant Repository Files:
{json.dumps(relevant_files[:5])}

Repository Code Context:
{rag_context}

Return JSON:
{{
  "difficulty": "easy|medium|hard",
  "estimated_time": "2 hours|1 day|3 days",
  "required_concepts": [
    {{"concept": "REST APIs", "description": "...", "resource": "https://..."}}
  ],
  "skill_requirements": ["Python", "FastAPI", "PostgreSQL"],
  "files_to_study": [
    {{"path": "src/api/routes.py", "reason": "This is where you'll make changes", "priority": "high"}}
  ],
  "implementation_hints": [
    "Step 1: Understand the existing pattern in auth/login.py",
    "Step 2: Add your route handler following the same pattern"
  ],
  "similar_examples_in_repo": [
    {{"description": "Similar feature was implemented in...", "file": "src/example.py"}}
  ],
  "learning_resources": [
    {{"title": "FastAPI Docs", "url": "https://fastapi.tiangolo.com", "type": "documentation"}}
  ],
  "testing_approach": "How to test your implementation",
  "gotchas": ["Watch out for...", "Don't forget to..."]
}}"""

        return await self.llm.complete_json(ISSUE_TUTOR_PROMPT, user_prompt)

    # ── PR Reviewer ───────────────────────────────────────────
    async def review_pr(self, repo_id: str, repo_full_name: str, pr_data: dict, diff: str) -> dict:
        """Perform comprehensive AI review of a pull request."""
        rag_context = await self.rag.build_rag_context(repo_id, pr_data.get("title", ""), max_tokens=1500)

        user_prompt = f"""Review this pull request for {repo_full_name}.

PR #{pr_data.get('number')}: {pr_data.get('title')}
Description: {(pr_data.get('body') or '')[:1000]}

=== Repository Context (relevant files) ===
{rag_context}

=== Diff ===
{diff[:6000]}

Return JSON:
{{
  "overall_assessment": "Summary of the PR quality",
  "quality_score": 75,
  "approved": false,
  "bugs": [
    {{"severity": "critical|major|minor", "file": "path/to/file.py", "line": 42, "description": "Bug description", "suggestion": "How to fix"}}
  ],
  "security_issues": [
    {{"severity": "critical|major", "description": "...", "suggestion": "..."}}
  ],
  "performance_issues": [
    {{"description": "...", "suggestion": "..."}}
  ],
  "style_issues": [
    {{"file": "...", "description": "...", "suggestion": "..."}}
  ],
  "architecture_violations": [
    {{"description": "This breaks the separation of concerns because...", "suggestion": "..."}}
  ],
  "positive_aspects": [
    "Good use of type hints",
    "Clear variable naming"
  ],
  "suggestions": [
    "Consider adding unit tests for the new function",
    "The error handling could be more specific"
  ],
  "summary_for_developer": "Encouraging message with key takeaways"
}}"""

        return await self.llm.complete_json(PR_REVIEWER_PROMPT, user_prompt)

    # ── Learning Path Generator ────────────────────────────────
    async def generate_learning_path(
        self,
        repo_id: str,
        repo_data: dict,
        developer_profile: dict,
        target_issue: Optional[dict] = None,
    ) -> dict:
        """Generate personalized day-by-day learning path."""
        arch_summary = repo_data.get("architecture_summary", "")
        tech_stack = repo_data.get("tech_stack", [])
        dev_skills = developer_profile.get("top_languages", [])
        expertise = developer_profile.get("expertise_level", "beginner")
        prereqs = repo_data.get("learning_prerequisites", [])

        user_prompt = f"""Create a personalized learning roadmap.

Repository: {repo_data.get('full_name')}
Tech Stack: {', '.join(tech_stack)}
Architecture: {arch_summary[:500]}
Prerequisites: {', '.join(prereqs)}

Developer Profile:
- Expertise: {expertise}
- Known languages: {', '.join(dev_skills)}
{"- Target Issue: " + target_issue.get('title') if target_issue else ""}

Return JSON:
{{
  "title": "Learning path title",
  "description": "What the developer will achieve",
  "total_days": 7,
  "plan": [
    {{
      "day": 1,
      "title": "Repository Architecture Overview",
      "objectives": ["Understand the project structure", "Learn the tech stack"],
      "concepts": ["Microservices", "REST API"],
      "files_to_read": ["README.md", "docs/architecture.md", "src/main.py"],
      "exercises": ["Run the project locally", "Read through the main entry point"],
      "resources": [
        {{"title": "FastAPI Tutorial", "url": "https://fastapi.tiangolo.com/tutorial", "duration": "30 min"}}
      ],
      "xp_reward": 100
    }}
  ]
}}

Create {5 if expertise == 'beginner' else 7} days. Day 1 should always be architecture overview.
Final day should relate to making a real contribution."""

        return await self.llm.complete_json(MENTOR_PROMPT, user_prompt)

    # ── Readiness Score Calculator ────────────────────────────
    async def calculate_readiness(
        self,
        issue: dict,
        developer_profile: dict,
        repo_data: dict,
    ) -> dict:
        """Calculate contribution readiness score for an issue."""
        dev_skills = developer_profile.get("skill_vector", {})
        dev_languages = developer_profile.get("top_languages", [])
        issue_skills = issue.get("required_skills", [])
        repo_prereqs = repo_data.get("learning_prerequisites", [])

        user_prompt = f"""Calculate a contribution readiness score.

Issue: {issue.get('title')}
Issue Difficulty: {issue.get('difficulty', 'unknown')}
Required Skills: {', '.join(issue_skills or [])}
Repository Prerequisites: {', '.join(repo_prereqs or [])}

Developer:
- Languages: {', '.join(dev_languages)}
- Expertise Level: {developer_profile.get('expertise_level', 'beginner')}
- Skill Scores: {json.dumps(dev_skills or {})}

Return JSON:
{{
  "readiness_score": 72,
  "skill_match_score": 80,
  "difficulty_match_score": 65,
  "familiarity_score": 70,
  "breakdown": {{
    "strengths": ["Python proficiency matches requirement", "Has REST API experience"],
    "gaps": ["No Redux experience", "Unfamiliar with this specific framework"]
  }},
  "missing_skills": [
    {{"skill": "Redux", "importance": "high", "learning_time": "2 days", "resource": "https://redux.js.org"}}
  ],
  "ready_to_contribute": false,
  "recommendation": "Study Redux fundamentals first, then tackle this issue",
  "estimated_completion_time": "3-5 days"
}}"""

        return await self.llm.complete_json(RECOMMENDATION_PROMPT, user_prompt)


# Singleton
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
