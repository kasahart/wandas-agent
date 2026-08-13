# wandas-analyst: Notebook Structure Guide

## Contents

1. Notebook contract
2. Cell sequence
3. Cell JSON
4. Validation checklist

## Notebook contract

- 目的と decision を先頭で固定する。
- Source loading、calibration、diagnostics を分離する。
- 1 code cell につき1つの evidence claim を扱う。
- 全 variable を一度だけ定義し、hidden execution order に依存しない。
- Wandas で signal transform と plot を行う。
- NumPy は small numerical summary に限る。
- Quantity、unit、reference、caveat を output/Markdown に残す。

## Cell sequence

```text
1. Markdown: title, purpose, decision, hypotheses
2. Markdown: file/condition/calibration table
3. Code: imports and source loading with wd.read()/wd.load()
4. Code: calibration and level-reference inspection
5. Code: diagnostic metrics
6. Markdown: diagnostic interpretation and exclusions
7. For each round:
   a. Markdown: question and motivation
   b. Code: minimal Wandas analysis
   c. Code: compact numerical summary (if separate)
   d. Markdown: observation, interpretation, caveat, next-question decision
8. Code: cross-condition summary table
9. Markdown: hypothesis status, conclusions, uncertainty, next steps
```

## Cell JSON

```json
{
  "cell_type": "code",
  "id": "load-data",
  "metadata": {},
  "execution_count": null,
  "outputs": [],
  "source": [
    "import numpy as np\n",
    "import wandas as wd\n",
    "\n",
    "signal = wd.read('recording.wav')\n"
  ]
}
```

Notebook root:

```json
{
  "nbformat": 4,
  "nbformat_minor": 5,
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python",
      "version": "3.10+"
    }
  },
  "cells": []
}
```

`source` は string または string array。`id` は notebook 内で unique にする。生成時の `outputs` は空、`execution_count` は `null`。

## Recommended setup cells

```python
import numpy as np
import wandas as wd

signal = wd.read("recording.wav")
print(signal.sampling_rate, signal.duration, signal.labels)
print([channel.level_reference.label for channel in signal.channels])
```

Calibration が既知の場合:

```python
signal = signal.with_calibration(
    {0: wd.ChannelCalibration(factor=0.42, unit="Pa")}
)
```

## Validation checklist

- 全 placeholder を置換したか。
- Source path と condition map が一致するか。
- `wd.read()` に存在しない `normalize` 引数を渡していないか。
- Frame 同士を `.concat_frame()` で結合しているか。
- Mono property に不要な `[0]` を付けていないか。
- Welch を PSD と呼んでいないか。
- `get_frame_at()` を time index として使っているか。
- Level claim に calibration/reference label があるか。
- dB の算術平均を Leq と呼んでいないか。
- Plot の直後に observation と caveat があるか。
- Cell を上から順に実行できるか。
