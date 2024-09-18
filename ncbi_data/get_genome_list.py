import requests
import json
import os
import time
import logging
import re
from typing import List
import pandas as pd
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from Bio import Entrez
import xml.etree.ElementTree as ET
from .tools import NCBIAssemblyIngress
from .logger import get_logger


class GetGenomeList:

	taxid: str
	outdir: str
	logger: logging.Logger
 
	def __init__(self, outdir):
		self.outdir = outdir
		self.logger = get_logger(name=__name__, level=logging.INFO)

	def main(self, taxid, download_files: False):
		self.taxid = taxid
		self.logger.info(f'Start Processing tax id: {taxid}')
		assembly_accessions = self.get_ncbi_accession_list(taxid=taxid)
		self.makedirs()
		output_csv = self.write_assembly_info_csv(accessions=assembly_accessions, outdir=self.outdir)
		if download_files:
			self.download_genome_data(ftp_df=output_csv, outdir=self.outdir)
   
		return output_csv

	def makedirs(self):
		os.makedirs(self.outdir, exist_ok=True)

	def get_ncbi_accession_list(self, taxid: int):

		assembly_accs = []

		base_url = 'https://api.ncbi.nlm.nih.gov/datasets/v2alpha'
		dataset = f'genome/taxon/{taxid}/dataset_report'
		params = {'filters.refseq_only': 0, 'filters.exclude_paired_reports': True, 'filters.assembly_version': 'current', 'page_size': 1000}#'all'}#, 'tax_exact_match': True}
		r = requests.get(f'{base_url}/{dataset}', params=params)
		JSONContent = r.json()
		content = json.dumps(JSONContent, indent=4, sort_keys=True)
		# print(json.loads(content)['reports'][0]['accession'])

		gcf_count = 0
		gca_count = 0
		total_count = 0
		records = json.loads(content)['reports']
		for record in records:
			if record['accession'].startswith("GCF_"):
				gcf_count += 1
			elif record['accession'].startswith("GCA_"):
				gca_count += 1
			else:
				self.logger.info(f'No GCF or GCA found: {record["accession"]}')

			total_count += 1
			acc = record['accession']
			assembly_accs.append(acc)


		self.logger.info(f'Total #Accessions: {total_count}, #GCF: {gcf_count}, #GCA: {gca_count}')

		return assembly_accs

	# Finds the ids associated with the assembly
	def get_ids(self, term: str):

		ids = []

		esearch_attempt = 1
		read_attemp = 1

		while esearch_attempt <= 3:

			try:

				handle = Entrez.esearch(db="assembly", term=term)
				time.sleep(0.5)
				break

			except HTTPError as err:
				if 500 <= err.code <= 599:
					self.logger.warning("Received error from server %s" % err)
					self.logger.warning("Attempt %i of 3: %s" % (esearch_attempt, term))
					esearch_attempt += 1
					time.sleep(15)
				elif err.code == 429:
					self.logger.warning("Received error from server %s" % err)
					self.logger.warning("Attempt %i of 3: %s" % (esearch_attempt, term))
					esearch_attempt += 1
					time.sleep(15)
				else:
					raise

		while read_attemp <= 3:
			try:
				record = Entrez.read(handle)
				break
			except RuntimeError:
				self.logger.warning("Received runtime error from server")
				self.logger.warning("Read attempt %i of 3" % read_attemp)
				read_attemp += 1
				time.sleep(15)

		ids += record["IdList"]
		handle.close()

		return ids

	def get_raw_assembly_summary(self, id):
		handle = Entrez.esummary(db="assembly", id=id,report="full")
		record = Entrez.read(handle)
		#Return individual fields
		#XML output: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=assembly&id=79781&report=%22full%22
		#return(record['DocumentSummarySet']['DocumentSummary'][0]['AssemblyName']) #This will return the Assembly name
		return record

	def get_assembly_summary_json(self, id):

		attempt = 1

		while attempt <= 3:

			try:

				handle = Entrez.esummary(db="assembly", id=id, report="full")
				time.sleep(0.5)
				break

			except HTTPError as err:

				if 500 <= err.code <= 599:
					self.logger.warning("Received error from server %s" % err)
					self.logger.warning("Attempt %i of 3: %s" % (attempt, id))
					attempt += 1
					time.sleep(15)
				elif err.code == 429:
					self.logger.warning("Received error from server %s" % err)
					self.logger.warning("Attempt %i of 3: %s" % (attempt, id))
					attempt += 1
					time.sleep(15)
				else:
					raise

		record = Entrez.read(handle)
		# Convert raw output to json
		content = json.dumps(record, sort_keys=True, indent=4, separators=(',', ': '))

		handle.close()

		return json.loads(content)

	def get_sra_uids(self, biosample_acc: str):

		ids = []
		attempt = 1

		while attempt <= 3:
			try:
				handle = Entrez.esearch(db="sra", term=biosample_acc)
				time.sleep(0.5)
				break

			except HTTPError as err:

				if 500 <= err.code <= 599:
					self.logger.warning("Received error from server %s" % err)
					self.logger.warning("Attempt %i of 3: %s" % (attempt, biosample_acc))
					attempt += 1
					time.sleep(15)
				elif err.code == 429:
					self.logger.warning("Received error from server %s" % err)
					self.logger.warning("Attempt %i of 3: %s" % (attempt, biosample_acc))
					attempt += 1
					time.sleep(15)
				else:
					raise

		record = Entrez.read(handle)
		ids += record["IdList"]

		handle.close()

		return ids

	def get_sra_info(self, sra_uids):

		sra_ids = []
		platforms = []

		for sra_uid in sra_uids:
			attempt = 1

			while attempt <= 3:
				try:
					handle = Entrez.esummary(db="sra", id=sra_uid)
					time.sleep(0.5)
					break

				except HTTPError as err:

					if 500 <= err.code <= 599:
						self.logger.warning("Received error from server %s" % err)
						self.logger.warning("Attempt %i of 3: %s" % (attempt, sra_uid))
						attempt += 1
						time.sleep(15)
					elif err.code == 429:
						self.logger.warning("Received error from server %s" % err)
						self.logger.warning("Attempt %i of 3: %s" % (attempt, sra_uid))
						attempt += 1
						time.sleep(15)
					else:
						raise

			root = ET.fromstring(handle.read())

			for child in root.iter('Item'):

				if not child.text:
					continue

				if child.attrib['Name'] == 'Runs':
					runs = re.findall('<Run (.*?)/>', child.text)
					sra_ids += [re.search('acc="(.*?)"', x).group(1) for x in runs]

				elif child.attrib['Name'] == 'ExpXml':

					platform_items = re.findall('<Platform .*>(.*)</Platform>', child.text)

					if len(platform_items) > 0:

						platforms.append(platform_items[0])

		handle.close()

		return ";".join(sra_ids), ";".join(platforms)

	def write_assembly_info_csv(self, accessions: List[str], outdir: str):
		output_csv = f'{outdir}/ncbi_assembly_report_{self.taxid}.csv'

		with open(output_csv, 'w') as o:

			o.write(','.join(['AssemblyAccession', 'SRA', 'Organism', 'SpeciesName', 'Taxid', 'AssemblyStatus', 'BioSampleAccn', 'BioSampleId', 'BioprojectAccn',
							  'Coverage', 'ContigN50', 'contig_count', 'contig_l50', 'scaffold_n50', 'scaffold_count', 'scaffold_l50', 'total_length',
							  'RefSeq_category', 'PartialGenomeRepresentation', 'full-genome-representation', 'genbank_has_annotation', 'refseq_has_annotation', 'has_annotation',
							  'WGS', 'Platform', 'FtpPath_GenBank', 'FtpPath_RefSeq', 'LastMajorReleaseAccession', 'LastUpdateDate', 'SubmitterOrganization']) + '\n')

			for i, accession in enumerate(accessions):

				ids = self.get_ids(accession)

				for id in ids:

					self.logger.info(f'Writing assembly info: {id}, {accession}')

					assembly_summary_dict = self.get_assembly_summary_json(id)['DocumentSummarySet']['DocumentSummary'][0]
					assembly_acc = assembly_summary_dict['AssemblyAccession']
					biosample_id = assembly_summary_dict['BioSampleId']
					assembly_status = assembly_summary_dict['AssemblyStatus']
					biosample_accn = assembly_summary_dict['BioSampleAccn']
					n50 = assembly_summary_dict['ContigN50']
					coverage = assembly_summary_dict['Coverage']
					fromtype = assembly_summary_dict['FromType']
					ftp_genbank = assembly_summary_dict['FtpPath_GenBank']
					ftp_refseq = assembly_summary_dict['FtpPath_RefSeq']
					lastmajoracc = assembly_summary_dict['LastMajorReleaseAccession']
					lastupdate = assembly_summary_dict['LastUpdateDate']
					organism = assembly_summary_dict['Organism']
					partial = assembly_summary_dict['PartialGenomeRepresentation']
					species = assembly_summary_dict['SpeciesName']
					taxid = assembly_summary_dict['Taxid']
					submitter = assembly_summary_dict['SubmitterOrganization']
					refseq_category = assembly_summary_dict['RefSeq_category']
					if assembly_summary_dict.get('GB_BioProjects'):
						bioprpject = assembly_summary_dict['GB_BioProjects'][0]['BioprojectAccn']
					else:
						bioprpject = ''
					property_dict = {'full-genome-representation': 'false',
									 'genbank_has_annotation': 'false',
									 'refseq_has_annotation': 'false',
									 'wgs': 'false',
									 'has_annotation': 'false'}
					propertylist = assembly_summary_dict['PropertyList']

					for p in propertylist:

						if property_dict.get(p):
							property_dict[p] = 'true'

					seq_stats = {'contig_count': 'na', 'contig_l50': 'na',
								 'scaffold_count': 'na', 'scaffold_l50': 'na', 'scaffold_n50': 'na',
								 'total_length': 'na'}

					meta = assembly_summary_dict['Meta']
					soup = BeautifulSoup(meta, 'xml')
					stats = soup.find('Stats')

					for stat in stats.find_all('Stat'):
						if seq_stats.get(stat['category']):
							if stat['sequence_tag'] == 'all':
								seq_stats[stat['category']] = stat.text

					if biosample_accn:
						sra_uids = self.get_sra_uids(biosample_accn)
					else:
						sra_uids = []

					if len(sra_uids) > 0:
						sra, platform = self.get_sra_info(sra_uids)
					else:
						sra, platform = ['', '']

					results = [assembly_acc, sra, organism, species, taxid, assembly_status, biosample_accn, biosample_id, bioprpject,
							   coverage, n50, seq_stats['contig_count'], seq_stats['contig_l50'], seq_stats['scaffold_n50'], seq_stats['scaffold_count'], seq_stats['scaffold_l50'], seq_stats['total_length'],
							   refseq_category, partial, property_dict['full-genome-representation'], property_dict['genbank_has_annotation'], property_dict['refseq_has_annotation'], property_dict['has_annotation'],
							   property_dict['wgs'], platform, ftp_genbank, ftp_refseq, lastmajoracc, lastupdate, submitter]
					o.write(','.join([str(x) for x in results]) + '\n')

				if i != 0 and i % 100 == 0:
					time.sleep(15)

		return output_csv

	def get_accession(self, fpath: str) -> str:
		accession = '_'.join(os.path.basename(fpath).split('_')[:2])
		return accession

	def get_ftp_paths(self, dataframe: str) -> List[str]:

		df = pd.read_csv(dataframe)

		if len(df.columns) == 1:
			df = pd.read_table(dataframe, names=['ftp'], header=None, sep="\t")
			ftppaths = [x for x in df['ftp'].tolist() if x.startswith('ftp://')]

		else:
			df_annot = df[df['has_annotation'] == True]

			ftppaths = []

			for i, row in df_annot.iterrows():
				if str(row['FtpPath_RefSeq']) != 'nan':
					ftppaths.append(row['FtpPath_RefSeq'])

				elif str(row['FtpPath_GenBank']) != 'nan':
					ftppaths.append(row['FtpPath_GenBank'])
				else:
					self.logger.warning(f'{row["AssemblyAccession"]} genome data not found.')

		return ftppaths

	def download_genome_data(self, ftp_df: str, outdir: str, file_types: List[str] = ['gbk', 'fna', 'faa', 'gff', 'transcript_fna']):

		ftppaths = self.get_ftp_paths(ftp_df)
		accession_list = []
		dst_counts = []
		outpath = f'{outdir}/ncbi_genome_download_summary_{self.taxid}.csv'
		o = open(outpath, 'w')
		o.write('accession,downloaded_files\n')

		for ftppath in ftppaths:
			self.logger.info(f'Downloading files: {ftppath}')
			dstpaths = NCBIAssemblyIngress.download_from_ftp(ftppaths=[ftppath], inquiries=file_types, dstdir=outdir)
			dst_num = len(list(filter(None, dstpaths)))
			dst_counts.append(dst_num)
			accession = self.get_accession(fpath=dstpaths[0])
   
			o.write(f'{accession},{dst_num}\n')

		return outpath

