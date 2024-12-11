#!/usr/bin/env python3

import argparse
import logging
import os
import urllib

import requests
from lxml import etree
from retry import retry

ASG_API_URL = "https://portal.aquaticsymbiosisgenomics.org/api/data_portal_test"
ENA_URL = "https://www.ebi.ac.uk/ena"
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
    results = parse_records(data)
    
    # Find genomes related to the target accession
    genomes_for_download = results[(target_accession,)]
    
    # Download the genomes
    if genomes_for_download:
        logging.info(f"Found {len(genomes_for_download)} genomes to download")
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
    """Parse collected records to extract relevant genome information."""
    results = {}
    
    for i, record in enumerate(data):
        logging.debug(f"Parsing record {i + 1}/{len(data)}")
        source_record = record.get("_source", {})
        
        if source_record.get("assemblies") and source_record.get("metagenomes_assemblies"):
            analyses_ids = collect_analyses_ids(source_record)
            results.update(analyses_ids)
    
    logging.info(f"Parsed {len(results)} genome sets from the records")
    return results

def collect_analyses_ids(record):
    """Collect analysis IDs (ERZs) from a single record."""
    host_assemblies = [assembly["accession"] for assembly in record["assemblies"]]
    primary_metagenomes = set()
    
    for metagenome in record["metagenomes_assemblies"]:
        project_id = get_project_id_from_ena(metagenome["accession"])
        primary_metagenomes.update(get_primary_assemblies_from_project_id(project_id))
    
    return {tuple(primary_metagenomes): host_assemblies}

def get_project_id_from_ena(accession):
    """Retrieve project ID from ENA using accession."""
    url = f"{ENA_URL}/browser/api/xml/{accession}"
    response = requests.get(url)
    
    try:
        root = etree.fromstring(response.content)
        project_id = (
            root.find("ASSEMBLY")
            .find("STUDY_REF")
            .find("IDENTIFIERS")
            .find("PRIMARY_ID")
            .text
        )
        return project_id
    except etree.XMLSyntaxError as e:
        logging.error(f"Error parsing XML for accession {accession}: {e}")
        raise

def get_primary_assemblies_from_project_id(accession):
    api_endpoint = "https://www.ebi.ac.uk/ena/portal/api/search"
    query = {
        'result': 'analysis',
        'query': f'analysis_type=sequence_assembly AND assembly_type="primary metagenome" AND study_accession="{accession}"',
        'format': 'json',
        'fields': 'analysis_accession'
    }
    response = requests.get(api_endpoint, params=urllib.parse.urlencode(query))
    primary_assemblies = {record["analysis_accession"] for record in response.json()}
    
    logging.debug(f"Found {len(primary_assemblies)} 'primary assembly' type analysis accessions for project {accession}")
    return primary_assemblies

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
    parser = argparse.ArgumentParser(description='Download macro organism genomes for a primary metagenome from ASG project.')
    parser.add_argument('target_accession', help='Primary metagenome accession')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args.target_accession)