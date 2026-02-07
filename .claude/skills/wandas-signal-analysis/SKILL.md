# wandas-signal-analysis

**説明:**  
wandasライブラリを使用して時系列信号データの解析を行います。WAV/CSVの読み込み、フィルタリング、FFT/STFT解析、可視化をサポートします。「信号処理」「スペクトログラム」「ノイズ除去」等のタスクで使用してください。

---

## Skill Overview

このスキルは、Pythonの信号処理ライブラリ **wandas** を使用して、効率的な信号解析コードを生成・実行するためのものです。  
wandas は **メソッドチェイン (Method Chaining)** を前提に設計されており、直感的なパイプライン処理が可能です。

---

## Core Philosophy

- **メソッドチェインの推奨:**  
    処理は可能な限りつなげて記述します。

    - Good:  
        ```python
        wd.read_wav("file.wav").high_pass_filter(100).plot()
        ```
    - Bad:  
        ```python
        s = wd.read_wav("...")
        s = s.high_pass_filter(...)
        ```

- **可視化:**  
    チェーンの最後には `.plot()` を呼び出し、結果を即座に確認します。

- **データ構造:**  
    すべての操作は Frame オブジェクト（ChannelFrame, SpectralFrame 等）を返し、これらがメタデータと波形データを保持します。

---

## Documentation Map

タスクに応じて、以下の参照ファイルを読み込んでください：

- **基本操作 (I/O, フィルタ, プロット):**  
    `references/core_api.md` を参照

- **高度な解析 (FFT, STFT, スペクトログラム):**  
    `references/analysis.md` を参照

- **実装パターン・コード例:**  
    `examples/workflows.md` を参照

---

## Utility Scripts

未知のデータファイル（WAV/CSV）が与えられた場合、まずは以下のスクリプトを実行してデータの概要（サンプリングレート、長さ、チャンネル数）を確認することを推奨します。


