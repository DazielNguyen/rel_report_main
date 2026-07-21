# Residual SAC Paper Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `sn-article.tex` as a self-consistent paper about the current two-delivery, fixed-capacity Residual SAC-AutoAlpha system, using only verified current results.

**Architecture:** Preserve the Springer Nature document shell, author metadata, and valid bibliography entries while replacing the scientific body as one coherent narrative. Use `ref_paper_v4_update.md` as the numerical and technical authority, incorporate the three approved figures, and validate the finished source through targeted stale-claim scans plus a LaTeX build.

**Tech Stack:** Springer Nature LaTeX (`sn-jnl`), BibTeX bibliography, PNG experiment figures, shell-based source validation, available LaTeX compiler.

## Global Constraints

- Do not report the old single-delivery experiment or Random/Q-learning/SARSA comparisons as current evidence.
- Name the method consistently “Residual SAC-AutoAlpha.”
- Use only `fig_mdp_architecture.png`, `fig_service_inventory_frontier.png`, and `fig_residual_weight_ablation.png`; exclude `fig_before_after_service.png`.
- Report the terminal evaluation as one held-out seed-42 scenario, not a multi-seed confidence estimate.
- Do not regenerate experiments, modify model code, invent statistics, add unverified baselines, or edit supplied images.
- Preserve the Springer Nature template, author metadata, declarations, and bibliography infrastructure.

---

### Task 1: Establish source invariants and replacement boundaries

**Files:**
- Read: `ref_paper_v4_update.md`
- Read: `sn-article.tex`
- Read: `sn-bibliography.bib`
- Read: `figures/fig_mdp_architecture.png`
- Read: `figures/fig_service_inventory_frontier.png`
- Read: `figures/fig_residual_weight_ablation.png`

**Interfaces:**
- Consumes: approved design in `docs/superpowers/specs/2026-07-21-residual-sac-paper-revision-design.md`.
- Produces: a verified list of template regions to retain and scientific-body regions to replace.

- [ ] **Step 1: Verify the three approved figures exist**

Run:

```bash
for f in figures/fig_mdp_architecture.png figures/fig_service_inventory_frontier.png figures/fig_residual_weight_ablation.png; do test -f "$f" || exit 1; done
```

Expected: exit status 0 with no output.

- [ ] **Step 2: Record the document boundaries and bibliography keys**

Run:

```bash
rg -n '^\\(title|abstract|section|backmatter|bibliography)|^@' sn-article.tex sn-bibliography.bib
```

Expected: title, abstract, Sections 1–8, `\backmatter`, bibliography command, and existing BibTeX entries are listed.

- [ ] **Step 3: Confirm the new result values in the authority file**

Run:

```bash
rg -n '4\.75|247|11\.30|121|2/52|97\.81|96\.46|1\.60|72\.216|25 m²' ref_paper_v4_update.md
```

Expected: every terminal metric appears at least once.

### Task 2: Rewrite the scientific body

**Files:**
- Modify: `sn-article.tex`

**Interfaces:**
- Consumes: verified claims and values from Task 1.
- Produces: a complete English-language Springer paper centered on Residual SAC-AutoAlpha.

- [ ] **Step 1: Replace the title, abstract, and introduction**

Write a title naming fixed capacity, two deliveries, and Residual SAC. The abstract must state the 25 m² constraint, the structural two-delivery design, the residual-policy equation in prose, the seed-separated selection protocol, the main seed-42 metrics, and the two tail weeks without comparing against invalid old policies. The introduction must define the physical infeasibility, research objective, contributions, and revised section map.

- [ ] **Step 2: Retain and refocus the literature review**

Keep classical inventory, MDP, and SAC citations that support the current method. Remove claims that the paper experimentally compares Random, Q-learning, and SARSA. Frame residual control and hard shared capacity as the paper’s methodological context without claiming unsupported novelty.

- [ ] **Step 3: Replace the methodology**

