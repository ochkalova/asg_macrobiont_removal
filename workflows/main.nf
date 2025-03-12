include { HOST_DECONTAMINATION } from "../subworkflows/host_decontaination/main.nf"

workflow PIPELINE {

    input_accessions_ch = Channel.fromPath(params.input_file).splitCsv()
    
    HOST_DECONTAMINATION(input_accessions_ch)

}