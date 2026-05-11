# Future Work

## Dataset Expansion

The next useful dataset size is about 300 trajectories. Expansion should not mean writing more near-duplicates. Each new item should have a clear proxy mapping, an expected turn where redirection should occur, and a short note explaining what workflow shape it tests.

The review process should include at least one molecular biologist, one biosecurity reviewer, and one model-evaluation researcher. The domain reviewer checks scientific plausibility. The biosecurity reviewer checks that the proxy remains safe. The eval reviewer checks that the item produces a measurable distinction between turn-level and trajectory-level behavior.

New proxy domains should be added only when their mapping is explicit. Plausible additions include biosecurity-adjacent dual-use chemistry in proxy form, virology workflows represented by harmless teaching systems, and supply-chain or screening workflows represented by synthetic non-biological records.

## Gated Dangerous-Adjacent Extension

The public repo should remain safe. A separate private tier could contain dangerous-adjacent trajectories under access controls similar in spirit to those used by SecureBio, Sentinel Bio, and Frontier Model Forum bio working groups. The details should be inherited from an institution with an existing review process, not invented casually inside this repo.

That private tier needs named access owners, reviewer approval, logging, limited export, and a clear rule for who can run models against it. It also needs a separation between item authors, model operators, and result reviewers so that no single person is casually expanding both content and access.

The public proxy suite remains useful after the gated tier exists. It provides CI tests, examples for external reviewers, and a shared method that can be discussed without distributing sensitive content.

## Production Red-Team Integration

A production red-team unit would run trajectories continuously, not as a one-off benchmark. It would maintain a versioned dataset, run scheduled model evaluations, inspect failures, and produce short reports that engineering teams can act on.

For a frontier lab, the artifact is a regression test suite for multi-turn biological assistance. For a gene synthesis provider, the artifact is a set of trajectory patterns that can inform monitoring and escalation. In both cases, the report should include transcripts, turn labels, trajectory labels, and a reviewer note explaining whether the model failed by over-answering, over-refusing, or behaving inconsistently.

Responsible disclosure should be boring and specific. Share only the minimum transcript needed to reproduce the failure, redact content that would increase misuse risk, give the model owner time to respond, and publish only proxy-safe examples unless a formal disclosure process says otherwise.

The person leading this work should be comfortable with biology, model evaluation, and operational security. They would need funding for domain reviewers, model access, secure data handling, and enough engineering time to turn the prototype into a maintained evaluation service.
