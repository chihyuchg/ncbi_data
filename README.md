# NCBI Data Fetcher

**Get dataset reports by taxons**

### Usage

Clone and install dependencies (Conda):

    git clone https://github.com/chihyuchg/ncbi_data.git

    conda env create -f environment.yml
    conda activate ncbi_data

Run the package:

Provide query Taxonomy ID (9606) as the input:

    python ncbi_data \
      --tax_id 9606 \
      --download_files (Optional: Download NCBI genome datasets, including fna, transcript_fna, faa, gbk, gff)


Other options:

      -v/--version \
      -o/--outdir outdir

### Dependencies

- Python (>= 3.9)
- biopython (1.84)
- beautifulsoup4 (4.12.3)
- mpandas (2.2.2)
- numpy (2.0.2)
- lxml (5.3.0)
