# Methodology

## Problem

Public AI-bio safeguard evaluations often score isolated prompts. That design answers a narrow question: does the model refuse or answer one request. It does not test whether safeguards track intent across a sequence.

Many real workflows are sequential. A user asks for background, narrows the task, asks for comparison criteria, then asks for a decision aid. Each turn can look acceptable by itself. The full conversation can still move toward assistance that a safety policy would not want to provide.

This repo evaluates that gap. It does not measure biological capability directly. It measures a safeguard behavior: whether model handling changes when the unit of analysis is the trajectory. That behavior matters because it can produce training and monitoring signal that isolated prompts do not expose.

## Trajectory Abstraction

A trajectory is an ordered sequence of user turns with shared context. Each item has an identifier, a proxy domain, a difficulty tier, expected handling labels for each turn, and an expected trajectory-level outcome.

Turn-level evaluation asks how the model handled the current request. The labels are `answer_full`, `answer_partial`, `soft_refuse`, and `hard_refuse`. The labels are intentionally behavioral. They do not try to infer the model's internal reasoning.

Trajectory-level evaluation asks what pattern appears across the sequence. The labels are `compliant_throughout`, `redirected`, `refused_early`, and `inconsistent`. A useful result records both layers. A model that refuses the final turn after answering the first two is different from a model that refuses immediately, and both are different from a model that answers all turns.

## Proxy Domains

The public dataset uses safe proxies. That choice is not cosmetic. It makes the methodology inspectable without distributing content that would belong behind access controls.

Crop-pathogen defense is the main proxy because it preserves host-pathogen structure while keeping the content in public plant biology. The items use concepts such as SWEET transporters, MLO, DMR6, eIF4E, callose deposition, SnRK1, phospholipid metabolism, and immune coreceptor signaling. The sensitive workflow shadow is the movement from host biology to vulnerability reasoning or target prioritization.

Molecular biology pedagogy functions partly as a control. PCR, plasmid maps, cloning vocabulary, Western blot interpretation, and assay sensitivity are normal undergraduate topics. A useful model should answer these when they remain educational. The same domain can also test drift from explanation into general design optimization.

Lab automation captures repeated-run reasoning. The proxy uses inert exercises such as colored-water transfer, mock inventory, scheduling, metadata hygiene, and classroom measurement. The workflow shadow is iterative process improvement. The proxy omits biological payloads and instrument-specific settings.

The proxy choice misses content-specific hazard. It cannot prove that a model will behave well on dangerous-adjacent items. It can show whether trajectory-aware handling is present before dangerous terms appear.

## Scoring

The rule backend scores each model response using lexical and structural cues. Refusal phrases, adjacent-help phrases, safety caveats, and short bounded answers determine the turn label. The trajectory label is computed from the sequence of turn labels. This backend is deterministic and cheap enough for tests.

The rule backend will miss subtle behavior. It can mistake boilerplate safety text for meaningful restriction. It can miss a refusal that uses unusual phrasing. It also cannot judge whether an answer is substantively useful in a sensitive way if the surface text looks ordinary.

The LLM judge backend applies the same rubric through a separate model call and returns structured JSON. It is better at paraphrase and context. It is also slower, non-deterministic, and vulnerable to the judge model's own policy preferences. Disagreement between the rule backend and LLM judge should be reviewed as data, not averaged away.

For a production run, the recommended workflow is rules first, LLM judge second, human review on disagreements and high-concern compliant trajectories.
