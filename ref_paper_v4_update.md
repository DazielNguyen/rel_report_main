# Reference Update v2 — Residual SAC for Fixed-Capacity Weekly Replenishment

> Purpose: consolidated source material for the paper-writing pass. Synthesizes
> `docs/Agent-explain.md`, `docs/architecture_MDP.md`,
> `docs/PIPELINE_INVENTORY_ECONOMICS_VI.md`, and
> `docs/SERVICE_REPLENISHMENT_PIPELINE_VI.md` as of 2026-07-21. Every claim below
> traces to a code citation in those source docs — this file does not introduce
> new numbers, only reorganizes and adds academic references + figures. Hand this
> to the paper-writing assistant alongside `paper/sn-article.tex` and
> `paper/sn-bibliography.bib`.
>
> Figures referenced below are generated at `paper/figures/*.png` from the
> project's own experiment artifacts (`outputs/service_inventory_frontier.json`,
> `outputs/service_residual_weight_ablation.json`, `outputs/service_eval_results.json`).
> They are placeholders you can drop into the manuscript as-is or re-render with
> your target journal's style.

---

## 1. What changed since the current draft (`REL-REPORT-V3-UPDATED.md`)

The existing report describes a **single delivery per week** system. The
codebase has since moved to a **two-delivery, residual-policy** design. Any
paper text copied from the old report needs these corrections:

| Old claim | Current state | Why it matters for the paper |
|---|---|---|
| One delivery at the start of the week | Two deliveries, day 0 and day 3 | A single delivery cannot physically fit a full week of demand into 25 m²; this is the structural fix, not a reward tweak |
| "SAC-AlphaLR" implies adaptive learning rate | Only entropy temperature (`alpha`) is adaptive; learning rates are fixed `3e-4` | Rename to **SAC-AutoAlpha** / "SAC with automatic entropy-temperature tuning" in all prose |
| Vanilla SAC policy | Policy is `0.90 × baseline(s) + 0.10 × π_θ(s)` — a residual policy with a hand-designed service-coverage prior | Must be named **Residual SAC** with a fixed-area service prior; comparisons to "SAC" in isolation are comparisons to a different algorithm |
| Margin-per-m² bonus active by default | Runtime default `MARGIN_BONUS_WEIGHT = 0.0`; ablation showed positive margin weight is unsafe under the paired guardrail | State clearly: margin bonus exists in code as an ablation lever, not as the shipped objective |
| Single evaluation seed | Terminal evaluation still on seed 42, but selection process now uses disjoint seed roles (see §7) | Needed for internal consistency, not yet a multi-seed confidence interval — flag as future work if not resolved before submission |

---

## 2. Problem formulation (paste-ready for a Methods section)

> The problem is modeled as a weekly Markov Decision Process for single-echelon
> retail replenishment. At each decision epoch *t*, the agent observes a
> 26-dimensional state comprising per-SKU inventory levels, a 7-day demand
> forecast, and per-SKU economic parameters (purchase cost, holding cost,
> shortage penalty), plus a normalized time-of-year index. The agent emits a
> 5-dimensional continuous action representing simultaneous order quantities
> for five SKUs. The environment rounds and clips this action against
> per-SKU maximum order limits and a **hard, non-negotiable storage-area
> constraint of 25 m²**, then delivers the resulting order **twice within the
> week** (day 0 and day 3) before simulating stochastic daily demand over the
> full 7-day horizon. The weekly reward is realized profit (revenue minus
> procurement, holding, and shortage costs) minus reward-shaping penalties for
> tail-risk shortage, per-SKU service gaps, and excess end-of-week inventory.
> The agent's objective is to maximize the expected discounted return with
> `γ = 0.99`.

Formal tuple: `M = (S, A, P, R, γ)` — see `docs/Agent-explain.md §3` for the
full notational walkthrough (state ⊂ ℝ²⁶, action ⊂ ℝ⁵, transition induced
implicitly by rounding/clipping/area-scaling rules plus a stochastic demand
generator, reward defined in §4 below, γ = 0.99).

