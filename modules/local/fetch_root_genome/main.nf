process FETCH_ROOT_GENOME {
    tag "$accession"
    label 'process_single'
    container 'community.wave.seqera.io/library/pip_requests_retry:be391101dc2ee5f0'

    input:
    tuple val(accession)

    output:
    tuple val(accession), path('*.fa.gz'), emit: root_organism_fasta

    script:
    """
    fetch_root_genome_from_asg_portal.py ${accession}

    """
}