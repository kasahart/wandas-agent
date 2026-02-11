# wandas-agent

Copilot Chat で信号解析を行うためのAgent スキルです。

## 使い方

1. `wandas` ライブラリをインストールします。

   ```bash
   pip install wandas
   ```
2. エージェントにタスクを指示します。例えば：
    - 「wandasを使って `data.wav` を読み込んで、20Hz以上の成分をハイパスフィルタで除去し、正規化してプロットしてください。」
    - 「wandasを使って `sensor.csv` を読み込んで、FFT解析を行い、スペクトルを表示してください。」

## 出力

- エージェントは `wandas` のメソッドチェーンを用いて信号処理パイプラインを構築し、解析結果をプロットします。

## 参考資料
- プロンプトと解析結果のサンプル　`notebooks/test.ipynb`