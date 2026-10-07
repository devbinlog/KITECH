"""
Shared Skills Library

This module provides the skills catalog for manufacturing agents.
Skills are divided into two categories:

1. Domain Skills: Executed by agents during runtime (gcode analysis, scheduling, etc.)
2. Development Skills: Used by Claude during code maintenance and extension

All skills are defined in markdown format with standardized input/output schemas.
"""

__all__ = [
    "DOMAIN_SKILLS",
    "DEVELOPMENT_SKILLS",
    "load_skill",
    "list_skills",
]

# Skill registry
DOMAIN_SKILLS = {
    "gcode_analysis",
    "cam_computation",
    "manufacturing_scheduling",
    "schedule_visualization",
    "workflow_orchestration",
}

DEVELOPMENT_SKILLS = {
    "test_implementation",
    "config_management",
    "data_validation",
    "error_handling",
    "code_documentation",
    "performance_optimization",
    "dependency_integration",
}

ALL_SKILLS = DOMAIN_SKILLS | DEVELOPMENT_SKILLS


def load_skill(skill_name: str) -> dict:
    """Load a skill definition by name.

    Args:
        skill_name: Name of the skill to load (without .md extension)

    Returns:
        Dictionary with skill metadata and content

    Raises:
        FileNotFoundError: If skill markdown file not found
        ValueError: If skill_name not registered
    """
    if skill_name not in ALL_SKILLS:
        raise ValueError(f"Unknown skill: {skill_name}. Available: {sorted(ALL_SKILLS)}")

    import os

    skill_dir = os.path.dirname(__file__)
    skill_file = os.path.join(skill_dir, f"{skill_name}.md")

    if not os.path.exists(skill_file):
        raise FileNotFoundError(f"Skill file not found: {skill_file}")

    with open(skill_file, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "name": skill_name,
        "category": "domain" if skill_name in DOMAIN_SKILLS else "development",
        "content": content,
        "file_path": skill_file,
    }


def list_skills(category: str = None) -> list:
    """List available skills.

    Args:
        category: Filter by "domain", "development", or None for all

    Returns:
        Sorted list of skill names
    """
    if category == "domain":
        return sorted(DOMAIN_SKILLS)
    elif category == "development":
        return sorted(DEVELOPMENT_SKILLS)
    elif category is None:
        return sorted(ALL_SKILLS)
    else:
        raise ValueError(f"Unknown category: {category}")
