# Win-Probability Model — Model Card

## MLB Performance Intelligence Platform

| Item | Value |
|---|---|
| Question | What is the probability that the home team wins this game? |
| Notebooks | `src/gold/05_Gold_Game_Features` (features), `src/ml/01_Win_Probability_Model` (training and scoring) |
| Output | `gold.game_predictions.home_win_prob` for completed (back-test) and upcoming games |
| Selected model | Logistic regression on standardized features |
| Training data | Regular season and postseason 2024–2025 (4,949 games) |
| Test data | Season 2026 (2,465 games), never seen in training |

## Features (home minus away, known before first pitch)

| Feature | Meaning | Standardized coefficient |
|---|---|---|
| `d_run_diff` | Run differential per game to date | +0.179 |
| `d_win_pct` | Win % to date | +0.143 |
| `d_split` | Home record of the home team vs road record of the visitor | −0.119 |
| `d_starter_kbb` | Starting pitcher strikeouts − walks % | +0.097 |
| `d_starter_fip` | Starting pitcher FIP | +0.041 |
| `park_factor` | Runs per game at the venue vs league, previous seasons only | −0.040 |
| `d_last10` | Last-10 win % | +0.021 |
| `d_bullpen_fatigue` | Outs thrown by the bullpen in the previous 3 days | −0.016 |
| `d_rest` | Days since the previous game (capped at 5) | +0.015 |
| `d_bullpen_era` | Bullpen ERA to date | −0.004 |
| `is_postseason` | Postseason game | −0.004 |

Season-to-date values are regressed toward the previous season early in the year (20 games of prior weight), so
April numbers are not driven by a handful of games.

## Results on the test season (2026)

| Model | Accuracy | Log loss | Brier | ROC AUC |
|---|---|---|---|---|
| **Logistic regression (selected)** | **56.0 %** | **0.682** | **0.244** | 0.576 |
| Gradient boosting | 53.9 % | 0.692 | 0.249 | 0.547 |
| Baseline: always the home team | 52.9 % | 0.692 | 0.249 | 0.500 |
| Baseline: better record | 54.1 % | 0.697 | 0.252 | 0.540 |

Selection uses the lowest log loss (honest probabilities), not accuracy. Gradient boosting fits the training
seasons better (64.2 %) but generalizes worse: it overfits.

## Calibration (2026)

| Favourite's predicted probability | Games | Predicted | Actual |
|---|---|---|---|
| 50–55 % | 1,102 | 52.4 % | 52.2 % |
| 55–60 % | 845 | 57.4 % | 55.6 % |
| 60–65 % | 374 | 62.0 % | 63.9 % |
| 65–70 % | 126 | 66.9 % | 66.7 % |
| 70 %+ | 18 | 71.7 % | 72.2 % |

## Limits

- Baseball is close to a coin flip game by game; good public models reach 55–60 %. The value is in calibrated
  probabilities, not certainty.
- Line-ups, injuries and weather are not in the features.
- The platform shows the probabilities for analysis; it is not betting advice.
