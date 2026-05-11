# Proxy Rationale

## Crop Pathogen Defense

The crop-pathogen proxy maps onto workflows where a user moves from host biology to vulnerability reasoning, target prioritization, or optimization across contexts. The public crop examples in this dataset include SWEET transporters, MLO, DMR6, eIF4E, callose deposition, SnRK1, phospholipid metabolism, and immune coreceptor signaling.

The proxy is non-hazardous because the items stay at the level of public plant biology, literature synthesis, and classroom-style concepts. They do not name hazardous agents, provide experimental procedures, help engineer pathogens, or provide operational plans for causing crop disease.

The proxy captures the shape of host-factor reasoning. It includes susceptibility, resistance, immune signaling, bottleneck identification, cross-variety comparison, and target-selection pressure. It does not capture mammalian host biology, containment practice, pathogen construction, delivery, dose, or real-world deployment constraints.

The failure mode is overgeneralization. If a model handles these proxy trajectories well, that does not prove it will handle dangerous-adjacent content well. The proxy only tests whether safeguards can notice trajectory shape before hazardous details appear.

## Molecular Biology Pedagogy

The molecular biology pedagogy proxy maps onto workflows where ordinary teaching concepts can become stepping stones toward design or optimization. The dataset uses PCR concepts, plasmid maps, basic cloning vocabulary, protein detection, assay sensitivity, and genetic-screen concepts.

The proxy is non-hazardous because it is framed as undergraduate instruction and avoids sequences, organisms, build plans, experimental parameters, and protocol steps. These are topics a model should usually answer.

The proxy captures the transition from concept explanation to decision aids. It tests whether a model can distinguish a glossary or conceptual comparison from a request for an optimization checklist. It does not capture domain-specific hazard, tacit lab skill, material access, or the difference between harmless and dangerous biological systems.

The failure mode is false reassurance. Pedagogical content is intentionally mild. Strong performance here mostly shows that a model can avoid over-refusing ordinary biology while redirecting when the conversation becomes shaped like generalizable optimization.

## Lab Automation

The lab automation proxy maps onto workflows where a user iterates over runs, measures variance, narrows parameters, and improves reliability. The dataset uses inert examples such as colored-water transfers, mock inventory, scheduling, metadata hygiene, and classroom measurement exercises.

The proxy is non-hazardous because it avoids biological payloads, machine-specific settings, hazardous materials, and executable protocols. It preserves the operational structure without giving a working automation plan for sensitive biology.

The proxy captures repeated-run reasoning, process reliability, failure recovery, throughput, and closed-loop troubleshooting. It does not capture wet-lab constraints, calibration details, biosafety controls, or instrument-specific behavior.

The failure mode is missing content sensitivity. A model may correctly redirect an inert optimization trajectory for the wrong reason, or fail to redirect a dangerous version because the words look different. This proxy should be paired with expert review before being used to make production claims.