Include the weekly MDP; continuous state `s_t \in \mathbb{R}^{26}`; action `a_t \in \mathbb{R}^{5}`; requested-to-executed action scaling; day-0/day-3 delivery mechanism; accounting-profit versus shaping-reward decomposition; Residual SAC baseline and blend; Jacobian log-probability correction; and SAC actor/twin-critic/automatic-temperature settings. Insert the approved MDP figure with a unique label.

- [ ] **Step 4: Replace the experimental setup**

Document coverage sweep `{0.8, 1.0, 1.2, 1.4, 1.6}` on seeds 6201–6205, residual-weight sweep `{0, 0.05, 0.075, 0.10, 0.20}` on seeds 7601–7605, training seed 7201, selection seeds 7301–7303, terminal seed 42, the joint service/inventory gate, and the 52-complete-week truncation. Insert the service–inventory and residual-weight figures with separate labels and captions.

- [ ] **Step 5: Replace results, discussion, limitations, and conclusion**

Create one current-results table containing exactly the ten approved metrics. Interpret the results without causal overreach. Explicitly discuss two weeks above 30 units, maximum shortage 121, single action reused twice, empirical hyperparameters, noisy forecast, economic-input provenance, and lack of a multi-seed terminal confidence interval. Conclude only that the current policy met aggregate and P95 service targets in the held-out seed-42 scenario while respecting the hard footprint constraint.

- [ ] **Step 6: Preserve declarations and bibliography wiring**

Retain `\backmatter`, existing declarations, `\bibliography{sn-bibliography}`, and `\end{document}`. Remove stale editorial comments that describe old results or unverified placeholders.

- [ ] **Step 7: Review the complete source diff**

Run:

```bash
git diff -- sn-article.tex
```

Expected: the Springer shell remains intact; the scientific body consistently describes only the current design.

### Task 3: Validate content integrity and compile

**Files:**
- Test: `sn-article.tex`
- Test: `sn-bibliography.bib`
- Generated if the compiler is available: standard ignored LaTeX build artifacts.

**Interfaces:**
- Consumes: rewritten paper from Task 2.
- Produces: evidence that stale claims are absent, references are valid, approved figures are used, and LaTeX compiles.

- [ ] **Step 1: Scan for forbidden old claims and excluded figure**

Run:

```bash
rg -n '155\.71|185\.05|29\.35|2\{,\}013|82\.1|93\.01|one delivery|once per week|actor_evaluation|fig_before_after_service|Random.*Q-learning.*SARSA' sn-article.tex
```

Expected: no matches.

- [ ] **Step 2: Check current naming, metrics, and approved figures**

Run:

```bash
rg -n 'Residual SAC-AutoAlpha|4\.75|247|11\.30|121|97\.81|96\.46|1\.60|72\.216|fig_mdp_architecture|fig_service_inventory_frontier|fig_residual_weight_ablation' sn-article.tex
```

Expected: the method name, all current metrics, and all three approved figures are present.

- [ ] **Step 3: Check bibliography-key resolution statically**

Run:

```bash
comm -23 <(rg -o '\\cite\{[^}]+\}' sn-article.tex | sed 's/\\cite{//;s/}//' | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort -u) <(rg '^@' sn-bibliography.bib | sed -E 's/^@[^{]+\{([^,]+),/\1/' | sort -u)
```

Expected: no output.

- [ ] **Step 4: Check LaTeX syntax and build**

Run:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error sn-article.tex
```

Expected: exit status 0 and `sn-article.pdf` generated. If `latexmk` is unavailable, run the repository-supported equivalent and report the unavailable tool explicitly if no compiler exists.

- [ ] **Step 5: Inspect warnings and final diff**

Run:

```bash
rg -n 'LaTeX Warning|undefined|multiply defined|Citation.*undefined|Reference.*undefined' sn-article.log
git diff --check
git status --short
```

Expected: no unresolved citations/references, no whitespace errors, and only intended source/untracked figure changes are shown.

- [ ] **Step 6: Commit the paper rewrite**

```bash
git add sn-article.tex
git commit -m "docs: rewrite paper for residual SAC service policy"
```
