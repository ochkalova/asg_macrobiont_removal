include { BLAST_BLASTN as BLAST_BLASTN_HUMAN_PHIX } from '../../modules/nf-core/blast/blastn/main'
include { BLAST_BLASTN as BLAST_BLASTN_HOST       } from '../../modules/nf-core/blast/blastn/main'
include { BLAST_MAKEBLASTDB                       } from '../../modules/nf-core/blast/makeblastdb/main'
include { SEQKIT_GREP as SEQKIT_GREP_HUMAN_PHIX   } from '../../modules/nf-core/seqkit/grep/main'
include { SEQKIT_GREP as SEQKIT_GREP_HOST         } from '../../modules/nf-core/seqkit/grep/main'
include { SEQKIT_SEQ                              } from '../../modules/nf-core/seqkit/seq/main'

process PUBLISH_CLEANED_CONTIGS {

    input:
    tuple val(meta), path(cleaned_contigs)

    output:
    tuple val(meta), path("${meta.id}_cleaned.contigs.fa.gz")

    script:
    """
    cp ${cleaned_contigs} ${meta.id}_cleaned.contigs.fa.gz
    """
}

workflow ASSEMBLY_QC {

    take:
    assembly                    // [ val(meta), path(assembly_fasta) ]
    host_reference_genome       // path(reference_genome)

    main:

    // ch_versions = Channel.empty()

    // /* Len filter using the parameter "min_contig_length" */
    // SEQKIT_SEQ(
    //     assembly
    // )

    // ch_versions = ch_versions.mix(SEQKIT_SEQ.out.versions)

    // cleaned_contigs = SEQKIT_SEQ.out.fastx

    // if ( params.remove_human_phix ) {

    //     ch_blast_human_phix_refs = Channel.fromPath( "${params.blast_reference_genomes_folder}/${params.human_phix_blast_index_name}*", checkIfExists: true)
    //         .collect().map {
    //             files -> [ ["id": params.human_phix_blast_index_name], files ]
    //         }

    //     BLAST_BLASTN_HUMAN_PHIX(
    //         SEQKIT_SEQ.out.fastx,
    //         ch_blast_human_phix_refs
    //     )

    //     ch_versions = ch_versions.mix(BLAST_BLASTN_HUMAN_PHIX.out.versions.first())

    //     SEQKIT_GREP_HUMAN_PHIX(
    //         cleaned_contigs.join( BLAST_BLASTN_HUMAN_PHIX.out.txt )
    //     )

    //     cleaned_contigs = SEQKIT_GREP_HUMAN_PHIX.out.filter

    //     ch_versions = ch_versions.mix(SEQKIT_GREP_HUMAN_PHIX.out.versions)
    // }

    // if ( host_reference_genome != null ) {

    //     ch_blast_host_refs = Channel.fromPath( "${params.blast_reference_genomes_folder}/${host_reference_genome}*", checkIfExists: true)
    //         .collect().map {
    //             files -> [ ["id": host_reference_genome], files ]
    //         }
    BLAST_MAKEBLASTDB(host_reference_genome)

    BLAST_BLASTN_HOST(
        assembly,
        BLAST_MAKEBLASTDB.out.db
    )

        // ch_versions = ch_versions.mix(BLAST_BLASTN_HOST.out.versions.first())

    BLAST_BLASTN_HOST.out.txt.view()

    SEQKIT_GREP_HOST(
        assembly.join(BLAST_BLASTN_HOST.out.txt)
    )

        // cleaned_contigs = SEQKIT_GREP_HOST.out.filter

    //     ch_versions = ch_versions.mix(SEQKIT_GREP_HOST.out.versions)
    // }

    // PUBLISH_CLEANED_CONTIGS(
    //     cleaned_contigs
    // )

    // emit:
    // cleaned_contigs = cleaned_contigs
    // versions         = ch_versions
}