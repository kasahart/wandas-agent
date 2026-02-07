import sys
import os
# wandasがインストールされていない環境でも動作するようにtry-exceptで囲むか、
# エージェント実行環境にはインストール済みであることを前提とする。
try:
    import wandas as wd
except ImportError:
    print("Error: 'wandas' library is not installed. Please install it via pip.")
    sys.exit(1)


def main():
    """
    WAVまたはCSVファイルを読み込み、基本情報を表示するスクリプト。
    Agentがデータの中身を知るための「目」として機能します。

    Usage: python basic_loading.py <file_path>
    """
    if len(sys.argv) < 2:
        print("Usage: python basic_loading.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    try:
        # ファイル拡張子に基づいて読み込みメソッドを分岐
        ext = file_path.lower()
        if ext.endswith('.wav'):
            print(f"Loading WAV file: {file_path}...")
            sig = wd.read_wav(file_path)
        elif ext.endswith('.csv'):
            print(f"Loading CSV file: {file_path}...")
            # CSVの場合はTime列の自動推定を試みるのが一般的だが、
            # ここでは一般的な 'Time' をデフォルトとしつつ、失敗したら警告する簡易実装
            try:
                sig = wd.read_csv(file_path, time_column="Time")
            except Exception:
                print(
                    "Warning: Could not automatically detect 'Time' column. Loading without time index.")
                sig = wd.read_csv(file_path)
        else:
            print(
                f"Error: Unsupported file format '{file_path}'. Supported: .wav, .csv")
            sys.exit(1)

        # 読み込み成功メッセージとオブジェクト情報の表示
        print("-" * 30)
        print(f"Successfully loaded: {os.path.basename(file_path)}")
        print("-" * 30)

        # エージェントがコンテキストとして理解すべきメタデータを出力
        # wandasのFrameオブジェクトが持つ属性を表示
        print(f"Object Type: {type(sig).__name__}")
        sig.info()
        print("-" * 30)
        print(
            "Suggestion: Use .describe() for visualization and listening, .plot() for simple visualization, or .info() for statistical details.")

    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
