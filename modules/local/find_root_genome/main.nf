process FIND_ROOT_GENOME {
    tag "$accession"
    label 'process_single'
    container 'community.wave.seqera.io/library/pip_requests_retry:be391101dc2ee5f0'

    input:
    tuple val(accession)

    output:
    path('*.fa.gz'), emit: root_organism_fasta

    script:
    """
    metagenomes_data_import_mgnify.py ${accession}

    # List all *.fa.gz files
    input_files=\$(ls *.fa.gz)

    # Create a combined filename by removing '.fa.gz' and joining with underscores
    output_file=\$(echo \$input_files | sed 's/\\.fa\\.gz//g' | tr ' ' '_' | sed 's/_\$//').fa.gz

    # Concatenate the input files into the output file
    cat \$input_files > \$output_file

    """
}