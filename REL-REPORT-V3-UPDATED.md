# Revision Requirements for REL-REPORT-FINAL-V3 (Updated)

> This revises `REL-REPORT-FINAL-V3.md`. Every item below was cross-checked against the current
> codebase (`env/weekly_retail_env.py`, `agent/sac_alphalr.py`, `agent/q_learning.py`,
> `agent/sarsa.py`, `pipeline.py`, `config.py`) as of 2026-07-17. Items marked **[CONFIRMED IN CODE]**
> are not hypothetical — they describe an actual gap found by reading the source. Items marked
> **[NEW]** were added because they were missing from V3 but matter for correctness or reproducibility.
> Items marked **[CORRECTED]** fix an inaccuracy in the V3 text.

---

## 1. Overall assessment

V3 improved clearly over V2:

- The problem is now scoped as **single-echelon weekly retail replenishment**, implemented in `WeeklyRetailEnv`.
- State is **26-dimensional**: `inventory(5) + forecast(5) + purchase_cost(5) + storage_cost(5) + shortage_penalty(5) + day(1)` — confirmed at `env/weekly_retail_env.py:58-65`.
- Action is **5-dimensional** (order quantity per product).
- Each episode runs **52 weekly decisions**.
- Reward is weekly accounting profit (`revenue - procurement - storage - shortage`) scaled by `REWARD_SCALE` — confirmed at `env/weekly_retail_env.py:133-135`.
- Business metrics (revenue, profit, stockout, service level, floor-space utilization) are reported.
- Discussion/Limitations are appropriately cautious and do not overclaim.

To make V3 strong enough for a research paper or a high-quality final report, the priority order below should be followed. **Priorities 1, 6, and 7 are the most urgent because they are confirmed methodological bugs, not just missing analysis.**

---

# 2. Revision items, in priority order

## Priority 1 — Separate validation seed from test seed **[CONFIRMED IN CODE]**

`pipeline.py:68` and `pipeline.py:136` both instantiate `WeeklyRetailEnv(HolidayDemandGenerator(seed=EVALUATION_SEED))` — the *same* `EVALUATION_SEED` constant is used both for evaluating checkpoints during training and for producing the final reported numbers. This is a real single-seed leak, not a theoretical risk: the checkpoint selection and the final report are computed on identical demand realizations.

### Required change

```text
Training seeds: 0-4
Validation seeds: 100-104
Test seeds: 200-209
```

### Proposed procedure

```text
Train on training seeds
        |
Evaluate periodically on validation seeds
        |
Select best checkpoint by validation performance
        |
Final evaluation on test seeds never used before
```

### Required output

- The list of training seeds.
- The list of seeds used to select the checkpoint.
- The list of seeds used for the final test.
- Confirmation that no test seed was used during model selection.

---

## Priority 2 — Run multiple random seeds

Current results come from a single seed and are not sufficient to show that the ranking between algorithms is stable.

Sources of randomness in the current codebase:

- Demand noise (`HolidayDemandGenerator`).
- Random baseline action sampling.
- Epsilon-greedy exploration in `QLearningAgent` (`agent/q_learning.py:56`) and SARSA.
- Neural network initialization in SAC (`Actor`/`Critic`).
- Action sampling in `Actor.sample()`.
- Replay Buffer sampling (`agent/replay_buffer.py`).

### Minimum requirement

```text
5 training seeds x 10 evaluation demand seeds
```

### Metrics to report

- Mean.
- Standard deviation.
- 95% confidence interval.
- Median, if the result distribution is skewed.
- Worst-case and best-case, if relevant.

### Suggested statistical tests

- Paired t-test if the data is approximately normal.
- Wilcoxon signed-rank test if normality should not be assumed.
- Report an effect size such as Cohen's d where appropriate.

---

## Priority 3 — Rename SAC-AlphaLR

Confirmed in `agent/sac_alphalr.py:28-32`: `actor_optimizer`, `critic_optimizer`, and `alpha_optimizer` all use a fixed `lr=3e-4` with no scheduler. The only adaptive component is `log_alpha`, updated via `alpha_loss` (line 84) based on `target_entropy = -action_dim`. There is no adaptive learning rate anywhere in the class. The name `SAC-AlphaLR` therefore misleads readers into thinking both alpha *and* the learning rate are adapted.

