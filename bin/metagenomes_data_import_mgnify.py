#!/usr/bin/env python3

import argparse
import logging
import os

import requests
from retry import retry

ASG_API_URL = "https://portal.aquaticsymbiosisgenomics.org/api/data_portal_test"
PAGE_LIMIT = 10
DOWNLOAD_DIR = "."

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

def main(target_accession):
    logging.info(f"Collecting genome information from ASG portal")
    
    # Collect ASG portal data
    data = collect_data_from_asg_portal()
    
    # Parse the collected data and collect relevant genome IDs
    host2metagenome = parse_records(data)
    
    logging.info(f"Fetching root organism assemblies for metagenome: {target_accession}")
    # Find genomes related to the target accession
    genomes_for_download = host2metagenome[(target_accession,)]
    
    # Download the genomes
    if genomes_for_download:
        logging.info(f"Found {len(genomes_for_download)} genomes to download: {','.join(genomes_for_download)}")
        handle_fasta_download(genomes_for_download)
    else:
        logging.warning(f"No genomes found for target accession {target_accession}")
    logging.info(f"Finished")

def collect_data_from_asg_portal():
    """Collect data from the ASG portal using paginated requests."""
    offset = 0
    data = []
    
    while True:
        url = f"{ASG_API_URL}?offset={offset}&limit={PAGE_LIMIT}"
        response = requests.get(url).json()
        data.extend(response["results"])
        offset += PAGE_LIMIT
        
        if offset >= response["count"]:
            break  # All data collected
    
    logging.info(f"Collected {len(data)} records from the ASG portal")
    return data

def parse_records(data):
    """Parse collected records to create host_genome-to-primary_assembly mapping."""
    host2metagenome = {}
    
    for i, record in enumerate(data):
        logging.debug(f"Parsing record {i + 1}/{len(data)}")
        source_record = record.get("_source", {})
        
        if source_record.get("assemblies") and source_record.get("metagenomes_analyses"):
            host_assemblies = [
                assembly["accession"] 
                for assembly in source_record["assemblies"] if not "alternate" in assembly["assembly_name"]]
            primary_metagenomes = tuple([
                analysis["analysis_accession"] 
                for analysis in source_record["metagenomes_analyses"] 
                if analysis["assembly_type"] == "primary metagenome"
                ])
            host2metagenome[primary_metagenomes] = host_assemblies
    
    logging.info(f"Parsed {len(host2metagenome)} genome sets from the records")
    return host2metagenome

def handle_fasta_download(accessions):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        logging.debug(f"Directory {DOWNLOAD_DIR} is created")
    for accession in accessions:
        outpath = os.path.join(DOWNLOAD_DIR, f'{accession}.fa.gz')
        if os.path.exists(outpath) and os.path.getsize(outpath) > 20:
            logging.info(f"File {outpath} already exists, skipping download.")
            return
        download_from_ENA_API(accession, outpath)
        
@retry(tries=7, delay=15, backoff=2) 
def download_from_ENA_API(accession: str, outpath: str) -> str:
    api_endpoint = f"https://www.ebi.ac.uk/ena/browser/api/fasta/{accession}"
    logging.debug(f"Download {accession} from ENA API using URL {api_endpoint}")
    query = {
        'download': 'true',
        'gzip': 'true'
    }
    response = requests.get(api_endpoint, params=query)
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
    parser = argparse.ArgumentParser(description='Download macro organism genomes for a primary metagenome from ASG project.')
    parser.add_argument('target_accession', help='Primary metagenome accession')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args.target_accession)