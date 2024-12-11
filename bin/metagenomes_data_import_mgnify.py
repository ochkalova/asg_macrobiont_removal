#!/usr/bin/env python3

import argparse
from lxml import etree
import logging
import os
import urllib

from retry import retry
import requests

ASG_URL = "https://portal.aquaticsymbiosisgenomics.org/api/data_portal_test"
ENA_URL = "https://www.ebi.ac.uk/ena"
RESULTS = {}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

def collect_data_from_asg_portal():
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
    return data

def main(target_accession):
    logging.info('Collecting info about deposited genomes in ASG portal')
    data = collect_data_from_asg_portal()

    logging.info('Parsing collected data')
    for i, record in enumerate(data):
        print(
            f"Processing data: {round(i / len(data) * 100, 2)}%\r", end="", flush=True
        )
        record = record["_source"]
        if ("assemblies" in record and len(record["assemblies"]) > 0) and ("metagenomes_assemblies" in record and len(record["metagenomes_assemblies"]) > 0):
            RESULTS.update(collect_analyses_ids(record))
    
    genomes_for_download = [
        root_org_genome
        for root_org_genome, accessions_set in RESULTS.items()
        if target_accession in accessions_set
    ]
    genomes_for_download = [
        accession
        for accessions_set in genomes_for_download
        for accession in accessions_set
    ]
    logging.info('Starting genome downloading')
    for genome in genomes_for_download:
        handle_fasta_download(genome, download_folder=".")


def collect_analyses_ids(record):
    """
    Collect all analyses IDs (ERZs) from ES record.
    record: ES entry
    """
    root_assemblies = tuple(assembly["accession"] for assembly in record["assemblies"])
    tmp = {}
    tmp[root_assemblies] = set()
    for assmbl in record["metagenomes_assemblies"]:
        # Identify project ID
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
        # Identify related primary assemblies
        response = requests.get(
            f"https://www.ebi.ac.uk/ena/portal/api/search?result=analysis&"
            f"query=analysis_type=sequence_assembly%20AND%20assembly_type%3D%22primary%20metagenome%22%20AND%20study_accession%3D%22{project_id}%22&"
            f"format=json&fields=analysis_accession"
        ).json()
        
        erz_list = set([line["analysis_accession"] for line in response])
        tmp[root_assemblies].update(erz_list)
    return tmp


def handle_fasta_download(accession, download_folder):
    outpath = os.path.join(download_folder, f'{accession}.fa.gz')

    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        logging.debug(f"Directory {download_folder} is created")
    
    download_from_ENA_API(accession, outpath)

@retry(tries=7, delay=15, backoff=2) 
def download_from_ENA_API(accession: str, outpath: str) -> str:
    api_endpoint = f"https://www.ebi.ac.uk/ena/browser/api/fasta/{accession}"
    logging.debug(f"Download {accession} from ENA API using URL {api_endpoint}")
    query = {
        'download': 'true',
        'gzip': 'true'
    }
    response = requests.get(api_endpoint, params=urllib.parse.urlencode(query))
    response.raise_for_status()
    
    with open(outpath, 'wb') as out:
        out.write(response.content)
    # 20 bytes is a size of an empty fa.gz
    if os.path.exists(outpath) and os.path.getsize(outpath) > 20:
        logging.debug(f"Successful. File saved to {outpath}")
        return outpath
    logging.debug(f"Downloaded file {outpath} has zero size. Removing the file.")
    os.remove(outpath)
    raise ValueError(f"Downloaded file {outpath} has zero size")


def parse_args():
    parser = argparse.ArgumentParser(description='Find and download macro organism (host) genome assemblies for a primary metagenome from ASG project')
    parser.add_argument('target_accession',
                        help='Primary metagenome accession')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    main(args.target_accession)