**Figure recommendation — Figure 1 (MDP loop):** `paper/figures/fig_mdp_architecture.png`.
Shows the closed loop: State → Residual SAC → Action → Weekly Environment →
(R, S') back to the agent, with the two constraint annotations (residual-policy
equation, 25 m² cap, day-0/day-3 delivery). Source spec:
`docs/architecture_MDP.md`. This is a schematic rendering built from that spec
(no prior diagram existed in the repo); redraw in your target house style if
needed — the content checklist is preserved in that doc for verification.

---

## 3. State, action, and why "26 states" / "5 actions" is a wrong phrase

Both counts describe **dimensionality of a continuous vector**, not a
discrete state/action count. This distinction is worth a sentence in the
paper because reviewers with a tabular-RL background may misread it.

- **State** `s_t ∈ ℝ²⁶` (bounded subset, not all of ℝ²⁶): 5 normalized
  inventories + 5 normalized 7-day forecasts + 5 normalized purchase costs +
  5 normalized carrying costs + 5 normalized shortage penalties + 1 normalized
  day-of-year index. Construction: `env/weekly_retail_env.py:L109-L121`.
- **Action** `a_t ∈ ℝ⁵` (bounded box `[0, MAX_ORDER_i]` per SKU, before
  rounding): one continuous order quantity per SKU, applied to **both**
  deliveries of the week (the same 5-vector is used at day 0 and day 3 —
  see §5).
- **Tabular agents (Q-learning, SARSA) do not consume the full 26-d state.**
  They read only `state[0:5]` (inventory) and `state[5:10]` (forecast) per
  SKU, discretize each into 14 and 10 buckets respectively (140 local states
  per SKU), and maintain **five independent Q-tables** — not one joint table.
  Joint discrete action space would be `8×7×5×7×9 = 17,640` combinations, but
  the implementation never forms this joint table (`agent/q_learning.py:L19-L71`).
  This is the single most important architectural contrast to draw between
  the tabular baselines and SAC: **the tabular agents cannot see the
  cross-SKU floor-space competition that the joint 26-d/5-d representation
  in SAC can.**

Requested vs. executed action distinction (needed for any coupling
discussion): the agent's raw action is `rounded → clipped to MAX_ORDER →
area-checked against the remaining 25 m² → uniformly rescaled across all 5
SKUs if it would overflow → floored to integers`. Because the rescale is
applied to the **whole vector**, one SKU's request can crowd out another's
even though the agent chose them independently
(`env/weekly_retail_env.py:L140-L182`).

---

## 4. Reward — the exact decomposition to publish, and what NOT to conflate

Two objectives must be kept visually and textually distinct in the paper —
conflating them is the most common mistake a first draft makes:

```text
business_profit   = revenue − procurement − storage − shortage_cost
training_reward    = ( business_profit
                        + margin_bonus                    (weight = 0 at runtime)
                        − aggregate_tail_shortage_penalty
                        − per_SKU_fill_gap_penalty
                        − excess_end_inventory_penalty ) × REWARD_SCALE (1e-8)
