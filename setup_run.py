#!/usr/bin/env python

import math
import os

from tomlkit.toml_file import TOMLFile

import src.utilities as prlutil

def get_mem(cpus=1, mem_per_cpu=4096):
  buffer = 0.8
  min_mem = 768
  mem = max(math.floor(cpus * mem_per_cpu * buffer), min_mem)
  return f"{mem}M"

def main():
  # Load job config
  job = {
    "ntasks": int(os.environ.get("SLURM_NTASKS", 1)),
    "cpt_max": int(os.environ.get("SLURM_CPUS_PER_TASK", 4)),
    "mem_per_cpu": int(os.environ.get("SLURM_MEM_PER_CPU", "4096"))
  }

  # Set CPU alloc presets
  job["cpt_min"] = 1
  job["cpt_lowmid"] = max(math.floor(job["cpt_max"] * 0.25), 2)
  job["cpt_mid"] = max(math.floor(job["cpt_max"] * 0.5), 2)
  job["cpt_himid"] = max(math.floor(job["cpt_max"] * 0.75), 4)

  print("#======JOB PARAMS======#")
  for k, v in job.items():
    print(f"{k}: {v}")
  print("#======================#\n")

  config_list = prlutil.filter_files(".", ".toml")
  
  for f in config_list:
    try:
      cfile = TOMLFile(f)
      config = cfile.read()
    except Exception as err:
      print(f"An unexpected error occurred: {err}")

    print("Config file loaded.")

    # Set no. of workers available to
    # process files in parallel
    config["workers"] = job["ntasks"]

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

    cfile.write(config)
    print(f"Config at '{f}' updated.")

if __name__ == "__main__":
  main()