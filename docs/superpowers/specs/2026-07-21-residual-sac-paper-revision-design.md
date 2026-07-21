# Residual SAC Paper Revision Design

## Objective

Rewrite `sn-article.tex` so that it reports only the current fixed-capacity,
two-delivery Residual SAC-AutoAlpha system. Remove the previous single-delivery
experiment, its policy comparisons, metrics, interpretations, and conclusions
because that experimental design is invalid for the revised paper.

## Authoritative Sources

- `ref_paper_v4_update.md` supplies the verified technical narrative, values,
  experimental protocol, caveats, and citation mapping.
- The current implementation and experiment artifacts cited by that document
  are the provenance for technical and numerical claims.
- `figures/fig_mdp_architecture.png`,
  `figures/fig_service_inventory_frontier.png`, and
  `figures/fig_residual_weight_ablation.png` are the figures used in the paper.
- `figures/fig_before_after_service.png` is excluded because its “Before” arm
  belongs to the invalid earlier design.

## Editorial Scope

Retain the Springer Nature LaTeX template, author metadata, declarations, and
bibliography infrastructure. Retain literature-review material only where it
still supports the revised problem and method. Rewrite the title, abstract,
introduction, methodology, experimental setup, results, discussion,
limitations, conclusion, tables, equations, figure captions, cross-references,
and reproducibility statements wherever they depend on the earlier design.

Delete all claims that treat Random, Q-learning, SARSA, single-delivery SAC, or
the old SAC-AutoAlpha checkpoint as current experimental results. The paper may
mention tabular methods or vanilla SAC only as literature or architectural
context; it must not report the invalid old comparison as evidence.

## Revised Scientific Narrative

The central problem is physical infeasibility: representative seven-day demand
requires about 50.39 m² of goods, while the retail area is capped at 25 m².
The structural intervention is therefore two replenishment events per week
(day 0 and day 3), reusing the same five-dimensional per-trip action after
mid-week sales release capacity.

The control policy is Residual SAC-AutoAlpha, not vanilla SAC. Its executed
proposal blends a service-coverage baseline and the learned actor:

`a_final(s) = (1 - w) baseline(s) + w pi_theta(s)`,

with coverage factor 1.20 and residual weight `w = 0.10`. The paper explains
the division by two in the baseline, the affine-policy Jacobian correction,
the hard area-scaling mechanism, automatic entropy-temperature tuning, and the
separation between accounting profit and reward-shaping penalties.

## Evidence and Figures

The methodology uses the MDP architecture figure. The experimental-selection
subsection uses the service–inventory frontier and residual-weight ablation
figures to explain why coverage 1.20 and residual weight 0.10 were selected.
The invalid before/after figure is not included or cited.

The main result table reports only the current 52-week, seed-42 terminal
evaluation:

- mean weekly shortage: 4.75 units;
- total shortage: 247 units;
- P95 weekly shortage: 11.30 units;
- maximum weekly shortage: 121 units;
- weeks above the 30-unit target: 2/52;
- aggregate fill rate: 97.81%;
- lowest per-SKU fill rate: 96.46%;
- mean end-of-week inventory: 1.60 days;
- accounting profit: 72.216 billion VND;
- peak footprint after a delivery: below the hard 25 m² limit.

The text must not invent missing comparisons, uncertainty intervals, or
causal attribution that the experiment does not establish.

## Experimental Protocol and Claim Boundaries

Describe the implemented separation between training seed 7201, checkpoint
selection seeds 7301–7303, and terminal reporting seed 42. Clearly distinguish
this protocol from earlier experimental generations. Coverage selection seeds
6201–6205 and residual-weight validation seeds 7601–7605 are documented as
empirical tuning pools, not external constants.

Frame the terminal result as a single held-out scenario, not a multi-seed
confidence estimate. The paper must explicitly disclose that two weeks exceed
the shortage threshold, one action is reused for both delivery events,
economic inputs include modeling assumptions, the forecast is noisy, and the
365-day environment is evaluated over 52 complete weeks.

## Validation

After editing, validate that:

1. no substantive old metric or single-delivery claim remains;
2. all algorithm names consistently use Residual SAC-AutoAlpha;
3. figure paths exist and the before/after figure is absent from the source;
4. numerical claims agree with `ref_paper_v4_update.md`;
5. LaTeX cross-references and bibliography keys resolve;
6. the document compiles successfully with the repository's available LaTeX
   toolchain, or any unavailable toolchain is reported explicitly.

## Out of Scope

Do not regenerate experiments, alter model code, fabricate multi-seed
statistics, add unsupported baselines, or edit the supplied figure images.
