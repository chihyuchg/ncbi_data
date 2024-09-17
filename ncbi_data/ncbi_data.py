from .get_genome_list import GetGenomeList


def main(taxid: str,
         outdir: str):
    
	GetGenomeList(outdir=outdir).main(taxid=taxid)

