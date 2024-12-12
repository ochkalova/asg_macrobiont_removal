include { HOST_DECONTAMINATION } from "../subworkflows/host_decontaination/main.nf"

workflow PIPELINE {

    HOST_DECONTAMINATION([[id: params.input_accession], params.input_fasta])
    
}