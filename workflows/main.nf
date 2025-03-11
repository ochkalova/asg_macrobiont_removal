include { HOST_DECONTAMINATION } from "../subworkflows/host_decontaination/main.nf"
include { samplesheetToList    } from 'plugin/nf-schema'

workflow PIPELINE {

    samplesheet_ch = Channel
        .fromList(samplesheetToList(params.input, "${projectDir}/assets/schema_input.json"))
    
    samplesheet_ch.view()
    decontamination_input_ch = samplesheet_ch
        .multiMap { id_1, metagenome, id_2, filtered_genome ->
            metagenome: [ id_1, metagenome ]
            filtered_genome: [ id_2, filtered_genome ]
        }
    // decontamination_input_ch.metagenome.view()
    // decontamination_input_ch.filtered_genome.view()

    HOST_DECONTAMINATION(
        decontamination_input_ch.metagenome, 
        decontamination_input_ch.filtered_genome
        )

}