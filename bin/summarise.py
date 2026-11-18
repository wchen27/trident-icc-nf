#!/usr/bin/env python
import glob

import pandas as pd

results = pd.concat(pd.read_csv(f, sep="\t") for f in sorted(glob.glob("tsv/*.tsv")))
results.to_csv("trident_icc_results.tsv", sep="\t", index=False)

change = results["tissue_change_pct"]
print(f"slides compared: {len(results)}")
print(f"tissue area change with ICC: median {change.median():+.1f}%, "
      f"range {change.min():+.1f}% to {change.max():+.1f}%, "
      f"{(change.abs() > 5).sum()} slides change by more than 5%")
for folder in sorted(c[:-len("_lost")] for c in results if c.endswith("_lost")):
    before, after = results[f"{folder}_stored"].sum(), results[f"{folder}_icc"].sum()
    print(f"{folder}: {before} tiles as stored, {after} with ICC ({100 * (after - before) / before:+.1f}%), "
          f"{results[f'{folder}_lost'].sum()} lost, {results[f'{folder}_gained'].sum()} gained")