### Recommended name

```text
SAC-AutoAlpha
```

Full name:

```text
Soft Actor-Critic with Automatic Entropy-Temperature Tuning
```

Alternative:

```text
Adaptive-Temperature SAC
```

### Handling the legacy checkpoint/class name

Keep the file and class name `SACAlphaLR` in source to avoid breaking existing checkpoints, but state explicitly in the paper:

> The legacy checkpoint and code class retain the name SAC-AlphaLR. However, the evaluated implementation uses a fixed learning rate and automatic entropy-temperature tuning only; therefore, the method is referred to as SAC-AutoAlpha in this paper.

### Locations that must be updated

- Title (if applicable).
- Abstract — note `sn-article.tex:83` currently reads "a Soft Actor-Critic variant with adaptive entropy temperature, denoted SAC-AlphaLR"; this sentence must change to SAC-AutoAlpha.
- Keywords.
- Methodology.
- Experimental setup.
- Result tables and figures.
- Discussion and conclusion.
- Source comments and README, where feasible.

---

## Priority 4 — Add SAC Fixed-Alpha as an ablation

The current report only shows that SAC with adaptive alpha beats Random, Q-learning, and SARSA. It does not show that automatic alpha tuning is better than a well-chosen fixed alpha — this is a missing ablation, since `target_entropy = -action_dim` (a common default) is used without justification against alternatives.

### Models to add

```text
SAC Fixed alpha = 0.05
SAC Fixed alpha = 0.10
SAC Fixed alpha = 0.20
SAC Fixed alpha = 0.50
SAC AutoAlpha
```

Minimum if resources are limited:

```text
SAC Fixed alpha = 0.1
SAC Fixed alpha = 0.2
SAC AutoAlpha
```

### Metrics to compare

- Total cost.
- Revenue.
- Estimated profit.
- Service level.
- Stockout units.
- Convergence speed.
- Variance across seeds.
- Final alpha value.
- Entropy per episode.

---

## Priority 5 — Archive full training artifacts for reproducibility

### Required artifacts

```text
Git commit hash
Python version
PyTorch version
Gym/Gymnasium version
Operating system
CPU/GPU
Training command
Training seed
Evaluation seeds
Config snapshot
Training log
Checkpoint file
Checkpoint SHA256 hash
Training duration
Date and time of training
```

### Proposed directory structure

```text
experiments/
|-- sac_autoalpha_seed_42/
    |-- config.json
    |-- command.txt
    |-- environment.txt
    |-- train.log
    |-- metrics.csv
    |-- actor.pth
    |-- critic.pth
    |-- checkpoint.sha256
    |-- summary.json
```

---

## Priority 6 — Clarify Q-learning / SARSA reward assignment **[CONFIRMED IN CODE — this is the real answer, not an open question]**

V3 poses this as an open question ("does each Q-table get the global reward? is it divided by 5?"). It is not open — `agent/q_learning.py:89` shows the exact formula already in use:

```python
td_target = reward / 5 + (0 if done else self.gamma * best_next)
```

**Confirmed: each of the 5 per-product Q-tables receives the same global weekly profit reward, divided equally by 5.** There is no per-product revenue/cost attribution and no capacity-scaling-aware term. SARSA follows the same pattern (`agent/sarsa.py`).

### Credit-assignment problem this causes

```text
AirPods ordered in excess
-> floor capacity consumed
-> iPhone order gets scaled down by env.step()'s capacity-scaling logic
-> iPhone revenue drops
-> global reward drops
-> the iPhone Q-table is penalized even though the excess order came from AirPods
```

Since all Q-tables receive the identical `reward / 5` signal, the iPhone table cannot distinguish "I made a bad decision" from "AirPods made a bad decision and consumed my capacity."

### Improvement options

#### Option A — Per-product reward

```text
reward_i = revenue_i - procurement_i - storage_i - shortage_i
```

Then add a shared capacity penalty term:

```text
reward_i = individual_reward_i + shared_capacity_penalty / 5
```

#### Option B — Keep the global `reward / 5` split

