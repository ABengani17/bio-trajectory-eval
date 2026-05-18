# Reviewer guide

```bash
bio-trajectory-eval report --in results/scan.json
```

Work blocked packages first, then packages with high-severity findings.

For each finding:

1. Confirm the manifest path is correct.
2. Check whether the record exists upstream but was not exported.
3. Decide whether to fix the manifest, escalate review, or reject the run.
4. Consider adding a `finding_actions` entry in local policy if the code should always block or always review.

Missing provenance, screening, approval, or biosafety fields on biological or unknown samples should not reach scheduling without an explicit review path.
