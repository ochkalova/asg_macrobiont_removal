process FILTER_PAF {
    tag "$meta.id"

    input:
    tuple val(meta), path(paf_file)

    output:
    tuple val(meta), path("${meta.id}.txt"), emit: unmapped_contigs_txt

    script:
    """
    awk '(\$6 == "*") || ((\$4 - \$3) / \$2) < 0.5' ${paf_file} > ${meta.id}.txt
    """
}