#!/usr/bin/env python3

import argparse
import logging
import os
import urllib
import csv

import boto3
from botocore import UNSIGNED
from botocore.config import Config
import requests
from retry import retry

DOWNLOAD_DIR = "."

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

def main(target_accession):

    handle_fasta_download(target_accession)
    logging.info(f"Finished")

def handle_fasta_download(accession):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        logging.debug(f"Directory {DOWNLOAD_DIR} is created")

    outpath = os.path.join(DOWNLOAD_DIR, f'{accession}.fa.gz')
    if os.path.exists(outpath) and os.path.getsize(outpath) > 20:
        logging.info(f"File {outpath} already exists, skipping download.")
        return
    download_from_ENA_FIRE(accession, outpath)

@retry(tries=5, delay=15, backoff=1.5) 
def download_from_ENA_FIRE(accession: str, outpath: str, analysis_ftp_field="generated_ftp") -> str:
    url = get_fasta_url(accession, analysis_ftp_field=analysis_ftp_field)
    if not url:
        logging.debug(f"{accession} URL is empty for accession, ftp field: {analysis_ftp_field}")
        return None
        # raise ValueError(f"URL is empty, ftp field: {analysis_ftp_field}")
    logging.debug(f"Download {accession} from ENA FIRE using URL {url}")

    fire_endpoint = "http://hl.fire.sdo.ebi.ac.uk"
    fire_ena_bucket = "era-public"
    fire_path = url.replace("ftp.sra.ebi.ac.uk/vol1/", "")
    s3 = boto3.client("s3", endpoint_url=fire_endpoint, config=Config(signature_version=UNSIGNED))
    s3.download_file(fire_ena_bucket, fire_path, outpath)
    # 20 bytes is a size of an empty fa.gz
    if os.path.exists(outpath) and os.path.getsize(outpath) > 20:
        logging.debug(f"Successful. File saved to {outpath}")
        return outpath
    logging.debug(f"Downloaded file {outpath} has zero size. Removing the file.")
    os.remove(outpath)
    return None

def get_fasta_url(accession, analysis_ftp_field="generated_ftp"):
    api_endpoint = 'https://www.ebi.ac.uk/ena/portal/api/search'
    accession_type = 'analysis' if accession.startswith("ERZ") else 'wgs_set'
    query = {
        "wgs_set": {
            "result": "wgs_set",
            "query": f'wgs_set="{accession}"',
            "fields": "set_fasta_ftp",
            "format": "tsv",
        },
        "analysis": {
            "result": "analysis",
            "query": f'analysis_accession="{accession}"',
            "fields": analysis_ftp_field,
            "format": "tsv",
        },
    }

    response = run_request(query[accession_type], api_endpoint)
    lines = response.text.splitlines()
    reader = csv.DictReader(lines, delimiter="\t")
    for row in reader:
        field_name = query[accession_type]["fields"]
        file_url = row[field_name].split(";")[0]  # Split to take the first FTP link if multiple
        return file_url
    return None # no information about this accession in ENA

@retry(tries=5, delay=15, backoff=1.5)
def run_request(query, api_endpoint):
    request = requests.get(api_endpoint, params=urllib.parse.urlencode(query))
    request.raise_for_status()
    return request

def parse_args():
    parser = argparse.ArgumentParser(description='Download macro organism genomes for a primary metagenome from ASG project.')
    parser.add_argument('target_accession', help='Primary metagenome accession')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    main(args.target_accession)