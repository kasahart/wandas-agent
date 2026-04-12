"""
SKILL.md 構造チェック

CLAUDE.md に定義された6セクション規約に各スキルが準拠しているか確認する。
スキルの追加・編集時に規約違反を早期検出する。
"""
from pathlib import Path
import re
import pytest

SKILLS_DIR = Path(".claude/skills")
SKILL_FILES = sorted(SKILLS_DIR.glob("*/SKILL.md"))

# テスト ID に使うスキル名を抽出
skill_ids = [f.parent.name for f in SKILL_FILES]


# ---------------------------------------------------------------------------
# 1. フロントマター
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=skill_ids)
def test_has_frontmatter(skill_file):
    content = skill_file.read_text(encoding="utf-8")
    assert content.startswith("---"), "YAML フロントマターで始まること"
    front = content.split("---")[1]
    assert "name:" in front, "フロントマターに name: が必要"
    assert "description:" in front, "フロントマターに description: が必要"


@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=skill_ids)
def test_description_is_not_empty(skill_file):
    content = skill_file.read_text(encoding="utf-8")
    front = content.split("---")[1]
    match = re.search(r"description:\s*(.+)", front)
    assert match and match.group(1).strip(), "description が空"


# ---------------------------------------------------------------------------
# 2. 必須ルール
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=skill_ids)
def test_has_wandas_first_rule(skill_file):
    content = skill_file.read_text(encoding="utf-8")
    assert re.search(r"[Ww]andas.?[Ff]irst", content), \
        "Wandas-first ルールが必要（scipy/numpy 直接実装禁止の明記）"


@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=skill_ids)
def test_has_visualization_rule(skill_file):
    content = skill_file.read_text(encoding="utf-8")
    # wandas-analyst はオーケストレーターなので可視化ルールは任意
    if "wandas-analyst" in str(skill_file):
        pytest.skip("wandas-analyst はオーケストレーターのためスキップ")
    # "matplotlib 禁止" または "plt.plot 禁止" のいずれかの表現を許容
    assert re.search(r"matplotlib|plt\.plot|plt\.show", content), \
        "matplotlib 直接描画禁止ルールが必要（matplotlib または plt.plot への言及）"


# ---------------------------------------------------------------------------
# 3. API テーブル
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=skill_ids)
def test_has_api_table(skill_file):
    content = skill_file.read_text(encoding="utf-8")
    # markdown テーブルの区切り行（|---|）が存在するか
    assert re.search(r"\|[-\s|]+\|", content), \
        "API サマリーテーブルが必要（| method | args | return | 形式）"


# ---------------------------------------------------------------------------
# 4. Patterns（コードスニペット）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=skill_ids)
def test_has_python_code_block(skill_file):
    content = skill_file.read_text(encoding="utf-8")
    assert "```python" in content, \
        "Python コードブロックが必要（Patterns セクション）"


@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=skill_ids)
def test_code_blocks_use_wandas(skill_file):
    content = skill_file.read_text(encoding="utf-8")
    code_blocks = re.findall(r"```python(.*?)```", content, re.DOTALL)
    has_wandas = any("wandas" in block or "wd." in block for block in code_blocks)
    assert has_wandas, "コードブロックに wandas の使用例が必要"


# ---------------------------------------------------------------------------
# 5. Common Mistakes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=skill_ids)
def test_has_common_mistakes_section(skill_file):
    content = skill_file.read_text(encoding="utf-8")
    assert re.search(r"[Cc]ommon\s+[Mm]istakes?", content), \
        "Common Mistakes セクションが必要"


# ---------------------------------------------------------------------------
# 6. Documentation Map
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=skill_ids)
def test_has_documentation_map_section(skill_file):
    content = skill_file.read_text(encoding="utf-8")
    assert re.search(r"[Dd]ocumentation\s+[Mm]ap", content), \
        "Documentation Map セクションが必要"


@pytest.mark.parametrize("skill_file", SKILL_FILES, ids=skill_ids)
def test_documentation_map_links_exist(skill_file):
    """Documentation Map で参照しているファイルが実際に存在するか"""
    content = skill_file.read_text(encoding="utf-8")
    # [text](path) 形式のリンクを抽出
    links = re.findall(r"\[.*?\]\((\.\.?/[^)]+)\)", content)
    skill_dir = skill_file.parent
    missing = []
    for link in links:
        target = (skill_dir / link).resolve()
        if not target.exists():
            missing.append(link)
    assert not missing, f"存在しないファイルへのリンク: {missing}"
