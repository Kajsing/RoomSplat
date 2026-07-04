from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class DependencyCheck:
    name: str
    available: bool
    kind: str
    detail: str


@dataclass(frozen=True)
class ReconstructionInput:
    frames_dir: Path
    frame_count: int
    width: int
    height: int


@dataclass(frozen=True)
class ReconstructionArtifact:
    name: str
    path: Path
    artifact_type: str
    description: str


@dataclass(frozen=True)
class AdapterAssessment:
    adapter: str
    status: str
    summary: str
    dependencies: list[DependencyCheck] = field(default_factory=list)
    expected_outputs: list[ReconstructionArtifact] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        return self.status == "ready"


class ReconstructionAdapter(Protocol):
    name: str
    description: str

    def assess(self, reconstruction_input: ReconstructionInput) -> AdapterAssessment:
        pass


def python_module_dependency(module_name: str, package_name: str | None = None) -> DependencyCheck:
    label = package_name or module_name
    available = importlib.util.find_spec(module_name) is not None
    return DependencyCheck(
        name=label,
        available=available,
        kind="python_module",
        detail="installed" if available else f"Install with pip if this adapter is selected: {label}",
    )


def executable_dependency(executable_name: str) -> DependencyCheck:
    path = shutil.which(executable_name)
    return DependencyCheck(
        name=executable_name,
        available=path is not None,
        kind="executable",
        detail=path or f"Add {executable_name} to PATH if this adapter is selected.",
    )


def dependencies_available(dependencies: list[DependencyCheck]) -> bool:
    return all(dependency.available for dependency in dependencies)
