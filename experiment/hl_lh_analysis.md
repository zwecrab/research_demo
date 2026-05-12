# HL / LH Session Analysis

**Source:** pilot 2 + pilot 3 + pilot 4 (n=28 sessions total; HL=11, LH=11, near-balanced excluded=6).

**HL** = high-severity patient speaks first (alpha position if sev_diff > 0, beta position if sev_diff < 0).  
**LH** = low-severity patient speaks first (opposite mapping).  
**sev_diff** = overall_A − overall_B from LLM rater consensus (positive = A more severe).  
**FAS_highsev** = FAS re-signed so positive always means therapist adopted the high-severity partner's framing, regardless of A/B label. Core measure for this analysis.  
Near-balanced couples (|sev_diff| < 0.40) excluded: C7, C8.  

---

## Severity Scoring Methodology

**Rater setup.** Each persona is scored independently by three frontier LLMs called via OpenRouter at temperature 0.2: Claude Opus 4 (`anthropic/claude-opus-4`), Gemini 2.5 Pro (`google/gemini-2.5-pro`), and GPT-4o (`openai/gpt-4o`). The consensus (mean across raters) is taken as the final score.

**Five-dimension rubric.** Each rater scores the persona on five continuous 0.0–10.0 dimensions grounded in the HiTOP taxonomy (Kotov et al. 2017):
- *Anxiety*: generalised worry, hypervigilance, rumination, somatic markers.
- *Depression*: anhedonia, hopelessness, withdrawal, loss-of-meaning markers.
- *Trauma*: trauma history or aftermath markers in persona text.
- *Attachment disorganisation*: disorganized or fearful-avoidant attachment; contradictory coping strategies.
- *Escalation tendency*: Four Horsemen markers (contempt, criticism, defensiveness, stonewalling).

**Overall score.** Each rater also assigns a single holistic clinical-severity score (0–10) per persona. This overall score is a separate clinical judgment by the rater, not a formula-derived composite of the five dimensions. The consensus overall is the mean of the three raters' overalls.

**Severity diff.** `severity_diff = overall_A − overall_B`. Positive values indicate Patient A is more clinically severe; negative values indicate Patient B is more severe.

**Inter-rater reliability.** ICC(2,1) absolute agreement = 0.790, exceeding the Koo & Li (2016) "good" threshold of 0.75. Disagreement is elevated on C2, C7, and C9 (per-couple rater range ≥ 1.85).

**HL/LH classification rule.**
- |severity_diff| < 0.40 → session excluded as near-balanced (C7, C8 in this dataset).
- severity_diff > 0 (A more severe): alpha → HL; beta → LH.
- severity_diff < 0 (B more severe): alpha → LH; beta → HL.

---

### Table 1 — HL sessions: high-severity patient speaks first (n=11)

| # | Couple | High-sev | Low-sev | sev_diff | Bids | Pos | FAS | FAS-vol | FAS_highsev | FASv_highsev | BRD | CAS | wA | wB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | C3 | David (+0.99) | James | +0.99 | neu+neu | alpha | +0.267 | +0.259 | **+0.267** | +0.259 | +0.714 | +1 | 280 | 264 |
| 2 | C4 | Sofia (+2.93) | Kenji | +2.93 | neu+neu | alpha | +0.133 | +0.187 | **+0.133** | +0.187 | +0.500 | -2 | 255 | 279 |
| 3 | C9 | Naomi (-0.83) | Lena | -0.83 | neu+neu | beta | -0.067 | +0.007 | **+0.067** | -0.007 | +0.467 | -2 | 257 | 304 |
| 4 | C2 | Rajan (-2.83) | Eszter | -2.83 | agg+agg | beta | -0.400 | -0.528 | **+0.400** | +0.528 | +0.600 | +0 | 364 | 337 |
| 5 | C4 | Sofia (+2.93) | Kenji | +2.93 | neu+neu | alpha | +0.200 | +0.507 | **+0.200** | +0.507 | +0.222 | +1 | 348 | 355 |
| 6 | C6 | Maya (+3.33) | Devon | +3.33 | agg+agg | alpha | -0.200 | -0.180 | **-0.200** | -0.180 | +0.667 | -1 | 334 | 387 |
| 7 | C9 | Naomi (-0.83) | Lena | -0.83 | neu+neu | beta | +0.100 | +1.000 | **-0.100** | -1.000 | +0.333 | +0 | 360 | 326 |
| 8 | C2 | Rajan (-2.83) | Eszter | -2.83 | agg+agg | beta | -0.357 | -0.296 | **+0.357** | +0.296 | +0.643 | -2 | 218 | 316 |
| 9 | C2 | Rajan (-2.83) | Eszter | -2.83 | agg+agg | beta | -0.300 | -0.452 | **+0.300** | +0.452 | +0.333 | -1 | 355 | 335 |
| 10 | C6 | Maya (+3.33) | Devon | +3.33 | agg+agg | alpha | +0.231 | +0.160 | **+0.231** | +0.160 | +0.385 | -1 | 333 | 230 |
| 11 | C6 | Maya (+3.33) | Devon | +3.33 | agg+agg | alpha | +0 | +0.011 | **+0** | +0.011 | -0.445 | +0 | 347 | 355 |
| **Mean** | — | — | — | — | — | — | **-0.036** | +0.061 | **+0.150** | +0.110 | +0.402 | -0.636 | 314 | 317 |

