"""
wandas-indexing skill snippet execution tests.

The examples in the indexing skill are deliberately written with synthetic
NumPy data so they can be executed without external WAV/CSV fixtures whenever
the real wandas package/submodule is available.
"""
from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import pytest


SKILL_PATHS = [
    Path(".claude/skills/wandas-indexing/SKILL.md"),
    Path(".claude/skills/wandas-indexing/examples/workflows.md"),
]


def _real_wandas_available() -> bool:
    try:
        import wandas as wd  # noqa: F401
    except Exception:
        return False
    return hasattr(wd, "from_numpy")


def _python_blocks(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    return [block.strip() for block in re.findall(r"```python\n(.*?)```", content, re.DOTALL)]


@pytest.mark.parametrize(
    "path,block_index,code",
    [
        (path, idx, code)
        for path in SKILL_PATHS
        for idx, code in enumerate(_python_blocks(path), start=1)
    ],
    ids=lambda value: str(value) if isinstance(value, Path) else None,
)
def test_wandas_indexing_skill_snippet_compiles(path: Path, block_index: int, code: str):
    compile(code, f"{path}#python-block-{block_index}", "exec")


@pytest.mark.skipif(
    not _real_wandas_available(),
    reason="real wandas package/submodule is not available in this environment",
)
@pytest.mark.parametrize(
    "path,block_index,code",
    [
        (path, idx, code)
        for path in SKILL_PATHS
        for idx, code in enumerate(_python_blocks(path), start=1)
    ],
    ids=lambda value: str(value) if isinstance(value, Path) else None,
)
def test_wandas_indexing_skill_snippet_executes(path: Path, block_index: int, code: str):
    namespace: dict[str, object] = {"__name__": "__wandas_indexing_snippet__"}
    exec(compile(code, f"{path}#python-block-{block_index}", "exec"), namespace)


def test_selection_operation_names_are_distinct():
    wd = pytest.importorskip("wandas")
    frame = wd.from_numpy(
        np.ones((2, 100)),
        sampling_rate=100,
        ch_labels=["left", "right"],
    )

    by_query = frame.get_channel(query="left")
    by_index = frame[0]

    assert by_query.operation_history[-1]["operation"] == "wandas.frame.get_channel"
    assert by_index.operation_history[-1]["operation"] == "wandas.frame.index"
