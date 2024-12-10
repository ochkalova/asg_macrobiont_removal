import requests
import json
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
        if "assemblies" in record["_source"] and len(record["_source"]["assemblies"]) > 0:
            RESULTS.append(collect_analyses_ids(record["_source"]))


def collect_analyses_ids(record):
    """
    Collect all analyses IDs (ERZs) from ES record.
    record: ES entry
    """
    tmp = dict()
    tmp["organism_name"] = record["organism"]
    for assembly_type in [
        "assemblies",
        "metagenomes_assemblies",
        "symbionts_assemblies",
    ]:
        tmp[assembly_type] = []
        if assembly_type in record and len(record[assembly_type]) > 0:
            for assmbl in record[assembly_type]:
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
                
                for erz in response:
                    tmp2[assmbl["accession"]].append(erz["analysis_accession"])
            tmp[assembly_type].append(tmp2)
    return tmp


if __name__ == "__main__":
    main()
    with open("asg_mgnify_assemblies.json", "w") as outfile:
        json.dump(RESULTS, outfile)
