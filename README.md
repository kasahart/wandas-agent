# wandas-agent

Wandas（Python）の信号解析を、Copilot Chat から自律的に実行するための VS Code 拡張です。

## 使い方（ノートブック実行）

1. `.ipynb` を開いて Python カーネルを起動します。
2. 解析対象の変数（例: `x` や `signal`）をノートブック側で用意します。
3. Copilot Chat で `@wandas` に解析を依頼します。

この拡張は、アクティブなノートブックに **専用セルを1つ** 作成し、そこを都度上書きして Python を実行します（同じカーネルなので既存変数にアクセスできます）。

## 出力

- 数値/要約テキスト: チャットとセル出力を使い分けます（モデルが実行結果を見て反復します）。
- プロット: ノートブックのセル出力として表示されます。

## 開発メモ

- `requirements.txt` に `wandas` が含まれます（devcontainer では `.venv` を用意）。
- コマンド: `wandas.showVersion`, `wandas.createPythonFile`
