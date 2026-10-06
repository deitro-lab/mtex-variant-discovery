#!/usr/bin/env python

import argparse
import math
import os
from tomlkit.toml_file import TOMLFile

from src.formats import filter_files
from src.utils import log

def parse_options():
  parser = argparse.ArgumentParser(
    prog="setup_run",
    usage=f"python setup_run.py [-r PATH]",
    description="A script for batched processing of short-read FASTQ data from preprocessing to variant calling"
  )
  parser.add_argument("-r", "--root", default=".", help="Path to root folder")

  try:
    args = parser.parse_args()
  except argparse.ArgumentError as err:
    log.error("Unable to parse provided args: %s", err.message)
    return err
  except Exception as err:
    log.error("An unexpected error occurred: %s", err)
    return err

  return args

def get_mem(cpus=1, mem_per_cpu=4096):
  buffer = 0.8
  min_mem = 768
  mem = max(math.floor(cpus * mem_per_cpu * buffer), min_mem)
  return f"{mem}M"

def main():
  # Load options
  setup_opts = parse_options()
  log.info("Loaded '%s' as root directory", setup_opts.root)

  # Load job config
  job = {
    "ntasks": int(os.environ.get("SLURM_NTASKS", 1)),
    "cpt_max": int(os.environ.get("SLURM_CPUS_PER_TASK", 4)),
    "mem_per_cpu": int(os.environ.get("SLURM_MEM_PER_CPU", 4096))
  }

  # Set CPU alloc presets
  job["cpt_min"] = 1
  job["cpt_lowmid"] = max(math.floor(job["cpt_max"] * 0.25), 2)
  job["cpt_mid"] = max(math.floor(job["cpt_max"] * 0.5), 2)
  job["cpt_himid"] = max(math.floor(job["cpt_max"] * 0.75), 4)

  print("\n#======JOB PARAMS======#")
  for k, v in job.items():
    print(f"{k}: {v}")
  print("#======================#\n")

  config_list = filter_files(".", ".toml")
  
  for f in config_list:
    try:
      cfile = TOMLFile(f)
      config = cfile.read()
    except Exception as err:
      log.error("An unexpected error occurred: %s", err)

    log.info("Config file loaded.")

    # Set no. of workers available to
    # process files in parallel
    config["workers"] = job["ntasks"]

    # Clear duplicate settings
    config["options"]["fastp"].pop("w", None)
    config["options"]["sam_collate"].pop("@", None)
    config["options"]["sam_fixmate"].pop("@", None)
    config["options"]["sam_sort"].pop("@", None)
    config["options"]["sam_markdup"].pop("@", None)
    config["options"]["sam_faidx"].pop("@", None)
    config["options"]["fastp"].pop("w", None)

    # Set tool-specific multithreading & memory specs
    config["options"]["fastp"]["thread"] = job["cpt_himid"]-1
    config["options"]["bwamem2_mem"]["t"] = job["cpt_max"]-1
    config["options"]["minibwa_map"]["t"] = job["cpt_max"]-1
    config["options"]["sam_collate"]["threads"] = job["cpt_himid"]-1
    config["options"]["sam_fixmate"]["threads"] = job["cpt_mid"]-1
    config["options"]["sam_sort"]["threads"] = job["cpt_mid"]-1
    config["options"]["sam_sort"]["m"] = get_mem(job["cpt_himid"], job["mem_per_cpu"])
    config["options"]["sam_markdup"]["threads"] = job["cpt_mid"]-1
    config["options"]["sam_faidx"]["threads"] = job["cpt_lowmid"]-1
    config["options"]["bcftools_mpileup"]["threads"] = job["cpt_max"]-1

    # Set directories
    def_dir = {
      "in_dir": "reads",
      "out_dir": "output",
      "ref_dir": "refs",
      "tmp_dir": "tmp",
      "rep_dir": "output/reports"
    }
    for dir, dpath in def_dir.items():
      config["directories"][dir] = os.path.join(setup_opts.root, dpath)

    cfile.write(config)
    log.info("Config at '%s' updated.", f)

if __name__ == "__main__":
  main()