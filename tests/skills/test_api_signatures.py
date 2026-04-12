"""
API シグネチャ照合テスト

SKILL.md に記載されたメソッド名・引数名が wandas ソースコードに実際に存在するか確認する。
wandas のアップデートで API が変わった場合にスキルの陳腐化を早期検出する。
"""
from pathlib import Path
import re
import pytest

WANDAS_SRC = Path("wandas/wandas")


def grep_in_source(pattern: str) -> list[str]:
    """wandas ソース内で pattern にマッチする行を返す"""
    results = []
    for py_file in WANDAS_SRC.rglob("*.py"):
        for line in py_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            if re.search(pattern, line):
                results.append(f"{py_file}:{line.strip()}")
    return results


def method_exists(method_name: str) -> bool:
    return bool(grep_in_source(rf"\bdef {re.escape(method_name)}\b"))


def param_exists_in_method(method_name: str, param_name: str) -> bool:
    """メソッド定義の近傍（複数行シグネチャ対応）に引数名が含まれるか"""
    for py_file in WANDAS_SRC.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(rf"\bdef {re.escape(method_name)}\b", text):
            # def 行から最大 500 文字を見る（複数行シグネチャに対応）
            snippet = text[match.start():match.start() + 500]
            if param_name in snippet:
                return True
    return False


# ---------------------------------------------------------------------------
# メソッド存在チェック
# ---------------------------------------------------------------------------

REQUIRED_METHODS = [
    # I/O
    "read_wav",
    "read_csv",
    "generate_sin",
    "from_numpy",
    # フィルタ
    "high_pass_filter",
    "low_pass_filter",
    "band_pass_filter",
    "a_weighting",
    "normalize",
    "remove_dc",
    # 時間操作
    "resampling",
    "trim",
    "fix_length",
    # 音圧
    "sound_level",
    "rms_trend",
    # 心理音響
    "loudness_zwtv",
    "loudness_zwst",
    "roughness_dw",
    "roughness_dw_spec",
    "sharpness_din",
    "sharpness_din_st",
    # スペクトル
    "fft",
    "ifft",
    "stft",
    "istft",
    "welch",
    "noct_spectrum",
    "coherence",
    "csd",
    "transfer_function",
]


@pytest.mark.parametrize("method_name", REQUIRED_METHODS)
def test_method_exists_in_source(method_name):
    assert method_exists(method_name), \
        f"def {method_name} が wandas ソースに見つからない — スキルの記述が古い可能性"


# ---------------------------------------------------------------------------
# 重要な引数名チェック
# 過去に間違いが起きた / 混同しやすい引数名を明示的に検証する
# ---------------------------------------------------------------------------

CRITICAL_PARAMS = [
    # (method_name, correct_param, wrong_param_hint)
    ("band_pass_filter", "low_cutoff",  "low ではなく low_cutoff"),
    ("band_pass_filter", "high_cutoff", "high ではなく high_cutoff"),
    ("high_pass_filter", "cutoff",      "high_cutoff ではなく cutoff"),
    ("low_pass_filter",  "cutoff",      "low_cutoff ではなく cutoff"),
    ("noct_spectrum",    "fmin",        "freq_min ではなく fmin"),
    ("noct_spectrum",    "fmax",        "freq_max ではなく fmax"),
    ("loudness_zwtv",    "field_type",  "field ではなく field_type"),
    ("loudness_zwst",    "field_type",  "field ではなく field_type"),
    ("sharpness_din_st", "field_type",  "field ではなく field_type"),
]


@pytest.mark.parametrize("method_name,param_name,hint", CRITICAL_PARAMS,
                         ids=[f"{m}-{p}" for m, p, _ in CRITICAL_PARAMS])
def test_critical_param_exists(method_name, param_name, hint):
    assert param_exists_in_method(method_name, param_name), \
        f"{method_name} の引数 '{param_name}' が見つからない（{hint}）"


# ---------------------------------------------------------------------------
# デフォルト値チェック
# スキルに記載したデフォルト値が実際と一致するか
# ---------------------------------------------------------------------------

DEFAULT_CHECKS = [
    # (method_name, expected_default_substring)
    # 型アノテーション付き形式（dB: bool = False）でチェック
    ("sound_level",  "= False"),    # dB のデフォルトは False（True ではない）
    ("band_pass_filter", "= 4"),    # order のデフォルトは 4
    ("high_pass_filter", "= 4"),
    ("low_pass_filter",  "= 4"),
]


@pytest.mark.parametrize("method_name,expected_default", DEFAULT_CHECKS,
                         ids=[f"{m}-default" for m, _ in DEFAULT_CHECKS])
def test_default_value_matches_source(method_name, expected_default):
    """def 行から 500 文字以内にデフォルト値の記述があるか確認（複数行シグネチャ対応）"""
    for py_file in WANDAS_SRC.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(rf"\bdef {re.escape(method_name)}\b", text):
            snippet = text[match.start():match.start() + 500]
            if expected_default in snippet:
                return  # found
    pytest.fail(f"{method_name} のデフォルト値 '{expected_default}' がソースに見つからない")
