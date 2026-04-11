新しい wandas スキル `$ARGUMENTS` を作成してください。

## 手順（必ず順番通りに実行）

1. `wandas/wandas/` を Grep/Read して `$ARGUMENTS` に関連する API のシグネチャ・引数名・返り値を確認する
2. `CLAUDE.md` のフォーマット規約と既存スキル（`.claude/skills/wandas-signal-analysis/`）のスタイルを参照する
3. 以下のファイルを作成する：
   - `.claude/skills/$ARGUMENTS/SKILL.md`
   - `.claude/skills/$ARGUMENTS/examples/workflows.md`
   - `.claude/skills/$ARGUMENTS/references/<topic>_api.md`
4. SKILL.md の `description:` はユーザーの具体的な操作（動詞＋目的語）で書く
5. 作成したコードスニペットの引数名がソースと一致していることを確認する
