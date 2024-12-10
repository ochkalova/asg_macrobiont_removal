import requests
import csv
from lxml import etree

ASG_URL = "https://portal.aquaticsymbiosisgenomics.org/api/data_portal_test"
ENA_URL = "https://www.ebi.ac.uk/ena"
RESULTS = []

def main():
    offset = 0
    data = list()

    # First request
    response = requests.get(f"{ASG_URL}?offset={offset}&limit=10").json()
    while offset + 10 <= response["count"]:
        data.extend(response["results"])
        offset += 10
        response = requests.get(f"{ASG_URL}?offset={offset}&limit=10").json()
    # Last request to collect remaining records
    response = requests.get(f"{ASG_URL}?offset={offset}&limit=10").json()
    data.extend(response["results"])

    for i, record in enumerate(data):
        print(
            f"Processing data: {round(i / len(data) * 100, 2)}%\r", end="", flush=True
        )
        record = record["_source"]
        if ("assemblies" in record and len(record["assemblies"]) > 0) and ("metagenomes_assemblies" in record and len(record["metagenomes_assemblies"]) > 0):
            RESULTS.append(collect_analyses_ids(record))


def collect_analyses_ids(record):
    """
    Collect all analyses IDs (ERZs) from ES record.
    record: ES entry
    """
    tmp = dict()
    tmp["organism_name"] = record["organism"]
    tmp["root_organism_assembly"] = [assembly["accession"] for assembly in record["assemblies"]]
    for assmbl in record["metagenomes_assemblies"]:
        tmp2 = {assmbl["accession"]: []}
        response = requests.get(
            f"{ENA_URL}/browser/api/xml/{assmbl['accession']}"
        )
        root = etree.fromstring(response.content)
        project_id = (
            root.find("ASSEMBLY")
            .find("STUDY_REF")
            .find("IDENTIFIERS")
            .find("PRIMARY_ID")
            .text
        )
        response = requests.get(
            f"https://www.ebi.ac.uk/ena/portal/api/search?result=analysis&"
            f"query=analysis_type=sequence_assembly%20AND%20assembly_type%3D%22primary%20metagenome%22%20AND%20study_accession%3D%22{project_id}%22&"
            f"format=json&fields=analysis_accession"
        ).json()
        
        erz_list = [erz["analysis_accession"] for erz in response]
        tmp2[assmbl["accession"]] = erz_list
        tmp["metagenomes_assemblies"] = tmp2
    return tmp


def write_tsv(output_file, results):
    with open(output_file, "w", newline="") as tsvfile:
        writer = csv.writer(tsvfile, delimiter='\t')
        # Write the header
        writer.writerow(["Organism Name", "Root organism Accession", "Metagenome Accessions"])
        
        # Write the data rows
        for result in results:
            organism_name = result["organism_name"]
            root_genomes = ",".join(result["root_organism_assembly"])
            metagenomes = ",".join([result["metagenomes_assemblies"][genome][0] for genome in result["metagenomes_assemblies"]])

            writer.writerow([organism_name, root_genomes, metagenomes])


if __name__ == "__main__":
    main()
    write_tsv("asg_mgnify_assemblies.tsv", RESULTS)
