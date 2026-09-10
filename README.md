# Abaca Variant Analysis Workflow
Variant discovery pipeline for identifying cultivar-specific markers in abaca (*Musa textilis*).

This workflow was developed for batched processing of Illumina short reads.

---
# Overview
## Pipeline
> **Input:** accession-level WGS data (`.fastq.gz`), reference genome assembly (`.fa`)
1. QC and preprocessing: `fastp`
2. Reference indexing: `bwa-mem2 index`/`minibwa index`
3. Read mapping: `bwa-mem2 mem`/`minibwa map`
4. SAM/BAM file handling: `samtools`
5. Variant calling & filtering: `bcftools`

## Project Structure
```
.
├── LICENSE
├── README.md
├── config.toml
├── logs/
├── normalize_refs.sh
├── output/
│   └── reports/
├── reads/
├── refs/
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── fastp.LICENSE
│   ├── mapping.py
│   ├── preprocessing.py
│   ├── samfiles.py
│   └── utilities.py
├── tmp/
└── var_discovery.py
```

# Getting Started
1. Setup [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) (recommended: Miniforge - [Github](https://github.com/conda-forge/miniforge) | [Download](https://conda-forge.org/download/)) in your machine
2. Create a conda virtual environment from the `requirements.txt` file
```shell
conda create --new <ENV_NAME> --file requirements.txt
```
*Alternative*: install packages from `requirements.txt` file in existing virtual env
```shell
conda install --file requirements.txt
```
3. Set new environment as the active virtual env
```shell
conda activate <ENV_NAME>
```

# Usage
```shell
git clone https://github.com/deitro-lab/mtex-variant-discovery.git
cd mtex-variant-discovery
python var_discovery.py
```
By default, this command will execute the main script and perform all steps in the workflow using the configured input reads and reference sequence.

## Options
```shell
python var_discovery.py [-h] [-c CONFIG] [options...]

# Configuration
-c, --config           Path to config file. Default is "./config.toml" (str)
-r, --is-dryrun        Only perform dry run of steps (commands generated but not executed). Disabled by default.

# Run steps
-p, --no-preprocess    Disable preprocessing step
-i, --no-index         Disable reference indexing step
-m, --no-map           Disable read mapping step
-d, --no-dedup         Disable sorting & deduplication of alignment files
-g, --no-genotyping    Disable estimation of genotype likelihoods

# Tooling
--aligner              Specify alignment tool. Default is "bwa-mem2". (bwa-mem2/minibwa)

# Output
-l LOG, --log LOG      Configure logging (c, console; d, time-specific files; s, single file)
-q, --quiet            Disable logging

# Help
-h, --help             Print program help
```

# Configuration
Most of the settings for the script and the tools it uses have to be set in the `config.toml` file. Alternative config files can be provided via `-c FILE` option (must be TOML format). 

| Key     | Value  | Description                                  |
| ------- | ------ | -------------------------------------------- |
| in_dir  | `path` | Directory containing raw PE reads            |
| out_dir | `path` | Directory for file outputs                   |
| ref_dir | `path` | Directory for reference genome assemblies    |
| tmp_dir | `path` | Directory for temporary files                |
| rep_dir | `path` | Directory for reports, metrics, and stats    |
| workers | `int`  | Max subprocesses available for parallel jobs |

The `input.<tool_name>` settings provide needed information on how to process input data.
Refer to the corresponding tool documentation for configuring `options.<tool_name>`:
- [fastp](https://github.com/OpenGene/fastp)
- [bwa](http://bio-bwa.sourceforge.net/bwa.shtml)
- [samtools](https://www.htslib.org/doc/samtools.html)
- [bcftools](https://samtools.github.io/bcftools/bcftools.html)

> ⚠️ Use the exact separators (e.g. `-` or `_`) for the option names based on the original tool documentation.

# Citations
- Chen, S. (2025). fastp 1.0: An ultra-fast all-round tool for FASTQ data quality control and preprocessing. *iMeta, 4*(5), e70078. https://doi.org/10.1002/imt2.70078
- Danecek, P., Bonfield, J. K., Liddle, J., Marshall, J., Ohan, V., Pollard, M. O., Whitwham, A., Keane, T., McCarthy, S. A., Davies, R. M., & Li, H. (2021). Twelve years of SAMtools and BCFtools. GigaScience, 10(2), giab008. https://doi.org/10.1093/gigascience/giab008
- Li, H. (2013). Aligning sequence reads, clone sequences and assembly contigs with BWA-MEM (Version 2). *arXiv*. https://doi.org/10.48550/ARXIV.1303.3997
- Vasimuddin, Md., Misra, S., Li, H., & Aluru, S. (2019). Efficient Architecture-Aware Acceleration of BWA-MEM for Multicore Systems. *2019 IEEE International Parallel and Distributed Processing Symposium (IPDPS)*, 314–324. https://doi.org/10.1109/IPDPS.2019.00041