---

### Table 2 — LH sessions: low-severity patient speaks first (n=11)

| # | Couple | High-sev | Low-sev | sev_diff | Bids | Pos | FAS | FAS-vol | FAS_highsev | FASv_highsev | BRD | CAS | wA | wB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | C3 | David (+0.99) | James | +0.99 | neu+neu | beta | +0.133 | +0.087 | **+0.133** | +0.087 | -0.133 | -2 | 291 | 260 |
| 2 | C4 | Sofia (+2.93) | Kenji | +2.93 | neu+neu | beta | +0.214 | +0.142 | **+0.214** | +0.142 | -0.308 | +2 | 303 | 252 |
| 3 | C9 | Naomi (-0.83) | Lena | -0.83 | neu+neu | alpha | +0 | +0.036 | **+0** | -0.036 | +0.143 | +0 | 270 | 290 |
| 4 | C2 | Rajan (-2.83) | Eszter | -2.83 | agg+agg | alpha | -0.400 | -0.543 | **+0.400** | +0.543 | +1.000 | -2 | 361 | 321 |
| 5 | C4 | Sofia (+2.93) | Kenji | +2.93 | neu+neu | beta | +0.600 | +1.000 | **+0.600** | +1.000 | +0.667 | -2 | 367 | 354 |
| 6 | C6 | Maya (+3.33) | Devon | +3.33 | agg+agg | beta | +0.300 | +0.636 | **+0.300** | +0.636 | +0.667 | -2 | 312 | 351 |
| 7 | C9 | Naomi (-0.83) | Lena | -0.83 | neu+neu | alpha | +0.100 | +0.213 | **-0.100** | -0.213 | +0 | -1 | 372 | 382 |
| 8 | C2 | Rajan (-2.83) | Eszter | -2.83 | agg+agg | alpha | -0.083 | -0.158 | **+0.083** | +0.158 | +2.364 | -8 | 305 | 277 |
| 9 | C2 | Rajan (-2.83) | Eszter | -2.83 | agg+agg | alpha | -0.100 | -0.111 | **+0.100** | +0.111 | +0.555 | +1 | 347 | 347 |
| 10 | C6 | Maya (+3.33) | Devon | +3.33 | agg+agg | beta | +0.308 | +0.303 | **+0.308** | +0.303 | +1.167 | -5 | 262 | 245 |
| 11 | C6 | Maya (+3.33) | Devon | +3.33 | agg+agg | beta | +0.100 | +0.139 | **+0.100** | +0.139 | +1.200 | -6 | 342 | 362 |
| **Mean** | — | — | — | — | — | — | **+0.107** | +0.159 | **+0.194** | +0.261 | +0.666 | -2.273 | 321 | 313 |

---

## Interpretation

| Condition | n | Mean FAS (raw) | Mean FAS_highsev | Interpretation |
|---|---:|---:|---:|---|
| HL (high-sev first) | 11 | -0.036 | **+0.150** | Therapist adopted high-sev frame |
| LH (low-sev first) | 11 | +0.107 | **+0.194** | Therapist still adopted high-sev frame despite speaking second |


**Key question:** If FAS_highsev > 0 in both HL and LH conditions, the therapist favors the high-severity patient *regardless* of speaking order; severity dominates position. If FAS_highsev > 0 in HL but ≈ 0 (or negative) in LH, position moderates severity.

**BRD sign convention.** BRD = mean_depth_B − mean_depth_A. BRD > 0 indicates Patient B received deeper therapist responses; BRD < 0 indicates Patient A received deeper responses.
