include { MINIMAP2_ALIGN   } from '../../modules/nf-core/minimap2/align/main'
include { FIND_ROOT_GENOME } from '../../modules/local/find_root_genome/main'
include { DOWNLOAD_ERZ } from '../../modules/local/download_erz/main'

workflow HOST_DECONTAMINATION {
    take:
    metagenome_accession  // [ val(accession)]

    main:
    FIND_ROOT_GENOME(metagenome_accession)

    FIND_ROOT_GENOME.out.root_organism_fasta
        .map { filepath ->
            [[id: filepath.getBaseName(3)], filepath]
        }
        .set { reference }

    DOWNLOAD_ERZ(metagenome_accession)

    DOWNLOAD_ERZ.out.metagenome
        .map{ accession, fasta ->
            [[id: accession], fasta]
        }
        .set { metagenome }

    MINIMAP2_ALIGN(metagenome, reference, "asg", "fasta", true, false, false, false )

    emit:
    metagenomes = metagenome
    references = reference
    decontaminated_metagenomes = MINIMAP2_ALIGN.out.filtered_output

}
