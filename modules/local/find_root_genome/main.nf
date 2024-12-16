process FIND_ROOT_GENOME {
    tag "$accession"
    label 'process_single'
    container 'community.wave.seqera.io/library/pip_requests_retry:be391101dc2ee5f0'

    input:
    tuple val(accession)

    output:
    path('combined_haplotype_genome.fa.gz'), emit: root_organism_fasta

    script:
    """
    metagenomes_data_import_mgnify.py ${accession}

    cat *.fa.gz > combined_haplotype_genome.fa.gz
    """
}