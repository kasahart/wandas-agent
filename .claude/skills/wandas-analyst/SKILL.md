---
name: wandas-analyst
description: Use when investigating audio, vibration, or sensor recordings end-to-end with Wandas 0.7.2; comparing measurement conditions; diagnosing anomalies; evaluating calibrated levels or sound quality; adapting the next analysis to prior findings; or generating an evidence-backed Jupyter Notebook report.
---

# wandas-analyst: Adaptive Signal Investigation

<SUBAGENT-STOP>
サブエージェントとして呼び出された場合は、このスキルのオーケストレーションを再帰的に開始せず、呼び出し元の問いだけを処理する。
</SUBAGENT-STOP>

## Mandatory Rules

1. **Wandas-first**: 読み込み、filter、spectral transform、level、可視化は Wandas を使う。NumPy は materialize 後の小さな統計集約に限る。
2. **Purpose-first**: 「何を判断するための解析か」を北極星として最初に明文化する。
3. **Diagnose before expanding**: 最初に signal quality、単位、校正、sampling rate、duration、channel を確認する。
4. **Quantity-correct**: linear RMS、reference-relative level、dBFS、dB SPL、psychoacoustic metric を区別する。dB を算術平均して Leq と呼ばない。
5. **Adaptive rounds**: 各 round は1つの問いに答え、発見が次 round を正当化するときだけ続ける。
6. **Evidence separation**: synthesis には目的、仮説、検証済み numerical summary、findings、caveat を渡し、巨大な raw array を渡さない。
7. **Reproducible Notebook**: `.ipynb` は実行順が明確な JSON artifact として生成し、placeholder を残さない。

## Investigation Protocol

```text
Purpose + decision
  -> data/condition map
  -> initial hypotheses
  -> diagnostic pass
  -> focused analysis round
  -> finding + caveat + next-question decision
  -> repeat only while useful
  -> synthesis
  -> reproducible notebook
```

| Step | Required output | Stop condition |
|---|---|---|
| 1. Design | purpose, decision, files, conditions, hypotheses | comparison axis is explicit |
| 2. Diagnose | metadata, calibration/level reference, signal-quality issues | invalid data is flagged before interpretation |
| 3. Analyze | one question, minimal code, numerical evidence, plot | the round answers its question |
| 4. Converge | support/refute/extend each hypothesis | purpose can be answered or 7 rounds reached |
| 5. Synthesize | conclusions, evidence, uncertainty, next steps | every claim points to evidence |
| 6. Package | rerunnable notebook | cells execute in order without hidden state |

## Diagnostician Prompt Template

```text
あなたは信号診断エージェントです。Wandas 0.7.2 の公開 API だけを使い、解析前の品質と quantity domain を確認してください。

FILES: {file_paths}
CONDITIONS: {condition_map}

REQUIRED SUB-SKILL: wandas-getting-started

Tasks:
1. `wd.read()` で各 source を読む。WDF だけは `wd.load()` を使う。
2. sampling_rate, duration, n_channels, labels, units, references を記録する。
3. `frame.channels[i].level_reference` の unit/label を記録する。
4. RMS, crest_factor, DC offset を確認する。
5. clipping は dBFS/full-scale domain と判定できる場合だけ評価する。正規化で隠さない。
6. sampling rate/length/calibration が planned comparison に適合するか判断する。

OUTPUT:
---
SIGNAL_QUALITY:
  - file: {filename}
    sampling_rate_hz: {value}
    duration_s: {value}
    channels: {value}
    level_reference: {label}
    rms: {values}
    issues: [clipping | dc_offset | uncalibrated | rate_mismatch | length_mismatch | none]
RECOMMENDED_ANALYSES: [temporal | spectral | level | stft | cepstral | coherence | psycho | comparison]
CAVEATS: [...]
---
```

## Analysis Round Prompt Template

