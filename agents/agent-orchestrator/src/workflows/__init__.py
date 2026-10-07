"""Workflow definitions loader from JSON files."""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class WorkflowStage:
    """Definition of a workflow stage."""

    name: str
    agent: str
    description: str
    enabled: bool = True
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStage":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            agent=data["agent"],
            description=data["description"],
            enabled=data.get("enabled", True),
            config=data.get("config", {}),
        )


@dataclass
class WorkflowDefinition:
    """Definition of a complete workflow."""

    name: str
    description: str
    version: str
    stages: List[WorkflowStage]

    def get_enabled_stages(self) -> List[WorkflowStage]:
        """Get all enabled stages."""
        return [s for s in self.stages if s.enabled]

    def get_stage_by_name(self, name: str) -> Optional[WorkflowStage]:
        """Get a stage by name."""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowDefinition":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            version=data.get("version", "1.0"),
            stages=[WorkflowStage.from_dict(stage) for stage in data.get("stages", [])],
        )


class WorkflowLoader:
    """Loader for JSON-based workflow definitions."""

    def __init__(self, workflows_dir: Optional[str] = None):
        """Initialize workflow loader.

        Args:
            workflows_dir: Directory containing workflow JSON files.
                          Defaults to samples/workflows
        """
        if workflows_dir is None:
            # Default to samples/workflows relative to workspace root
            workflows_dir = Path(__file__).parent.parent.parent / "samples" / "workflows"

        self.workflows_dir = Path(workflows_dir)
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self._load_workflows()

    def _load_workflows(self) -> None:
        """Load all workflow definitions from JSON files."""
        if not self.workflows_dir.exists():
            return

        for json_file in self.workflows_dir.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    workflow = WorkflowDefinition.from_dict(data)
                    self.workflows[workflow.name] = workflow
            except Exception as e:
                raise ValueError(f"Failed to load workflow from {json_file}: {e}")

    def get_workflow(self, name: str) -> WorkflowDefinition:
        """Get a workflow by name.

        Args:
            name: Workflow name

        Returns:
            WorkflowDefinition instance

        Raises:
            ValueError: If workflow not found
        """
        if name not in self.workflows:
            available = ", ".join(self.workflows.keys())
            raise ValueError(f"Unknown workflow '{name}'. Available: {available}")
        return self.workflows[name]

    def list_workflows(self) -> Dict[str, str]:
        """List all available workflows.

        Returns:
            Dictionary of workflow names and descriptions
        """
        return {name: wf.description for name, wf in self.workflows.items()}

    def add_workflow(self, definition: WorkflowDefinition) -> None:
        """Add a workflow definition.

        Args:
            definition: WorkflowDefinition instance
        """
        self.workflows[definition.name] = definition

    def save_workflow(
        self,
        definition: WorkflowDefinition,
        output_path: Optional[str] = None,
    ) -> str:
        """Save a workflow definition to JSON file.

        Args:
            definition: WorkflowDefinition instance
            output_path: Output file path. Defaults to workflows_dir/{name}.json

        Returns:
            Path to saved file
        """
        if output_path is None:
            output_path = self.workflows_dir / f"{definition.name}.json"
        else:
            output_path = Path(output_path)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dictionary
        workflow_dict = {
            "name": definition.name,
            "description": definition.description,
            "version": definition.version,
            "stages": [
                {
                    "name": stage.name,
                    "agent": stage.agent,
                    "description": stage.description,
                    "enabled": stage.enabled,
                    "config": stage.config,
                }
                for stage in definition.stages
            ],
        }

        with open(output_path, "w") as f:
            json.dump(workflow_dict, f, indent=2)

        return str(output_path)


# Global loader instance
_loader: Optional[WorkflowLoader] = None


def get_loader(workflows_dir: Optional[str] = None) -> WorkflowLoader:
    """Get or create the global workflow loader.

    Args:
        workflows_dir: Directory containing workflow JSON files

    Returns:
        WorkflowLoader instance
    """
    global _loader
    if _loader is None:
        _loader = WorkflowLoader(workflows_dir)
    return _loader


def get_workflow(name: str) -> WorkflowDefinition:
    """Get a workflow by name using the global loader.

    Args:
        name: Workflow name

    Returns:
        WorkflowDefinition instance
    """
    return get_loader().get_workflow(name)


def list_workflows() -> Dict[str, str]:
    """List all available workflows using the global loader.

    Returns:
        Dictionary of workflow names and descriptions
    """
    return get_loader().list_workflows()
