include { MINIMAP2_ALIGN              } from '../../modules/nf-core/minimap2/align/main'
include { FETCH_ROOT_GENOME           } from '../../modules/local/fetch_root_genome/main'
include { DOWNLOAD_PRIMARY_METAGENOME } from '../../modules/local/download_primary_metagenome/main'

workflow HOST_DECONTAMINATION {
    take:
    metagenome         // [ val(id), path(metagenome_fasta) ]
    filtered_genome    // [ val(id), path(assembly_fasta) ]

    main:
    element = filtered_genome.map { tuple -> tuple[0] }
    element.view()
    
    if ( filtered_genome.map { tuple -> tuple[0] } == "ASG" ) {
        asg_metagenome2reference = FETCH_ROOT_GENOME(metagenome.map { tuple -> tuple[0] }).out.root_organism_fasta
        
        metagenome
            .join(asg_metagenome2reference)
            .multiMap { metagenome_id, metagenome_file, root_org_file ->
                metagenome: [[id: metagenome_id], metagenome_file]
                reference: [[id: root_org_file.getBaseName(3)], root_org_file]
            }
            .set { for_alignment_ch }

        MINIMAP2_ALIGN(for_alignment_ch.metagenome, for_alignment_ch.reference, "asg", "fasta", true, false, false, false )
    }
    else {
        metagenome = metagenome.map { [[id: it[0]], it[1]] }
        filtered_genome = filtered_genome.map { [[id: it[0]], it[1]] }
        MINIMAP2_ALIGN(metagenome, filtered_genome, "asg", "fasta", true, false, false, false )
    }

    // if ( !filtered_genome[1] ) 
    //     DOWNLOAD_PRIMARY_METAGENOME(metagenome[0])

    // DOWNLOAD_PRIMARY_METAGENOME.out.metagenome
    //     .join(FETCH_ROOT_GENOME.out.root_organism_fasta)
    //     .multiMap { metagenome_id, metagenome_file, root_org_file ->
    //         metagenome: [[id: metagenome_id], metagenome_file]
    //         reference: [[id: root_org_file.getBaseName(3)], root_org_file]
    //     }
    //     .set { for_alignment_ch }

    emit:
    decontaminated_metagenomes = MINIMAP2_ALIGN.out.filtered_output

}
