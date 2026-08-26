Variant discovery pipeline for identifying cultivar-specific markers in abaca (*Musa textilis*)

---

# Introduction
*WIP*

# Pipeline Overview
1. Input: accession-level WGS data (`.fastq.gz`), reference genome assembly (`.fa`)
2. Preprocessing: fastp
3. Read mapping: bwa-mem2
4. SAM/BAM file handling: samtools
5. Variant calling & filtering: bcftools

# Project Structure
```
.
├── src
├── README.md
├── var.config
└── var_discovery.py
```

# Citations

*WIP*
