"""Static checks that skill-facing Wandas 0.7.2 API contracts still exist."""

from __future__ import annotations

import ast
from pathlib import Path
import re

import pytest


WANDAS_SRC = Path("wandas/wandas")
SKILLS_DIR = Path(".claude/skills")


def source_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in WANDAS_SRC.rglob("*.py"))


def method_exists(method_name: str) -> bool:
    return re.search(rf"\bdef {re.escape(method_name)}\b", source_text()) is not None


def function_nodes(method_name: str) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    nodes: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for path in WANDAS_SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        nodes.extend(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name
        )
    return nodes


def param_exists(method_name: str, param_name: str) -> bool:
    for node in function_nodes(method_name):
        names = {
            arg.arg
            for arg in [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ]
        }
        if param_name in names:
            return True
    return False


REQUIRED_METHODS = [
    "read",
    "load",
    "supported_formats",
    "from_numpy",
    "from_folder",
    "generate_sin",
    "cache",
    "astype",
    "concat_frame",
    "with_calibration",
    "high_pass_filter",
    "low_pass_filter",
    "band_pass_filter",
    "a_weighting",
    "normalize",
    "remove_dc",
    "resampling",
    "trim",
    "fix_length",
    "sound_level",
    "rms_trend",
    "loudness_zwtv",
    "loudness_zwst",
    "roughness_dw",
    "roughness_dw_spec",
    "sharpness_din",
    "sharpness_din_st",
    "fft",
    "ifft",
    "stft",
    "istft",
    "welch",
    "cepstrum",
    "noct_spectrum",
    "coherence",
    "csd",
    "transfer_function",
    "select_pair",
    "get_frame_at",
]


@pytest.mark.parametrize("method_name", REQUIRED_METHODS)
def test_method_exists_in_source(method_name):
    assert method_exists(method_name), f"def {method_name} is missing from the pinned Wandas source"


CRITICAL_PARAMS = [
    ("read", "file_type"),
    ("read", "source_name"),
    ("from_folder", "metadata_resolver"),
    ("from_folder", "path_metadata"),
    ("band_pass_filter", "low_cutoff"),
    ("band_pass_filter", "high_cutoff"),
    ("sound_level", "freq_weighting"),
    ("sound_level", "time_weighting"),
    ("cepstrum", "floor"),
    ("noct_spectrum", "fmin"),
    ("noct_spectrum", "fmax"),
    ("csd", "scaling"),
    ("transfer_function", "scaling"),
    ("select_pair", "output"),
    ("select_pair", "input"),
    ("get_frame_at", "time_idx"),
]


@pytest.mark.parametrize("method_name,param_name", CRITICAL_PARAMS)
def test_critical_parameter_exists(method_name, param_name):
    assert param_exists(method_name, param_name), f"{method_name} no longer has parameter {param_name}"


@pytest.mark.parametrize("method_name", ["read", "read_wav"])
def test_read_apis_do_not_have_normalize_parameter(method_name):
    assert not param_exists(method_name, "normalize")


EXPECTED_RETURNS = {
    "coherence": "CoherenceFrame",
    "csd": "CrossSpectralFrame",
    "transfer_function": "TransferFunctionFrame",
}


@pytest.mark.parametrize("method_name,return_name", EXPECTED_RETURNS.items())
def test_pairwise_transform_has_typed_return(method_name, return_name):
    annotations = {
        ast.unparse(node.returns).strip("'\"")
        for node in function_nodes(method_name)
        if node.returns is not None
    }
    assert return_name in annotations


def test_level_reference_is_public():
    init_text = (WANDAS_SRC / "__init__.py").read_text(encoding="utf-8")
    assert '"LevelReference"' in init_text


def test_skills_declare_current_version():
    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    assert skill_files
    for skill_file in skill_files:
        content = skill_file.read_text(encoding="utf-8")
        assert "0.7.2" in content, f"{skill_file} does not identify the pinned Wandas contract"
