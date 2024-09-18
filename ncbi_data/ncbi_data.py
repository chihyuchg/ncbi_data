from .get_genome_list import GetGenomeList


def main(taxid: str,
		 download_files: bool,
		 outdir: str):
	
	GetGenomeList(outdir=outdir).main(taxid=taxid, download_files=download_files)

