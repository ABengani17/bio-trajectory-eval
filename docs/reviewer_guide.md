# Reviewer Guide

Start with:

```bash
bio-trajectory-eval report --in results/scan.json
```

Review blocked packages first, then review packages with high findings.

For each finding, check:

- whether the referenced manifest path is correct
- whether the missing record exists in a source system but was not exported
- whether the package should be fixed, routed to biosafety review, or rejected
- whether the finding code should become a local policy rule

The scanner is intentionally conservative about missing records. If a sample has biological or unknown material and no provenance, screening, approval, or biosafety metadata, the package should not silently move into automation scheduling.
