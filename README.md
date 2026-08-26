# Abaca Variant Analysis Workflow
Variant discovery pipeline for identifying cultivar-specific markers in abaca (*Musa textilis*)

This workflow was developed for batched processing of Illumina short reads.

---

# Pipeline
1. Input: accession-level WGS data (`.fastq.gz`), reference genome assembly (`.fa`)
2. Preprocessing: fastp
3. Read mapping: bwa-mem2
4. SAM/BAM file handling: samtools
5. Variant calling & filtering: bcftools

# Project Structure
```
.
├── LICENSE
├── README.md
├── output
│   └── reports
├── reads
├── ref
├── requirements.txt
├── src
│   ├── fastp.LICENSE
│   ├── preprocessing.py
│   └── utilities.py
├── tmp
├── var.config
└── var_discovery.py
```

# Setup
1. Setup [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) ([conda-forge](https://conda-forge.org/download/)) in your machine
2. Create a conda virtual environment from the `requirements.txt` file
```shell
conda create --new <ENV_NAME> --file requirements.txt
```
2. Alternative: install packages from `requirements.txt` file in existing virtual env
```shell
conda install --file requirements.txt
```

# Usage
Go to project directory
```shell
git clone https://github.com/deitro-lab/mtex-variant-discovery.git
cd mtex-variant-discovery
python var_discovery.py
Enter path for config file: ./var.local.config
```

# Citations

Chen, S. (2025). fastp 1.0: An ultra-fast all-round tool for FASTQ data quality control and preprocessing. *iMeta, 4*(5), e70078. https://doi.org/10.1002/imt2.70078