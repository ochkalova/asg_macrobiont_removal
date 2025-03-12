include { MINIMAP2_ALIGN   } from '../../modules/nf-core/minimap2/align/main'
include { FIND_ROOT_GENOME } from '../../modules/local/find_root_genome/main'
include { DOWNLOAD_ERZ     } from '../../modules/local/download_erz/main'
include { FILTER_PAF       } from '../../modules/local/filter_paf/main'
include { SEQKIT_GREP      } from '../../modules/nf-core/seqkit/grep/main'

workflow HOST_DECONTAMINATION {
    take:
    metagenome_accession  // [ val(accession)]

    main:
    FIND_ROOT_GENOME(metagenome_accession)

    DOWNLOAD_ERZ(metagenome_accession)

    DOWNLOAD_ERZ.out.metagenome
        .join(FIND_ROOT_GENOME.out.root_organism_fasta)
        .multiMap { metagenome_id, metagenome_file, root_org_file ->
            metagenome: [[id: metagenome_id], metagenome_file]
            reference: [[id: root_org_file.getBaseName(3)], root_org_file]
        }
        .set { for_alignment_ch }

    MINIMAP2_ALIGN(
        for_alignment_ch.metagenome, 
        for_alignment_ch.reference, 
        true, 
        false, 
        false, 
        false)

    FILTER_PAF(MINIMAP2_ALIGN.out.paf)

    SEQKIT_GREP(for_alignment_ch.metagenome.join(FILTER_PAF.out.unmapped_contigs_txt))

    emit:
    decontaminated_metagenomes = SEQKIT_GREP.out.filter

}
