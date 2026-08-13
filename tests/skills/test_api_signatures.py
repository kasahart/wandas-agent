"""Static checks that skill-facing Wandas 0.7.2 API contracts still exist."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest
import wandas as wd


SKILLS_DIR = Path(".claude/skills")


TOP_LEVEL_APIS = [
    "read",
    "load",
    "supported_formats",
    "from_numpy",
    "from_folder",
    "generate_sin",
]


CHANNEL_FRAME_METHODS = [
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
    "stft",
    "welch",
    "cepstrum",
    "noct_spectrum",
    "coherence",
    "csd",
    "transfer_function",
]


@pytest.mark.parametrize("api_name", TOP_LEVEL_APIS)
def test_top_level_api_is_publicly_exported(api_name):
    assert callable(getattr(wd, api_name, None)), f"wd.{api_name} is not publicly callable"


@pytest.mark.parametrize("method_name", CHANNEL_FRAME_METHODS)
def test_channel_frame_method_is_public(method_name):
    assert callable(getattr(wd.ChannelFrame, method_name, None))


@pytest.mark.parametrize(
    "owner,method_name",
    [
        (wd.SpectralFrame, "ifft"),
        (wd.SpectrogramFrame, "istft"),
        (wd.SpectrogramFrame, "get_frame_at"),
        (wd.CoherenceFrame, "select_pair"),
        (wd.CrossSpectralFrame, "select_pair"),
        (wd.TransferFunctionFrame, "select_pair"),
    ],
)
def test_typed_frame_method_is_public(owner, method_name):
    assert callable(getattr(owner, method_name, None))


CRITICAL_PARAMS = [
    (wd, "read", "file_type"),
    (wd, "read", "source_name"),
    (wd, "from_folder", "metadata_resolver"),
    (wd, "from_folder", "path_metadata"),
    (wd.ChannelFrame, "band_pass_filter", "low_cutoff"),
    (wd.ChannelFrame, "band_pass_filter", "high_cutoff"),
    (wd.ChannelFrame, "sound_level", "freq_weighting"),
    (wd.ChannelFrame, "sound_level", "time_weighting"),
    (wd.ChannelFrame, "cepstrum", "floor"),
    (wd.ChannelFrame, "noct_spectrum", "fmin"),
    (wd.ChannelFrame, "noct_spectrum", "fmax"),
    (wd.ChannelFrame, "csd", "scaling"),
    (wd.ChannelFrame, "transfer_function", "scaling"),
    (wd.CoherenceFrame, "select_pair", "output"),
    (wd.CoherenceFrame, "select_pair", "input"),
    (wd.SpectrogramFrame, "get_frame_at", "time_idx"),
]


@pytest.mark.parametrize("owner,method_name,param_name", CRITICAL_PARAMS)
def test_critical_parameter_exists_on_public_owner(owner, method_name, param_name):
    parameters = inspect.signature(getattr(owner, method_name)).parameters
    assert param_name in parameters, f"{owner}.{method_name} no longer has parameter {param_name}"


@pytest.mark.parametrize("api_name", ["read", "read_wav"])
def test_read_apis_do_not_have_normalize_parameter(api_name):
    assert "normalize" not in inspect.signature(getattr(wd, api_name)).parameters


EXPECTED_RETURNS = {
    "coherence": "CoherenceFrame",
    "csd": "CrossSpectralFrame",
    "transfer_function": "TransferFunctionFrame",
}


@pytest.mark.parametrize("method_name,return_name", EXPECTED_RETURNS.items())
def test_pairwise_transform_has_typed_return(method_name, return_name):
    annotation = inspect.signature(getattr(wd.ChannelFrame, method_name)).return_annotation
    assert return_name in str(annotation)


def test_level_reference_is_public():
    assert wd.LevelReference.__module__.startswith("wandas")


def test_skills_declare_current_version():
    skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))
    assert skill_files
    for skill_file in skill_files:
        content = skill_file.read_text(encoding="utf-8")
        assert "0.7.2" in content, f"{skill_file} does not identify the pinned Wandas contract"


def test_analyst_template_includes_dc_and_domain_aware_clipping_checks():
    path = SKILLS_DIR / "wandas-analyst" / "templates" / "analysis_report.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    assert "dc_offset" in source
    assert "near_fs_fraction" in source
    assert "references[index].unit == 'dBFS'" in source


def test_acceleration_workflow_does_not_apply_acoustic_a_weighting():
    path = SKILLS_DIR / "wandas-signal-processing" / "examples" / "workflows.md"
    scenario = path.read_text(encoding="utf-8").split("## Scenario 4:", maxsplit=1)[1]
    scenario = scenario.split("## Scenario 5:", maxsplit=1)[0]
    assert 'unit="m/s^2"' in scenario
    assert "Aw=True" not in scenario
    assert "dB=False" in scenario