If kept, the paper must state explicitly that this is a heuristic factorization and discuss the credit-assignment limitation demonstrated above — this is no longer optional given the confirmed code behavior.

---

## Priority 7 — Distinguish requested action from executed action **[CONFIRMED IN CODE — real gap, not hypothetical]**

`env/weekly_retail_env.py:84-91` shows the order is rounded/capped first, then scaled down if it exceeds remaining floor-space capacity:

```python
order_qty = _cap(np.round(order_qty).astype(np.int32), MAX_ORDER)
...
if current_m2 + order_m2 > RETAIL_STORE_AREA_M2:
    scale = max(RETAIL_STORE_AREA_M2 - current_m2, 0) / max(order_m2, 1)
    order_qty = np.floor(order_qty * scale).astype(np.int32)
```

The pre-scaling value is **never stored** — `info` (lines 139-154) only exposes the final, post-scaling `order_qty`. There is no `requested_action`, `executed_action`, or `capacity_scale` field in `info` today.

This matters because whatever the training loop stores in the Replay Buffer as "the action taken" for this transition determines what the Critic learns to associate with the observed reward. If the policy's raw output (pre-scaling) is stored instead of the executed, scaled action, the Critic learns an incorrect state-action-reward relationship whenever scaling occurs.

### Required fix

`env.step()` must return, at minimum:

```python
info["requested_action"]   # the policy's raw output, pre-scaling
info["executed_action"]    # order_qty after capacity scaling (currently the only one exposed)
info["capacity_scale"]     # the scale factor applied, 1.0 if no scaling occurred
```

### What the Replay Buffer should store

```python
executed_action
```

i.e., the action actually applied to the environment, not the policy's raw (potentially infeasible) output.

---

## Priority 8 — State clearly that Q-learning and SARSA are factorized baselines

The shared floor-space constraint makes the five products' decisions interdependent. Yet Q-learning and SARSA (confirmed in `agent/q_learning.py:11-31`):

- Use a separate Q-table per product.
- Observe only a discretized inventory bucket (`N_INV=14`) and forecast bucket (`N_FC=10`) per product — no cross-product information.
- Select a discrete action per product independently.

SAC, by contrast:

- Observes the full 26-dimensional state.
- Selects a joint 5-dimensional continuous action.
- Can, in principle, coordinate capacity allocation across products.

### Correct framing

> All policies interact with the same business environment, but the tabular baselines use a reduced and factorized state-action representation, whereas SAC uses the full continuous state and joint action vector.

### Conclusion must be scoped

> SAC achieved the best performance among the evaluated methods under the reported discretization, training budget, and seed configuration.

---

## Priority 9 — Add a classical inventory-management baseline

Random is a weak baseline and is not sufficient to show RL beats a reasonable inventory policy.

### Proposed baselines

#### Forecast base-stock

```text
target_inventory_i = forecast_7day_i + safety_stock_i
order_i = max(0, target_inventory_i - current_inventory_i)
```

#### (s, S) policy

```text
if inventory_i < s_i:
    order_i = S_i - inventory_i
else:
    order_i = 0
```

### Parameter selection

- Grid search on validation seeds.
- Do not tune directly on test seeds.
- Safety stock may be chosen from the demand standard deviation.

---

## Priority 10 — Add learning curves

### Required figures

#### Figure 1 — Evaluation profit vs. episode

- X-axis: training episode.
- Y-axis: average validation profit.
- Lines: Q-learning, SARSA, SAC Fixed Alpha, SAC AutoAlpha.

#### Figure 2 — Alpha and entropy vs. episode

- Learned alpha.
- Policy entropy.
- Target entropy (constant, `-action_dim = -5`).

### Additional recommended figures

- Episode return.
- Total cost.
- Service level.
- Stockout units.
- Actor loss.
- Critic loss.
- Average Q-value.

---

## Priority 11 — Add floor-space utilization to the state, or explain its absence

The floor-space constraint is central to the problem, yet the 26-dim state (`env/weekly_retail_env.py:58-65`) has no direct `remaining floor space` scalar — only per-product inventory levels, from which floor usage can in principle be inferred since `RETAIL_FOOTPRINT_M2` is fixed per product.

