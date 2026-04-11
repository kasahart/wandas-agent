wandas スキル `$ARGUMENTS` を最新の wandas API に合わせて更新してください。

## 手順（必ず順番通りに実行）

1. `wandas/wandas/` で `$ARGUMENTS` に関連するファイルを Grep し、現在の API シグネチャを確認する
2. `.claude/skills/$ARGUMENTS/` の既存ファイルをすべて Read する
3. ソースと既存スキルの差分（変更・追加・削除されたメソッド）を洗い出す
4. SKILL.md・examples/workflows.md・references/ を差分に合わせて更新する
5. 引数名の変更があれば Common Mistakes に追記する
