# wandas-analyst: Focused Agent Protocol

## Roles

| Role | Input | Output | Frequency |
|---|---|---|---|
| Diagnostician | files, conditions, intended quantities | quality/calibration report, viable analyses | once at start |
| Analysis agent | one question, relevant prior findings, files | runnable code, small evidence, finding/caveat | once per round |
| Synthesis agent | purpose, hypotheses, validated findings | conclusion, uncertainty, action | once at end |

## Context isolation

各 agent へ必要な情報を self-contained に渡す。`先ほどの続き` のような参照を避ける。

Analysis handoff には次だけを含める。

- current question
- file paths and condition meaning
- known calibration
- validated prior observations/caveats
- exact expected output format

Raw arrays、全 notebook、意図した答えは渡さない。

## Diagnostic gates

| Issue | Action |
|---|---|
| unknown calibration | dBFS/generic relative results に限定し、dB SPL と呼ばない |
| possible clipping | original source を保持し、acquisition limitation として報告する。normalize で隠さない |
| DC offset | 仮説に影響するか判断し、必要なら `.remove_dc()` を明示した branch で比較する |
| sampling-rate mismatch | comparison 前に target rate と情報損失を決める |
| length mismatch | `.concat_frame(..., align=...)` の意味を決める。default strict を優先する |
| psychoacoustic extra missing | `wandas[psychoacoustic]` を要求し、private implementation で代用しない |
| insufficient high-frequency content | resampling で情報が増えないことを明記し、psychoacoustic claim を止める |

Clipping check は `channel.level_reference.unit == "dBFS"` のように full-scale domain が確認できる場合だけ行う。Pa や generic sensor unit の `ref` は full-scale limit ではない。`abs(data) >= 0.999` の比率や反復 peak はスクリーニングに過ぎず、WAV subtype/量子化段が不明なら「possible clipping」と報告する。

回転次数は既知 RPM またはタコ同期との照合が必要。FFT/Welch peak、harmonic spacing、cepstrum/cepstrogram だけなら「periodic/rotational candidate」とし、1×・2×のような次数を確定しない。

## Round selection

| Finding | Useful next round |
|---|---|
| broadband amplitude difference | calibrated level or N-octave comparison |
| narrow peaks | FFT/Welch amplitude; STFT for timing |
| periodic spectral spacing | cepstrum/cepstrogram |
| time-local event | STFT + nearest `.times` index |
| input-output relationship | typed coherence/transfer selected pair |
| perceived quality difference | calibrated psychoacoustic metrics |

Do not schedule every analysis category by default.

## Convergence

Continue only when the next result could materially change the decision. Stop when:

- purpose is answered with evidence;
- remaining uncertainty comes from missing calibration/data rather than another transform;
- next question is merely confirmatory;
- seven rounds are complete.

## Synthesis handoff

Pass:

- purpose and decision;
- hypotheses;
- each round's question;
- small numerical summary with unit;
- observation, interpretation, caveat;
- excluded/failed analyses and why.

Do not pass giant arrays. Do not hide unresolved calibration or alignment limits.
