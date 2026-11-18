# trident-icc-nf

Runs TRIDENT tissue segmentation and tiling on each slide twice, once as stored and once with the slide's own ICC colour profile applied, and compares the two.

- Container: `wchen27/trident-cpu:0.3.1-tiles.3` (TRIDENT v0.3.1)
- Settings: Otsu segmentation, then tiles at 20x, 512 px, no overlap, minimum tissue 25% and 75%
- `bin/trident_icc.py` runs `trident` with every pixel read converted from the slide's ICC profile to sRGB. Slides without a profile are read as stored

## Run

```
nextflow run main.nf --samplesheet samplesheet.csv --outdir results [--limit 5] [--min_tissue '0.25 0.75']
```

The samplesheet needs `name` and `Address` columns. If TRIDENT or the comparison fails on a slide, the slide gets a row with the failed step and the last error line, and its logs are kept in `slides/<name>/`.

## Output

- `trident_icc_results.tsv`: one row per slide. Tissue area as stored and with ICC, change, tissue lost and gained (% of stored area), and for each tile setting the tiles as stored, with ICC, lost and gained
- `trident_icc_summary.txt`: totals across slides, and failures grouped by error
- `masks/<name>_mask.png`: slide thumbnail with tissue lost (orange) and gained (blue)
- `slides/<name>/`: tissue contours and tile coordinates for both runs, and the TRIDENT logs
