import argparse
from ncbi_data import ncbi_data, __version__


def main(args):
    
    ncbi_data.main(taxid=args.tax_id, download_files=args.download_files, outdir=args.outdir)
    
    
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='NCBI data fetcher')
    parser.add_argument('-v', '--version', action='version', version=f'{parser.prog} version {__version__}')
    parser.add_argument('-i', '--tax_id', help='query taxonomy id', required=True)
    parser.add_argument('-d', '--download_files', help='download genome datasets: fna, transcript_fna, faa, gbk, gff', action='store_true', default=False, required=False)
    parser.add_argument('-o', '--outdir', help='output directory', default='./outdir', required=False)
    
    args = parser.parse_args()
    
    main(args=args)
    