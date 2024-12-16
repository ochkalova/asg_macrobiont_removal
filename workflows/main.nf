include { HOST_DECONTAMINATION } from "../subworkflows/host_decontaination/main.nf"
include { ASSEMBLY_QC } from "../subworkflows/assembly_qc/main.nf"

workflow PIPELINE {

    HOST_DECONTAMINATION([[id: params.input_accession], params.input_fasta])
    
    ASSEMBLY_QC(
            [[id: params.input_accession], params.input_fasta],
            [[id: "asg"], params.host_reference_genome]
            )

}