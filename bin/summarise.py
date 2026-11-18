#!/usr/bin/env python
import glob

import pandas as pd

results = pd.concat([pd.read_csv(f, sep="\t") for f in sorted(glob.glob("tsv/*.tsv"))], ignore_index=True)
results.to_csv("trident_icc_results.tsv", sep="\t", index=False)

failed = results[results["failed_step"].notna()] if "failed_step" in results else results.iloc[:0]
done = results.drop(failed.index)
print(f"slides: {len(results)}, compared: {len(done)}, failed: {len(failed)}")
for (step, error), n in failed.groupby(["failed_step", "error"], dropna=False).size().items():
    print(f"  failed in {step} ({n} slides): {error}")
if len(done):
    change = done["tissue_change_pct"]
    print(f"slides with no tissue as stored: {(done['tissue_stored'] == 0).sum()}")
    print(f"tissue area change with ICC: median {change.median():+.1f}%, "
          f"range {change.min():+.1f}% to {change.max():+.1f}%, "
          f"{(change.abs() > 5).sum()} slides change by more than 5%")
    for folder in sorted(c[:-len("_lost")] for c in done if c.endswith("_lost")):
        before, after = done[f"{folder}_stored"].sum(), done[f"{folder}_icc"].sum()
        pct = f"{100 * (after - before) / before:+.1f}%" if before else "n/a"
        print(f"{folder}: {before:.0f} tiles as stored, {after:.0f} with ICC ({pct}), "
              f"{done[f'{folder}_lost'].sum():.0f} lost, {done[f'{folder}_gained'].sum():.0f} gained")
