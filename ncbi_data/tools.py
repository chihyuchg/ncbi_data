import os
import subprocess
import logging
import shutil
import urllib.request
from typing import List, Dict, Union, Optional

logger = logging.getLogger(__name__)


def call(cmd: str, log_cmd: bool = True):
	if log_cmd:
		logger.debug(f'CMD: {cmd}')

	try:
		subprocess.check_call(cmd, shell=True)

	except Exception as inst:
		logger.error(inst)


def curl_ftp(src, dst):
	print(f'curl {src} -o {dst}')
	call(f'curl {src} -o {dst}')


def ftp_download(src, dst):
	try:
		with urllib.request.urlopen(src) as response:
			with open(dst, "wb") as o:
				shutil.copyfileobj(response, o)
	except Exception as inst:
		logger.error(inst)


def gunzip(fpath):
	assert fpath.endwith('.gz')
	call(f'gzip -d {fpath}')
	return fpath[:-3]


def get_accession(fpath: str) -> str:
	accession = '_'.join(os.path.basename(fpath).split('_')[:2])
	return accession


RETURN_TYPES = Union[Optional[str], List[Optional[str]]]


class NCBIAssemblyIngress:

	@classmethod
	def download_from_ftp(cls,
	                ftppaths: Union[str, List[str]],
	                inquiries: Union[str, List[str]],
	                dstdir: str = '.') -> RETURN_TYPES:
		"""

		Args:
			ftppaths: NCBI Assembly ftp paths.
			inquery: {'gbk', 'fna', 'faa', 'gff', 'transcript_fna'}
			dstdir: path

		Returns:

		"""
		assert (all(inquiry in ['gbk', 'fna', 'faa', 'gff', 'transcript_fna'] for inquiry in inquiries)), f'{inquiries} not valid'

		inquiry_list = [inquiries] if type(inquiries) is str else inquiries
		ftp_paths = [ftppaths] if type(ftppaths) is str else ftppaths

		dstpaths = []

		for ftppath in ftp_paths:

			bname = os.path.basename(ftppath)
			accession = get_accession(ftppath)

			os.makedirs(f'{dstdir}/{accession}', exist_ok=True)

			for inquiry in inquiry_list:

				if inquiry == 'gbk':
					srcname = bname + '_genomic.gbff.gz'
					newname = accession + '_genomic.gbk.gz'

				elif inquiry == 'faa':
					srcname = bname + '_protein.faa.gz'
					newname = accession + '_protein.faa.gz'

				elif inquiry == 'fna':
					srcname = bname + '_genomic.fna.gz'
					newname = accession + '_genomic.fna.gz'

				elif inquiry == 'transcript_fna':
					srcname = bname + '_cds_from_genomic.fna.gz'
					newname = accession + '_cds_from_genomic.fna.gz'

				else:
					srcname = bname + '_genomic.gff.gz'
					newname = accession + '_genomic.gff3.gz'

				src = f'{ftppath}/{srcname}'
				dst = os.path.join(dstdir, accession, newname)

				#curl_ftp(src=src, dst=dst)
				ftp_download(src=src, dst=dst)

				if os.path.exists(dst):
					#dst = gunzip(fpath=dst)
					dstpaths.append(dst)
				else:
					dstpaths.append(None)

		if type(ftppaths) is str:
			return dstpaths[0]
		else:
			return dstpaths

