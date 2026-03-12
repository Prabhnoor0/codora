"""
Skills analysis service — extract developer expertise from GitHub profile data.
"""
import structlog

log = structlog.get_logger()

EXPERTISE_THRESHOLDS = {
    "beginner": {"repos": 0, "commits": 0},
    "intermediate": {"repos": 8, "commits": 10},
    "advanced": {"repos": 25, "commits": 30},
    "expert": {"repos": 60, "commits": 100},
}

LANGUAGE_CONCEPTS = {
    "Python": ["OOP", "Functional Programming", "Async IO", "Data Structures"],
    "JavaScript": ["Async/Await", "Closures", "Event Loop", "Promises"],
    "TypeScript": ["Type System", "Generics", "Decorators", "Interfaces"],
    "Go": ["Goroutines", "Channels", "Interfaces", "Error Handling"],
    "Rust": ["Ownership", "Lifetimes", "Traits", "Concurrency"],
    "Java": ["OOP", "Spring", "JVM", "Concurrency"],
}

DOMAIN_KEYWORDS = {
    "backend": ["api", "server", "database", "backend", "fastapi", "django", "flask", "express"],
    "frontend": ["react", "vue", "angular", "ui", "frontend", "web", "css"],
    "ml": ["machine-learning", "deep-learning", "pytorch", "tensorflow", "model", "ml", "ai"],
    "devops": ["docker", "kubernetes", "ci", "cd", "deploy", "infrastructure", "terraform"],
    "mobile": ["ios", "android", "react-native", "flutter", "mobile"],
    "data": ["data", "analytics", "pandas", "spark", "etl", "pipeline"],
}


class SkillExtractor:
    def extract_from_profile(self, github_profile: dict) -> dict:
        """Extract structured skills from aggregated GitHub data."""
        top_langs = github_profile.get("top_languages", [])
        lang_breakdown = github_profile.get("language_breakdown", {})
        topics = github_profile.get("top_topics", [])
        repos = github_profile.get("total_repos", 0)
        commits = github_profile.get("recent_commits", 0)
        prs = github_profile.get("recent_prs", 0)

        # Expertise level
        expertise = self._compute_expertise(repos, commits, prs)

        # Skill vector: language → proficiency 0.0-1.0
        skill_vector = {}
        for lang, pct in lang_breakdown.items():
            # Normalize: 100% in a language → 1.0, scaled by expertise
            expertise_multiplier = {"beginner": 0.6, "intermediate": 0.75, "advanced": 0.9, "expert": 1.0}
            base_score = min(pct / 100, 1.0)
            skill_vector[lang] = round(base_score * expertise_multiplier.get(expertise, 0.7), 2)

        # Domain detection
        topic_text = " ".join(topics).lower()
        domains = []
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if any(kw in topic_text for kw in keywords):
                domains.append(domain)

        # Key concepts inferred
        concepts = []
        for lang in top_langs[:3]:
            concepts.extend(LANGUAGE_CONCEPTS.get(lang, []))

        return {
            "expertise_level": expertise,
            "skill_vector": skill_vector,
            "top_languages": top_langs,
            "language_breakdown": lang_breakdown,
            "contribution_domains": domains,
            "inferred_concepts": list(set(concepts))[:20],
        }

    def _compute_expertise(self, repos: int, commits: int, prs: int) -> str:
        score = (repos * 0.3) + (commits * 0.5) + (prs * 0.2)
        if score >= 50:
            return "expert"
        elif score >= 20:
            return "advanced"
        elif score >= 6:
            return "intermediate"
        return "beginner"

    def compute_skill_gap(self, user_skills: dict, required_skills: list[str]) -> list[dict]:
        """Compute which required skills the user is missing."""
        gaps = []
        for skill in required_skills:
            user_level = user_skills.get(skill, user_skills.get(skill.lower(), 0.0))
            if user_level < 0.3:
                gaps.append({
                    "skill": skill,
                    "user_level": user_level,
                    "required_level": 0.5,
                    "importance": "high" if user_level == 0 else "medium",
                })
        return gaps