```text
あなたは信号解析エージェントです。1つの問いに最小限の Wandas 解析で答えてください。

QUESTION: {one_question}
ANALYSIS_TYPE: {type}
CONTEXT: {validated prior findings only}
FILES: {file_paths}
CONDITIONS: {condition_map}
CALIBRATION: {known calibration or "unknown"}

REQUIRED SUB-SKILL: wandas-signal-processing
REQUIRED SUB-SKILL: wandas-spectral-analysis
REQUIRED SUB-SKILL: wandas-visualization

Tasks:
1. Signal transforms は Wandas で行う。
2. quantity と unit を明示する。
3. numerical summary と Wandas plot を1つの問いに必要な範囲だけ作る。
4. observation / interpretation / caveat を分ける。
5. 次の問いが結論を変えうる場合だけ提案する。

OUTPUT:
---
CODE: {runnable Python}
NUMERICAL_SUMMARY: {small values/table}
FINDINGS:
  observation: {what the evidence shows}
  interpretation: {what it may mean}
  caveat: {limits}
  next_question: {question or "converged"}
---
```

## Analysis Type Map

| Type | Preferred Wandas API | Quantity check |
|---|---|---|
| `temporal` | `.plot()`, `.rms`, `.rms_trend()` | linear vs reference-relative level |
| `spectral` | `.fft()`, `.welch()`, `.noct_spectrum()` | Welch is averaged peak amplitude, not PSD |
| `level` | `.a_weighting()`, `.rms`, `.sound_level()`, `LevelReference.to_level()` | dBFS / dB SPL / generic dB |
| `stft` | `.stft().plot()` | time index vs seconds |
| `cepstral` | `.cepstrum()`, `.lifter()`, `.to_spectral_envelope()` | quefrency domain |
| `rotational candidate` | `.welch()`, `.stft()`, `.cepstrum()` | RPM/tacho なしでは order を確定しない |
| `coherence` | `.concat_frame()`, `.coherence()`, `.transfer_function()`, `.select_pair()` | output/input role and pair domain |
| `psycho` | loudness / roughness / sharpness methods | calibration, optional dependency, sampling rate |
| `comparison` | same pipeline per condition + compact table | no normalization when amplitude differences matter |

### Full-scale clipping heuristic

```python
import numpy as np
import wandas as wd

raw = wd.read("measurement.wav")
if all(channel.level_reference.unit == "dBFS" for channel in raw.channels):
    absolute = np.abs(np.asarray(raw.data))
    peak = np.max(absolute, axis=-1)
    near_fs_fraction = np.mean(absolute >= 0.999, axis=-1)
    print({"peak_fs": peak, "near_fs_fraction": near_fs_fraction})
```

これは acquisition clipping の確定判定ではなく「疑い」のスクリーニング。WAV subtype、量子化段、float WAV の ±1 超過、連続/反復する同値 peak を考慮する。full-scale domain でない Pa/generic sensor data へ 0.999 threshold を流用しない。

## v0.7.2 Analysis Patterns

### Calibrated overall level and time trend

```python
import numpy as np
import wandas as wd

raw = wd.read("measurement.wav")
pressure = raw.with_calibration(
    {0: wd.ChannelCalibration(factor=0.42, unit="Pa")}
)

weighted = pressure.a_weighting()
reference = weighted.channels[0].level_reference
equivalent_level = reference.to_level(weighted.rms[0])

fast_level = pressure.sound_level("A", "Fast", dB=True)
summary = {
    "equivalent_level": equivalent_level,
    "unit": reference.unit,
    "fast_max": float(np.max(fast_level.data)),
}
fast_level.plot(title="A-weighted Fast level")
```

### Reuse a bounded expensive result

```python
signal = wd.read("bounded-recording.wav")
spectrogram = signal.stft(n_fft=2_048, hop_length=256).astype("complex64").cache()

spectrogram.plot(fmin=20, fmax=8_000)
spectrogram.cepstrum().plot(qmax=0.02)
```

`cache()` は Frame 全量を local memory に同期計算する。bounded recording だけに使う。

