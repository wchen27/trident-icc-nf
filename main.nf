#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

params.samplesheet = null
params.outdir      = 'results'
params.limit       = -1
params.min_tissue  = '0.25 0.75'

process TRIDENT_ICC {
    tag "$name"
    publishDir "${params.outdir}/slides", mode: 'copy', pattern: "${name}"
    publishDir "${params.outdir}/masks", mode: 'copy', pattern: "*.png"

    input:
    tuple val(name), path(slide)

    output:
    path "${name}.tsv", emit: tsv
    path "${name}_mask.png", optional: true
    path "${name}"

    script:
    def ext = slide.name.tokenize('.').last()
    """
    mkdir wsi "${name}"
    ln -s "\$PWD/${slide}" "wsi/${name}.${ext}"

    run() {
        \$1 batch -- --task seg --wsi_dir wsi --job_dir \$2 --segmenter otsu --gpus -1 --max_workers 0 || return 1
        for t in ${params.min_tissue}; do
            \$1 batch -- --task coords --wsi_dir wsi --job_dir \$2 --coords_dir tiles_\$t --gpus -1 \
                --mag 20 --patch_size 512 --overlap 0 --min_tissue_proportion \$t --max_workers 0 || return 1
        done
        mkdir "${name}/\$2" && cp -r \$2/contours_geojson \$2/tiles_* "${name}/\$2/"
    }
    step=done
    run trident stored > "${name}/stored.log" 2>&1 || step=stored
    if [ \$step = done ]; then run trident_icc.py icc > "${name}/icc.log" 2>&1 || step=icc; fi
    if [ \$step = done ]; then compare_slide.py "${name}" "wsi/${name}.${ext}" > "${name}/compare.log" 2>&1 || step=compare; fi
    if [ \$step != done ]; then
        error=\$(grep -v -i warning "${name}/\$step.log" | tail -n 1 | tr '\\t' ' ' | sed "s|${name}|<slide>|g")
        printf 'name\\tfailed_step\\terror\\n%s\\t%s\\t%s\\n' "${name}" "\$step" "\$error" > "${name}.tsv"
    fi
    """
}

process SUMMARY {
    publishDir params.outdir, mode: 'copy'

    input:
    path tsvs, stageAs: 'tsv/*'

    output:
    path 'trident_icc_results.tsv'
    path 'trident_icc_summary.txt'

    script:
    """
    summarise.py | tee trident_icc_summary.txt
    """
}

workflow {
    if (!params.samplesheet) {
        error "Please give --samplesheet"
    }
    slides = Channel.fromPath(params.samplesheet, checkIfExists: true)
        .splitCsv(header: true)
        .map { row -> tuple(row.name, file(row.Address)) }
    def limit = params.limit.toString().toInteger()
    if (limit > 0) {
        slides = slides.take(limit)
    }

    TRIDENT_ICC(slides)
    SUMMARY(TRIDENT_ICC.out.tsv.collect())
}