### Improvement option

Add:

```text
occupied_area_ratio = occupied_area / total_area
```

or

```text
remaining_area_ratio = remaining_area / total_area
```

Adding one scalar increases state dimensionality from 26 to 27.

### If retraining is not desired

State explicitly that per-product footprint is fixed (`RETAIL_FOOTPRINT_M2`), so the Actor can learn the inventory-vector-to-floor-space relationship implicitly, and that this is a design tradeoff rather than an oversight.

---

## Priority 12 — Run a state ablation

Of the 26 state dimensions, 15 are static within an episode:

- Purchase cost: 5 (constant, only varies if `PURCHASE_COST` in `config.py` changes).
- Storage cost: 5 (`RETAIL_STORAGE_COST_DAY`, constant).
- Shortage penalty: 5 (`SHORTAGE_PENALTY_UNIT`, constant).

### State variants to compare

#### Full state

```text
26 dimensions
```

#### Dynamic-only state

```text
Inventory: 5
Forecast: 5
Day: 1
Floor utilization: 1
```

### Purpose

- Test whether the static cost features actually help learning.
- Reduce complexity if they are not needed.
- Give the state design empirical justification.

---

## Priority 13 — Add a Deep RL baseline in the same class as SAC

### Preferred baseline

```text
TD3
```

Rationale:

- Continuous action space.
- Off-policy.
- Twin critics.
- No entropy term, unlike SAC — isolates the effect of the entropy-regularized objective itself.

### Additional baselines

- DDPG.
- PPO.

### Proposed comparison set

```text
Random
Forecast Base-Stock
Q-learning
SARSA
TD3
SAC Fixed Alpha
SAC AutoAlpha
```

---

## Priority 14 — Scope the Abstract to the actual evaluated results

Since results currently come from a single seed (`EVALUATION_SEED`, confirmed identical across training-eval and final report — see Priority 1), the Abstract must state this scope explicitly:

> In the evaluated seed-42 scenario...

The current abstract text in `sn-article.tex:83` ("SAC-AlphaLR achieves the lowest total annual cost... 8.4% reduction... 46% reduction") reports point estimates with no uncertainty — this must be flagged as single-seed until Priority 2 is done.

Once multiple seeds are run, replace with:

> Across multiple training and evaluation seeds, SAC-AutoAlpha achieved...

and report `mean +/- standard deviation`.

---

## Priority 15 — Complete author metadata

The paper still needs:

- Correct affiliation.
- Corresponding author.
- Author contributions.
- Funding statement.
- Conflict of interest statement.
- Code availability.
- Data availability.
- Ethics statement, if the template requires it.

### Note on Data Availability for this project

This project uses no external or human-subject dataset — demand is generated synthetically by `HolidayDemandGenerator` (`env/advanced_demand_generator.py`), and costs/prices are hand-configured in `config.py`. The correct framing is:

> No external dataset was used. Demand trajectories were generated synthetically by a parameterized demand generator (day-of-week effects, seasonal variation, and calibrated holiday spikes); the generator, its parameters, and the random seeds used to produce all reported results are released with the code so results can be regenerated exactly.

This should replace any implication that a real-world dataset exists — the "data" here is the generator plus seeds, not a corpus.

---

## Priority 16 — Compare runtime fairly

Do not compare Q-learning/SARSA training + evaluation time against SAC checkpoint-loading + evaluation time — these measure different things.

### Separate the two runtime types

#### Training time

| Algorithm | Training time | Hardware | Episodes |
|---|---:|---|---:|
| Q-learning | ... | ... | 200 |
| SARSA | ... | ... | 200 |
| TD3 | ... | ... | 200 |
| SAC | ... | ... | 200 |

#### Inference time

| Algorithm | 52-week rollout time |
|---|---:|
| Random | ... |
| Q-learning | ... |
| SARSA | ... |
| SAC | ... |

---

# 3. Metrics to report

## 3.1 Business metrics

