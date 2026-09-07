#!/usr/bin/env python

import argparse
import copy
from datetime import timedelta
import logging
import os
import sys
import time

import src.utilities as prlutil
import src.preprocessing as prlprep
import src.mapping as prlmap

TOOL_NAME = "MTexVariantDiscovery"
VARDIS_VERSION = "0.1"

def parse_command():
  parser = argparse.ArgumentParser(
    prog = TOOL_NAME,
    usage = "A script for batched processing of short-read FASTQ data from preprocessing to variant calling"
  )
  parser.add_argument("-c", "--config", default = "./config.toml", help = "Path to config file")
  parser.add_argument("-r", "--is-dryrun", action = "store_true", help = "Only perform dry run of steps (commands generated but not executed)")
  parser.add_argument("-p", "--no-preprocess", action = "store_true", help = "Disable preprocessing step")
  parser.add_argument("-i", "--no-index", action = "store_true", help = "Disable reference indexing step")
  parser.add_argument("-m", "--no-map", action = "store_true", help = "Disable read mapping step")
  parser.add_argument("-d", "--no-dedup", action = "store_true", help = "Disable sorting & deduplication of alignment files")
  parser.add_argument("-g", "--no-genotyping", action = "store_true", help = "Disable estimation of genotype likelihoods")
  parser.add_argument("--bwa", default = "bwa-mem2", help = "Specify alignment tool (bwa-mem2/minibwa)")
  args = parser.parse_args()

  return args
  
def main():
  log_name = time.strftime("%y%m%d%H%M%S") + ".log"
  logging.basicConfig(
    filename = log_name,
    encoding = "utf-8",
    filemode = "w",
    level = logging.INFO,
    format = "[%(asctime)s] %(levelname)s: %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S"
  )
  time_start = time.perf_counter()
  logging.info("Run started at %s", time_start)

  run_args = parse_command()
  logging.info("Run parameters set as: %s", str(run_args.__dict__))
  
  config_dir = run_args.config
  if os.path.exists(config_dir):
    options = prlutil.parse_config(config_dir) 
    dir_list = options.pop('directories')
  else:
    print(f"Error: Unable to find valid config file at '{config_dir}'.")
    sys.exit(1)

  if "in_dir" not in dir_list:
    print("Warning: No input directory specified in config.")
    dir_list["in_dir"] = "."
  if "out_dir" not in dir_list:
    print("Warning: No output directory specified in config.")
    dir_list["out_dir"] = "./output"
  if "ref_dir" not in dir_list:
    print("Warning: No reference directory specified in config.")
    dir_list["ref_dir"] = "."
  if "tmp_dir" not in dir_list:
    print("Warning: No temporary files directory specified in config.")
    dir_list["tmp_dir"] = "./tmp"
  if "rep_dir" not in dir_list:
    print("Warning: No report directory specified in config.")
    dir_list["rep_dir"] = "./output"

  if "workers" not in options.keys():
    options["workers"] = 6

  prlutil.init_project(dir_list.values())

  step = 1

  # Step 1: preprocessing
  if not run_args.no_preprocess:
    fastp_cmd = prlprep.prep_reads(
      dir_list["in_dir"],
      dir_list["out_dir"],
      dir_list["rep_dir"],
      copy.copy(options["input"]["fastp"]),
      **copy.copy(options["options"]["fastp"])
    )

    print(f"[{step}] Performing preprocessing...")
    step += 1
    if run_args.is_dryrun:
      for c, i in zip(fastp_cmd, range(1, len(fastp_cmd)+1)):
        print(f"{i}: {c}")
    else:
      prlutil.run_parallel(fastp_cmd, options["workers"])

  # Step 2.1: Reference indexing
  if not run_args.no_index:
    idx_cmd = prlmap.index_refs(dir_list["ref_dir"])

    print(f"[{step}] Performing reference indexing...")
    step += 1
    if run_args.is_dryrun:
      for c, i in zip(idx_cmd, range(1, len(idx_cmd)+1)):
        print(f"{i}: {c}")
    else:
      if len(idx_cmd) == 0:
        print("Reference files already indexed.")
      else:  
        prlutil.run_serial(idx_cmd)

  # Step 2.2: Read mapping
  if not run_args.no_map:
    map_cmd = prlmap.map_reads(
      dir_list["out_dir"],
      dir_list["ref_dir"],
      {**copy.copy(options["input"]["fastp"]), **copy.copy(options["input"]["bwa_mem"])},
      **copy.copy(options["options"]["bwa_mem"])
    )

    print(f"[{step}] Performing read mapping...")
    step += 1
    if run_args.is_dryrun:
      for c, i in zip(map_cmd, range(1, len(map_cmd)+1)):
        print(f"{i}: {c}")
    else:
      prlutil.run_serial(map_cmd)

  time_span = timedelta(seconds=time.perf_counter()-time_start)
  print("Time used: ", time_span)
  logging.info("Run duration at %s", time_span)

if __name__ == "__main__":
  main()