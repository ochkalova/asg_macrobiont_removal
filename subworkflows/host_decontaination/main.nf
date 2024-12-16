include { MINIMAP2_ALIGN   } from '../../modules/nf-core/minimap2/align/main'
include { FIND_ROOT_GENOME } from '../../modules/local/find_root_genome/main'

workflow HOST_DECONTAMINATION {
    take:
    assembly                    // [ val(meta), path(assembly_fasta) ]

    main:
    FIND_ROOT_GENOME(assembly)

    // FIND_ROOT_GENOME.out.root_organism_fasta.view()

    FIND_ROOT_GENOME.out.root_organism_fasta
        .map { filepath ->
            [[id: filepath.getBaseName(2)], filepath]
        }
        .set { reference }

    MINIMAP2_ALIGN(assembly, reference, "asg","fasta", true, false, false, false )

    emit:
    decontaminated_metagenomes = MINIMAP2_ALIGN.out.filtered_output
}
