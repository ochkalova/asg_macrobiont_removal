process FIND_ROOT_GENOME {
    label 'process_single'
    container 'community.wave.seqera.io/library/pip_requests_retry:be391101dc2ee5f0'

    input:
    tuple val(meta), path(assembly_fasta)

    output:
    path('combined_haplotype_genome.fa'), emit: root_organism_fasta

    script:
    """
    metagenomes_data_import_mgnify.py ${meta.id}

    cat *.fa.gz > combined_haplotype_genome.fa
    """
}