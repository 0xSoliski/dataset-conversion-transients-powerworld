"""Shared helpers for the release smoke suite.

Every repository in this publication family ships this file unchanged, so the
release checks read and review identically across projects. The helpers stay
dependency-free on purpose: they must work on a source-only checkout with
nothing but pytest installed, which is the supported CI baseline
(Linux, Python 3.10).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Directories that hold build or tool state rather than published content.
IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "venv",
    }
)


def source_id(path: Path) -> str:
    """Stable, unique pytest id: the path relative to the repository root."""
    return path.relative_to(REPO_ROOT).as_posix()


def published_files() -> list[Path]:
    """Every file this release publishes.

    Inside a checkout this is the tracked set, so a local dataset cache never
    counts as published. Reproducibility testing also runs against a
    ``git archive`` extraction, which carries no Git metadata, so fall back to
    walking the tree there -- an archive only ever contains tracked files.
    """
    if (REPO_ROOT / ".git").exists():
        listing = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
            text=True,
        ).stdout
        paths = (REPO_ROOT / name for name in listing.split("\0") if name)
    else:
        paths = (
            path
            for path in REPO_ROOT.rglob("*")
            if not IGNORED_DIRECTORIES.intersection(path.parts)
        )
    return sorted((path for path in paths if path.is_file()), key=source_id)


def tracked_sources() -> list[Path]:
    """Every published Python source, in a stable order."""
    return [path for path in published_files() if path.suffix == ".py"]


def load_module(relative_path: str) -> ModuleType:
    """Load a published script directly, without importing its heavy stack.

    Experiment entry points sit next to TensorFlow or PyTorch code. Loading one
    by file path keeps the smoke suite runnable with pytest alone.
    """
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