```

- `business_profit` is what the dashboard reports as KPI/accounting profit —
  it never includes the shaping terms.
- The three shaping penalties exist purely to steer the policy during
  training; they are **not accounting costs** and must not be double-counted
  against reported profit.
- `REWARD_SCALE = 1e-8` is an optimization hyperparameter (gradient/Q-target
  scale), not an economic assumption — multiplying every reward by the same
  positive constant does not change the theoretical reward-maximizing policy
  ordering, but does affect deep-RL training dynamics (gradient magnitude,
  entropy coefficient, numerical stability).

Full formulas for each penalty term (tail shortage uses a squared-excess term
over a 30-unit weekly target; per-SKU fill-gap penalizes shortfall beyond a
93% per-product fill floor; excess-inventory penalizes end-of-week stock
beyond a 2-day-of-demand target) are in
`docs/SERVICE_REPLENISHMENT_PIPELINE_VI.md §6`, with direct code citations at
`env/weekly_retail_env.py:L283-L369`.

**Reward vs. return:** the agent optimizes discounted return
`G_t = Σ γ^k r_{t+k+1}`, not the instantaneous weekly reward. With
weekly steps and `γ = 0.99`, the half-life is ≈ 69 weeks — longer than one
52-week episode, meaning end-of-year outcomes still carry non-trivial weight
in the objective (`docs/Agent-explain.md §19.1`).

---

## 5. The structural fix: two deliveries per week under a fixed 25 m² cap

This is the paper's central engineering contribution and deserves its own
subsection, independent of the RL-algorithm discussion.

**Why a single weekly delivery cannot work under a hard area constraint:** at
measured demand, a representative week requires ≈ 50.39 m² of goods to cover
seven days of sales, but the store area is fixed at 25 m². No reward
shaping or additional training episodes can overcome this — it is a physical
capacity constraint, not a learning problem
(`docs/SERVICE_REPLENISHMENT_PIPELINE_VI.md §3`).

**The fix:** keep the action space at ℝ⁵ (do not expand to ℝ¹⁰ for two
independent delivery decisions), but **replay the same 5-dimensional action
through the same 25 m² twice per week** — once at day 0, once at day 3, after
mid-week sales have freed up floor space. Rationale for keeping ℝ⁵ rather
than moving to ℝ¹⁰: no architecture change to the 26→5 Actor, no added
dimension to the Q-tables, and the resulting policy is interpretable as "a
per-trip replenishment level," at the acknowledged cost that the agent cannot
choose two genuinely different quantities for the two delivery events
(`docs/SERVICE_REPLENISHMENT_PIPELINE_VI.md §4.3`, an intentional limitation
to state explicitly in the paper's Discussion/Limitations).

Per-delivery logic (`_apply_replenishment()`,
`env/weekly_retail_env.py:L140-L182`): round → cap to `MAX_ORDER` → cap to
remaining `MAX_CAPACITY` → compute current + incoming footprint → if over
25 m², scale the whole delivery vector down to fit → floor to integers →
only credit inventory (and only bill procurement) for units that actually
entered the store. This closes a prior accounting gap where procurement was
charged even for units that never made it past the area cap.

---

## 6. Residual policy — the exact mechanism and its academic framing

The deployed SAC policy is **not** a raw learned Gaussian policy. It is a
convex blend of a hand-designed, feasible service baseline and a learned
residual:

```text
baseline(s)      = clip( (forecast × coverage − inventory) / 2, 0, MAX_ORDER )
action_final(s)  = (1 − w) × baseline(s) + w × π_θ(s)
```

with `coverage = 1.20` and `w = 0.10` at the current release
(`agent/sac_alphalr.py:L70-L97`). The division by 2 accounts for there being
two deliveries per week. Because this transform is affine in the actor's raw
output, the log-probability used in both the Bellman target and the actor
loss must be Jacobian-corrected:

```text
log π_final(a|s) = log π_actor(a|s) − 5 · log(w)
```

(`agent/sac_alphalr.py:L89-L97`). This is **not** a way of disabling RL — the
Actor and both Critics still train continuously and the Actor still changes
the executed action — it is an action *prior* that keeps exploration inside
an operationally feasible region.

**Academic name to use throughout the paper:** *Residual Soft Actor-Critic
with automatic entropy-temperature tuning and a fixed-area service prior*
(short form: **Residual SAC-AutoAlpha**). Do not call this "vanilla SAC" or
"SAC-AlphaLR" (see §1 table) in any comparison table or abstract.

### 6.1 Why coverage = 1.20 and residual weight = 0.10 (hyperparameter provenance)

Both values are **empirical, seed-validated choices**, not values taken from
external market literature — say this explicitly in the paper to preempt a
reviewer question.

- **Coverage factor** was swept over `{0.8, 1.0, 1.2, 1.4, 1.6}` on five
  frontier-validation seeds (6201–6205) before any residual weight was
  introduced. `1.2` was the least-inventory candidate that cleared every
  service target (aggregate fill ≥ 97%, every per-SKU fill above its warning
  floor). See **Figure 2** below.
- **Residual weight** was swept over `{0, 0.05, 0.075, 0.10, 0.20}` with the
  Actor already frozen, on five different validation seeds (7601–7605); only
  candidates clearing the full gate were compared on profit, and `0.10` won.
  See **Figure 3** below.

**Figure recommendation — Figure 2 (service–inventory frontier):**
`paper/figures/fig_service_inventory_frontier.png`. X-axis: coverage factor
(0.8–1.6). Left Y-axis: total fill rate (%), with the 97% target line marked.
Right Y-axis: mean end-of-week inventory (days). The selected operating
point (coverage = 1.20) is circled. Data: `outputs/service_inventory_frontier.json`
(`docs/SERVICE_REPLENISHMENT_PIPELINE_VI.md §8`).

**Figure recommendation — Figure 3 (residual-weight ablation):**
`paper/figures/fig_residual_weight_ablation.png`. Three-panel small-multiple:
fill rate, mean weekly stockout, 52-week accounting profit — all against
residual policy weight `w ∈ {0, 0.05, 0.075, 0.10, 0.20}`, selected point
(`w = 0.10`) circled in each panel. Data:
`outputs/service_residual_weight_ablation.json`.

---

## 7. Training, seed roles, and gating — the part reviewers will scrutinize

### 7.1 Seed separation actually implemented (current release pipeline)

| Role | Seeds | Used for |
|---|---|---|
| Train | 7201 | Gradient updates |
| Checkpoint selection | 7301, 7302, 7303 | Periodic candidate evaluation during training |
| Terminal evaluation / reported numbers | 42 | Final headline metrics in §8 below |

Every 10 episodes, the candidate policy is evaluated on the three selection
seeds; promotion requires **simultaneously**: aggregate fill ≥ 97%, every
per-SKU fill ≥ 93%, mean weekly shortage ≤ 30 units, mean end-inventory ≤ 2
days. Only candidates clearing this gate are then compared by P95 shortage
and profit (`docs/SERVICE_REPLENISHMENT_PIPELINE_VI.md §9`,
`pipeline.py:L87-L125`).

> **Caveat to disclose:** the *earlier* generation of this pipeline
> (`docs/PIPELINE_INVENTORY_ECONOMICS_VI.md`) used a richer five-role seed
> separation (calibration-train, calibration-validation, final-train,
> checkpoint-selection, locked terminal holdout — 3 seeds each) with a
> **universal release gate**: a checkpoint is only promoted if SAC *and*
> Q-learning *and* SARSA all clear the terminal holdout simultaneously. In
> that generation's last documented run, SAC passed the terminal holdout but
> Q-learning and SARSA did not, so the artifact was **not promoted**
> (report-only). The current service-pipeline generation evaluates SAC alone
> against its own gate and does promote `actor_service.pth`. **State clearly
> in the paper which governance policy applies to the numbers you report** —
> a single-algorithm release policy is a defensible experimental design
> choice, but it is a different claim than "all three agents passed a shared
> holdout."

### 7.2 Algorithm implementation summary (for a Methods table)

| Agent | Class | On/off-policy | Exploration | State used | Action |
|---|---|---|---|---|---|
| Random | — | n/a, no learning | uniform sampling | ignored | continuous, uniform |
| Q-learning | tabular TD | off-policy (`max Q` bootstrap) | ε-greedy, ε: 0.30→0.01, decay 0.995/episode | 2 features/SKU, bucketed (140 local states/SKU) | discrete per-SKU levels |
| SARSA | tabular TD | on-policy (bootstraps on actual next action) | same ε-greedy schedule as Q-learning | same as Q-learning | discrete per-SKU levels |
| Residual SAC-AutoAlpha | actor-critic, max-entropy | off-policy (replay buffer) | Gaussian sampling + learned entropy temperature | full 26-d vector | continuous 5-d, blended with baseline |

γ = 0.99 for all three learning agents. SAC additionally uses twin critics
(`min(Q1,Q2)` for overestimation control), a Polyak-averaged target critic
(`τ = 0.005`), and automatic entropy tuning (`target_entropy = -5`, learned
`log α`). Full derivations, parameter counts (Actor ≈ 75k params, twin
Critic ≈ 148k params), and worked TD-update numeric examples are in
`docs/Agent-explain.md §9–§19` if the paper needs an appendix.

---

## 8. Headline results table (paste-ready, cite as your own experiment)

52-week evaluation, seed 42, `outputs/actor_service.pth`
(`docs/SERVICE_REPLENISHMENT_PIPELINE_VI.md §1`,
`outputs/service_eval_results.json`):

| Metric | Before (single delivery, unconstrained SAC) | After (two deliveries, Residual SAC) |
|---|---:|---:|
| Mean weekly shortage (units) | 70.50 | **4.75** |
| Total 52-week shortage (units) | 3,666 | **247** |
| P95 weekly shortage (units) | not logged in prior generation | **11.30** |
| Max single-week shortage (units) | 359 | **121** |
| Weeks exceeding 30-unit shortage target | 40/52 | **2/52** |
| Total fill rate | ≈92% (intermediate actor) | **97.81%** |
| Lowest per-SKU fill rate | — | **96.46%** |
| Mean end-of-week inventory | 4.18–4.55 days (intermediate actors) | **1.60 days** |
| 52-week accounting profit | — | **72.216 billion VND** |
| Peak footprint after any single delivery | — | **< 25 m² (hard constraint held)** |

**State this precisely, do not round up the claim:** the *average* and *P95*
weekly shortage targets (< 20–30 units) are met. **Not every week** clears
the target — two tail weeks in the 52-week evaluation still exceed 30 units
(max 121), because physical demand in those weeks exceeds what two
deliveries can move through 25 m² of floor space. This is a tail-risk
finding to report honestly, not a residual bug to paper over
(`docs/SERVICE_REPLENISHMENT_PIPELINE_VI.md §13`).

**Figure recommendation — Figure 4 (before/after bars):**
`paper/figures/fig_before_after_service.png`. Four-panel bar comparison:
mean weekly shortage, P95 weekly shortage (marked n/a for "before" since it
was not logged in that generation), total fill rate, mean end-of-week
inventory days. This is the figure to lead the Results section with.

---

## 9. Limitations to state explicitly (Discussion / Threats-to-validity section)

Carried over directly from the source docs — a paper that omits these while
the code comments already flag them will read as less rigorous, not more
polished:

1. **Tail risk is real, not hidden.** Two of 52 weeks still exceed the
   30-unit shortage target (max 121 units) — a consequence of physical
   throughput limits under `25 m²`, not a training failure. Do not report
   only the mean.
2. **One action, two deliveries.** The same 5-d action vector is executed at
   both day 0 and day 3; the policy cannot make two genuinely different
   decisions for the two delivery events. A future `A ⊂ ℝ¹⁰` variant is the
   natural next step but was deliberately deferred.
3. **"Residual SAC" naming discipline.** Any comparison table that includes
   a vanilla-SAC baseline must make clear that the deployed policy is a
   *blend* with a hand-designed baseline, not a pure learned policy — the
   90/10 split materially changes what "the RL agent achieved" means.
4. **Coverage (1.20) and residual weight (0.10) are empirical, not
   theoretical, constants** derived from seed-limited grid search (5 seeds
   each stage) — not values sourced from retail operations literature.
5. **Reward-shaping terms are not accounting costs.** They must never be
   presented as money the business actually spends or loses.
6. **"Zero stockout and zero excess inventory" is not achievable under
   stochastic demand** — the system is designed to find a Pareto-reasonable
   operating point (fill rate, P95 stockout, inventory days, profit) subject
   to the hard 25 m² constraint, not to eliminate both failure modes
   simultaneously.
7. **Tabular agents observe partial state.** Q-learning/SARSA each maintain
   five *independent* Q-tables keyed only on that SKU's own
   inventory/forecast buckets — they cannot see remaining floor space or
   what the other four SKUs are requesting, which is the likely cause of any
   per-SKU service failures reported for those baselines (see §7.1 caveat
   for the specific documented case: Q-learning failed MacBook/AirPods,
   SARSA failed MacBook, in the terminal holdout of the economics-ablation
   generation).
8. **Forecast is a noisy sample, not the expected value.** The 7-day forecast
   in the state vector is itself one stochastic draw from the same demand
   generator that later produces actual daily demand (via the shared global
   NumPy RNG) — it is a leading indicator, not ground truth, and the two are
   drawn from *different* random samples even though they share a
   distribution (`docs/PIPELINE_INVENTORY_ECONOMICS_VI.md §4.2`).
9. **Provenance of economic inputs.** Carrying-cost rate, shortage-penalty
   rate, and purchase costs are documented as `derived_estimate`,
   `assumption`, or `private_not_available` respectively against public
   benchmarks (inFlow inventory carrying-cost benchmark, Savills Vietnam
   industrial warehouse pricing, Apple Vietnam retail reference) — they are
   defensible modeling choices, not audited invoices. See §10 for full
   citations.
10. **52 vs. 53 decision epochs.** `EPISODE_LENGTH = 365` days does not
    divide evenly into 7-day weeks; all reported evaluations truncate to 52
    weeks (364 days) to avoid a partial 53rd episode, and this truncation
    boundary should be stated alongside any return/discounting discussion.

---

## 10. Citations to add or reuse

### 10.1 Already in `sn-bibliography.bib` — map claims to existing keys

| Claim in this paper | Existing bib key |
|---|---|
| RL/MDP/tabular-methods foundations, Q-learning and SARSA textbook treatment | `bib22` (Sutton & Barto, *Reinforcement Learning: An Introduction*, 2nd ed., MIT Press, 2018) |
| Q-learning original derivation | `bib20` (Watkins & Dayan, 1992) |
| SARSA / on-line Q-learning historical source | `bib21` (Rummery & Niranjan, 1994) |
| Soft Actor-Critic, original formulation, twin critics, max-entropy objective | `bib3` (Haarnoja et al., ICML 2018) |
| Automatic entropy-temperature tuning for SAC | `bib23` (Haarnoja et al., arXiv:1812.05905, 2018) |
| Classical (s,S) multi-echelon inventory theory, for framing why a hard capacity constraint changes the classical policy shape | `bib4` (Clark & Scarf, 1960), `bib8` (Scarf, 1960) |
| Newsvendor-style deep learning framing, if the paper discusses order-quantity learning as a newsvendor variant | `bib13` (Oroojlooyjadid et al., 2020) |
| Deep RL for inventory management, general framing / related-work paragraph | `bib1`, `bib5`, `bib14`, `bib15`, `bib16`, `bib17`, `bib18`, `bib19` |
| Foundational deep RL (DQN) if discussing value-based deep RL lineage | `bib10` (Mnih et al., *Nature*, 2015) |
| Continuous-control deep RL lineage (DDPG), useful contrast point before introducing SAC | `bib11` (Lillicrap et al., ICLR 2016) |
| Dynamic programming / Bellman equation, if the paper derives Q-value definitions from scratch | `bib9` (Bellman, 1957) |
| Classical EOQ, if framing the storage-area constraint against classical lot-sizing | `bib6` (Harris, 1913), `bib7` (Arrow, Harris & Marschak, 1951) |

### 10.2 Non-academic sources cited for economic-input provenance (add as footnotes or a data-appendix, not as research citations)

- Carrying-cost rate benchmark (20–30%): inFlow Inventory, "What Are
  Inventory Carrying Costs and How Are They Calculated?"
  <https://www.inflowinventory.com/blog/what-are-inventory-carrying-costs-and-how-are-they-calculated>
- Vietnam industrial/warehouse rent benchmark (sanity check only, not full
  carrying cost): Savills Vietnam, "Price of Warehouse for Lease in Vietnam."
  <https://industrial.savills.com.vn/price-of-warehouse-for-lease-in-vietnam/>
- Retail price reference for purchase-cost assumption: Apple Vietnam retail
  storefront. <https://www.apple.com/vn/shop/buy-iphone>
- Shortage/service-penalty framing: Oracle, "Retail Inventory Management."
  <https://www.oracle.com/retail/fashion/retail-inventory-management/>

State in the paper's data section that these are **benchmarks and modeling
assumptions**, explicitly labeled in the codebase's own metadata as
`derived_estimate`, `market_benchmark`, `private_not_available`, and
`assumption` respectively — not invoices or contractual figures
(`docs/PIPELINE_INVENTORY_ECONOMICS_VI.md §3.2.1`).

---

## 11. Suggested Methodology chapter outline

1. Problem formulation and assumptions (use §2 text above).
2. Weekly MDP definition — S, A, P, R, γ (§2–§4).
3. State representation, 26-d vector, per-block normalization (§3).
4. Action space and the two hard physical constraints: per-SKU `MAX_ORDER`
   and the 25 m² area cap (§3, §5).
5. The two-delivery redesign and why one delivery per week is physically
   infeasible (§5) — Figure 1.
6. Demand/transition model: `HolidayDemandGenerator`, day-of-week and
   seasonal multipliers, holiday cosine boosts, Gaussian noise.
7. Reward decomposition: accounting profit vs. training objective vs. the
   three shaping penalties (§4).
8. Tabular baselines: Q-learning and SARSA, five independent per-SKU Q-tables
   (§6, table in §7.2).
9. Residual SAC-AutoAlpha: Actor/twin-Critic architecture, the baseline-blend
   policy, Jacobian log-prob correction (§6) — Figures 2–3.
10. Training protocol and seed-role separation, including the governance
    caveat about universal vs. single-algorithm release gates (§7).
11. Evaluation metrics and headline results (§8) — Figure 4.
12. Threats to validity / limitations (§9), citing the provenance table (§10.2)
    for all economic assumptions.

---

## 12. Figure manifest (for LaTeX `\includegraphics` or Word insertion)

| Figure | File | One-line caption to use |
|---|---|---|
| Fig. 1 | `paper/figures/fig_mdp_architecture.png` | MDP architecture of the fixed-capacity inventory control system: state, residual-policy action, weekly environment with two deliveries, and reward feedback. |
| Fig. 2 | `paper/figures/fig_service_inventory_frontier.png` | Service–inventory frontier under the fixed 25 m² constraint across five coverage-factor settings; coverage = 1.20 selected as the least-inventory candidate clearing all service targets. |
| Fig. 3 | `paper/figures/fig_residual_weight_ablation.png` | Residual-policy-weight ablation with the Actor frozen at coverage = 1.20; w = 0.10 selected among eligible candidates by profit. |
| Fig. 4 | `paper/figures/fig_before_after_service.png` | Service and inventory outcomes before vs. after the two-delivery, Residual-SAC redesign, 52-week evaluation, seed 42. |

All four are regenerated directly from the repository's own JSON experiment
artifacts and are safe to cite as "figure generated from experiment logs
[artifact path]" in a reproducibility statement.