- Total cost.
- Revenue.
- Estimated profit.
- Procurement cost.
- Storage cost.
- Shortage cost.
- Units sold.
- Stockout units.
- Service level.
- Stockout weeks.
- Average floor utilization.
- Peak floor utilization.
- Number of scaled actions (**[NEW]** — directly measurable once Priority 7's `capacity_scale` field exists; counts how often the policy requests an infeasible order).
- Average capacity scale factor.
- Total order quantity.

## 3.2 Machine-learning metrics

- Episode return.
- Evaluation profit.
- Convergence speed.
- Sample efficiency.
- Standard deviation across seeds.
- Worst-case performance.
- Actor loss.
- Critic loss.
- Learned alpha.
- Policy entropy.
- Training time.
- Inference time.

---

# 4. Priority summary table

| # | Task | Level | Required output | Status |
|---:|---|---|---|---|
| 1 | Separate validation/test seeds | Required | Distinct seed sets for selection vs. reporting | Confirmed bug |
| 2 | Run multiple seeds | Required | Mean +/- std and confidence interval | Open |
| 3 | Rename SAC-AlphaLR | Required | SAC-AutoAlpha or equivalent | Confirmed naming issue |
| 4 | Add SAC Fixed Alpha | Very high | Adaptive-alpha ablation | Open |
| 5 | Archive training artifacts | Very high | Command, log, config, hash, checkpoint | Open |
| 6 | Clarify Q-learning/SARSA reward | Very high | Documented as `reward / 5` global split | Confirmed in code |
| 7 | Track requested vs. executed action | Very high | `info` exposes both + Replay Buffer stores executed | Confirmed gap |
| 8 | State tabular baselines are factorized | High | Comparison scope correctly described | Open |
| 9 | Add base-stock or (s, S) baseline | High | Classical inventory baseline | Open |
| 10 | Add learning curves | High | Profit, return, alpha, entropy vs. episode | Open |
| 11 | Add floor utilization to state, or explain | Medium-high | Clear capacity representation | Open |
| 12 | State ablation | Medium | Evaluate static cost features' contribution | Open |
| 13 | Add TD3/DDPG/PPO | Medium | Continuous-control baseline | Open |
| 14 | Scope the Abstract | Medium | Conclusions limited to seed/scenario until Priority 2 | Open |
| 15 | Complete author metadata | Required before submission | Affiliation, contributions, data/code availability | Open |
| 16 | Fair runtime comparison | Low-medium | Training and inference measured separately | Open |

---

# 5. Proposed execution plan

## Phase 1 — Fix methodological issues (no new experiments needed)

1. Rename the algorithm in text (keep code/checkpoint names).
2. Separate validation/test seeds in `pipeline.py`.
3. Add `requested_action` / `executed_action` / `capacity_scale` to `env.step()`'s `info` dict; update Replay Buffer usage to store the executed action.
4. Document the confirmed `reward / 5` credit-assignment behavior in Q-learning/SARSA and discuss its limitation in the paper.
5. Set up the artifact-saving directory structure (Priority 5).

## Phase 2 — Re-run experiments

1. Train across multiple seeds.
2. Add SAC Fixed Alpha runs.
3. Add the forecast base-stock baseline.
4. Add TD3 if resources allow.
5. Evaluate on independent test seeds.

## Phase 3 — Regenerate results

1. Mean +/- std tables.
2. Learning curves.
3. Alpha/entropy curves.
4. Business metric charts.
5. Statistical tests.

## Phase 4 — Update the paper

1. Abstract.
2. Methodology.
3. Experimental Setup.
4. Results.
5. Discussion.
6. Limitations.
7. Conclusion.
8. Author metadata.
9. Reproducibility section.

---

# 6. Definition of "done"

## Sufficient for a course report

- Correct algorithm name.
- Clear explanation of tabular baseline limitations.
- Full command and config recorded.
- Metadata fixed.
- Results and figures do not contradict each other.
- Requested vs. executed action distinction documented, even if not yet fixed in the Replay Buffer.

## Sufficient for a stronger research paper

- Multiple seeds.
- Validation/test separation.
- Confidence intervals.
- SAC Fixed Alpha ablation.
- Classical inventory baseline.
- Deep RL baseline.
- Learning curves.
- Reproducible checkpoint.
- Statistical comparison.
- Replay Buffer confirmed to store executed (not requested) actions.
