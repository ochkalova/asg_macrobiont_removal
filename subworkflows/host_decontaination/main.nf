include { MINIMAP2_ALIGN              } from '../../modules/nf-core/minimap2/align/main'
include { FETCH_ROOT_GENOME            } from '../../modules/local/fetch_root_genome/main'
include { DOWNLOAD_PRIMARY_METAGENOME } from '../../modules/local/download_primary_metagenome/main'

workflow HOST_DECONTAMINATION {
    take:
    metagenome_accession  // [ val(accession)]

    main:
    FETCH_ROOT_GENOME(metagenome_accession)

    DOWNLOAD_PRIMARY_METAGENOME(metagenome_accession)

    DOWNLOAD_PRIMARY_METAGENOME.out.metagenome
        .join(FETCH_ROOT_GENOME.out.root_organism_fasta)
        .multiMap { metagenome_id, metagenome_file, root_org_file ->
            metagenome: [[id: metagenome_id], metagenome_file]
            reference: [[id: root_org_file.getBaseName(3)], root_org_file]
        }
        .set { for_alignment_ch }

    MINIMAP2_ALIGN(for_alignment_ch.metagenome, for_alignment_ch.reference, "asg", "fasta", true, false, false, false )

    emit:
    metagenomes = for_alignment_ch.metagenome
    references = for_alignment_ch.reference
    decontaminated_metagenomes = MINIMAP2_ALIGN.out.filtered_output

}