### Typed input-output analysis

```python
input_signal = wd.read("input.wav").rename_channels({0: "input"})
output_signal = wd.read("output.wav").rename_channels({0: "output"})
combined = input_signal.concat_frame(output_signal)

coherence = combined.coherence(n_fft=2_048).select_pair(output=1, input=0)
transfer = combined.transfer_function(n_fft=2_048).select_pair(output=1, input=0)

coherence.plot(title="Output/Input coherence")
transfer.plot(view="gain_db", title="Output/Input transfer gain")
```

## Convergence Rules

各 round 後に次を判断する。

1. 発見はどの仮説を支持・否定・拡張したか。
2. 追加 round の結果が最終判断を変える可能性があるか。
3. calibration、sampling、alignment、optional dependency の caveat が結論を制限していないか。
4. 目的へ十分に答えたか。

7 round に達したら synthesis へ移り、未解決事項を明示する。

## Synthesis Prompt Template

```text
PURPOSE: {purpose}
DECISION: {decision}
INITIAL_HYPOTHESES: {hypotheses}
VALIDATED_FINDINGS:
  - round: {n}
    question: {question}
    numerical_evidence: {small summary}
    observation: {observation}
    interpretation: {interpretation}
    caveat: {caveat}

Produce:
1. Hypothesis status: supported / refuted / unresolved, with evidence.
2. Answer-first conclusions with quantity and unit.
3. Uncertainty and data-quality limits.
4. Actionable next steps.
5. Unresolved questions.
```

## Notebook Structure

`templates/analysis_report.ipynb` を複製し、次の順に埋める。

```text
0. Purpose, decision, hypotheses, condition map
1. Imports and reproducible source loading
2. Calibration and diagnostic evidence
3. One section per focused round
4. Compact cross-condition summary
5. Hypothesis status, conclusions, caveats, next steps
```

各 code cell は1つの claim を検証し、plot/output が何を証明するかを直後の Markdown で説明する。cell 間 variable は一度だけ定義する。

## Common Mistakes

| 間違い | 正解 |
|---|---|
| `read_wav(..., normalize=True)` | `wd.read()` に normalize 引数はない。校正解析では正規化しない |
| clipping を見つけたので normalize して続行 | acquisition issue として報告し、元 data を保持する |
| `np.mean(level_db)` を Leq と呼ぶ | weighted linear RMS を channel `LevelReference` で level に変換する |
| 未校正 audio を dB SPL と報告 | `level_reference.label` を確認し、校正がなければ dBFS/generic と報告する |
| Welch を PSD と報告 | Wandas Welch は averaged peak amplitude |
| `.add_channel(other_frame)` | `.concat_frame(other_frame)` |
| `get_frame_at(10)` を 10 秒と解釈 | `.times` から frame index を求める |
| pairwise result を generic spectrum と解釈 | typed property、`select_pair()`、`view=` を使う |
| pairwise result に A-weighting | 未定義で拒否される |
| normalization 後の条件差を改善量とする | 同じ calibrated linear pipeline で比較する |
| `cache()` を無制限データへ使う | memory に収まる bounded result に限る |
| plot の見た目だけから断定 | numerical evidence、unit、caveat を併記する |

## Documentation Map

- [`examples/workflows.md`](examples/workflows.md) — level、異常検知、input-output、条件比較
- [`templates/analysis_report.ipynb`](templates/analysis_report.ipynb) — v0.7.2 Notebook template
- [`references/notebook_structure.md`](references/notebook_structure.md) — reproducible cell structure
- [`references/subagent_protocol.md`](references/subagent_protocol.md) — focused-agent handoff contract

## Required Sub-Skills

**REQUIRED SUB-SKILL:** wandas-getting-started

**REQUIRED SUB-SKILL:** wandas-signal-processing

**REQUIRED SUB-SKILL:** wandas-spectral-analysis
**REQUIRED SUB-SKILL:** wandas-visualization
