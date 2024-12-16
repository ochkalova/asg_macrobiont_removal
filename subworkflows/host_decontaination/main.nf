include { MINIMAP2_ALIGN   } from '../../modules/nf-core/minimap2/align/main'
include { FIND_ROOT_GENOME } from '../../modules/local/find_root_genome/main'
include { DOWNLOAD_ERZ } from '../../modules/local/download_erz/main'

workflow HOST_DECONTAMINATION {
    take:
    assembly                    // [ val(accession) ]

    main:
    FIND_ROOT_GENOME(assembly)

    FIND_ROOT_GENOME.out.root_organism_fasta
        .map { filepath ->
            [[id: filepath.getBaseName(2)], filepath]
        }
        .set { reference }

    DOWNLOAD_ERZ(assembly)

    DOWNLOAD_ERZ.out.metagenome
        .map{ accession, fasta ->
            [[id: accession], fasta]
        }
        .set { metagenome }

    MINIMAP2_ALIGN(metagenome, reference, "asg","fasta", true, false, false, false )

    emit:
    decontaminated_metagenomes = MINIMAP2_ALIGN.out.filtered_output
}
