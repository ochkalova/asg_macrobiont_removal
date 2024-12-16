include { HOST_DECONTAMINATION } from "../subworkflows/host_decontaination/main.nf"
include { ASSEMBLY_QC } from "../subworkflows/assembly_qc/main.nf"

workflow PIPELINE {

    input_accessions_ch = Channel.fromPath(params.input_file).splitCsv()
    
    HOST_DECONTAMINATION(input_accessions_ch)
    
    // ASSEMBLY_QC(
    //         [[id: params.input_accession], params.input_fasta],
    //         [params.host_reference_genome]
    //         )

}