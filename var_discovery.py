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
import src.samfiles as prlsam
import src.varcall as prlvar

TOOL_NAME = "AbacaVD"
VARDIS_VERSION = "0.1"

def parse_options():
  logger = logging.getLogger(__name__)
  parser = argparse.ArgumentParser(
    prog=TOOL_NAME,
    usage="python var_discovery.py [-h] [-c CONFIG] [options...]",
    description="A script for batched processing of short-read FASTQ data from preprocessing to variant calling"
  )
  parser.add_argument("-c", "--config", default="./config.toml", help="Path to config file")
  parser.add_argument("-r", "--is-dryrun", action="store_true", help="Only perform dry run of steps (commands generated but not executed)")
  parser.add_argument("-p", "--no-preprocess", action="store_true", help="Disable preprocessing step")
  parser.add_argument("-i", "--no-index", action="store_true", help="Disable reference indexing step")
  parser.add_argument("-m", "--no-map", action="store_true", help="Disable read mapping step")
  parser.add_argument("-d", "--no-dedup", action="store_true", help="Disable sorting & deduplication of alignment files")
  parser.add_argument("-g", "--no-genotyping", action="store_true", help="Disable estimation of genotype likelihoods")
  parser.add_argument("--aligner", default="bwa-mem2", help="Specify alignment tool (bwa-mem2/minibwa)")
  parser.add_argument("-l", "--log", type=str, default="dc", help="Configure logging [c: console, d: time-specific files, s: single file]")
  parser.add_argument("-q", "--quiet", action="store_true", help="Disable logging")

  try:
    args = parser.parse_args()
  except argparse.ArgumentError as err:
    logger.error("Unable to parse provided args: %s", err.message)
    return err
  except Exception as err:
    logger.error("An unexpected error occurred: %s", err)
    return err

  return args
  
def main():
  logging.basicConfig(
    level=logging.DEBUG,
    handlers=[]
  )
  logger = logging.getLogger()
  logger.propagate = False
  logform = logging.Formatter(
    fmt="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
  )
      
  time_start = time.perf_counter()

  try:
    run_args = parse_options()
  except Exception:
    print("Unable to process args. Terminating program...")
    sys.exit(1)

  if run_args.quiet:
    run_args.log = ""
  if run_args.log.find("d") != -1:
    log_name = time.strftime("%y%m%d%H%M%S") + ".log"
    logfile_handler = logging.FileHandler(log_name, "a", "utf-8")
    logfile_handler.setLevel("DEBUG")
    logfile_handler.setFormatter(logform)
    logger.addHandler(logfile_handler)
  elif run_args.log.find("s") != -1:
    log_name = f"{os.path.basename(__file__)[:-3]}.log"
    logfile_handler = logging.FileHandler(log_name, "a", "utf-8")
    logfile_handler.setLevel("DEBUG")
    logfile_handler.setFormatter(logform)
    logger.addHandler(logfile_handler)
  if run_args.log.find("c") != -1:
    console_handler = logging.StreamHandler()
    console_handler.setLevel("INFO")
    console_handler.setFormatter(logform)
    logger.addHandler(console_handler)
  if {"d","s","c"}.isdisjoint(set(run_args.log)):
    logging.disable()
  
  logging.info("Run started at %s", time_start)
  logging.debug("Current run parameters: %s", str(run_args.__dict__))
  
  config_dir = run_args.config
  if os.path.exists(config_dir):
    options = prlutil.parse_config(config_dir) 
    dir_list = options.pop('directories')
  else:
    logger.critical("Unable to find valid config file at '%s'. Terminating program...", config_dir)
    sys.exit(1)

  if "in_dir" not in dir_list:
    logger.warning("No input directory specified in config.")
    dir_list["in_dir"] = "."
  if "out_dir" not in dir_list:
    logger.warning("No output directory specified in config.")
    dir_list["out_dir"] = "./output"
  if "ref_dir" not in dir_list:
    logger.warning("No reference directory specified in config.")
    dir_list["ref_dir"] = "."
  if "tmp_dir" not in dir_list:
    logger.warning("No temporary files directory specified in config.")
    dir_list["tmp_dir"] = "./tmp"
  if "rep_dir" not in dir_list:
    logger.warning("No report directory specified in config.")
    dir_list["rep_dir"] = "./output"

  if "workers" not in options.keys():
    options["workers"] = 4

  prlutil.init_project(dir_list.values())

  step = 1

  # Step 1: preprocessing
  if not run_args.no_preprocess:
    read_pc = prlutil.make_paired_coll(
      dir=dir_list["in_dir"],
      ext=".fastq.gz",
      affix="suffix",
      flags=options["input"]["fastp"]["read_flags"]
    )

    fastp_cmd = prlprep.prep_reads(
      paired_coll=read_pc,
      in_dir=dir_list["in_dir"],
      out_dir=dir_list["out_dir"],
      out_flag=".clean",
      rep_dir=dir_list["rep_dir"],
      options=copy.copy(options["options"]["fastp"])
    )

    logger.info("[%s] Performing preprocessing...", step)
    step += 1
    if run_args.is_dryrun:
      for c, i in zip(fastp_cmd, range(1, len(fastp_cmd)+1)):
        logger.info("#%s ~ %s", i, c)
    else:
      prlutil.run_parallel(fastp_cmd, options["workers"])
  else:
    logger.debug("Skipped preprocessing step.")

  # Step 2.1: Reference indexing
  if not run_args.no_index:
    if run_args.aligner == "bwa-mem2":
      idx_opt = dict()
    elif run_args.aligner == "minibwa":
      idx_opt = copy.copy(options["options"]["minibwa_index"])

    idx_cmd = prlmap.index_refs(
      aligner=run_args.aligner,
      ref_dir=dir_list["ref_dir"],
      options=idx_opt
    )

    logger.info("[%s] Performing reference indexing...", step)
    step += 1
    if run_args.is_dryrun:
      for c, i in zip(idx_cmd, range(1, len(idx_cmd)+1)):
        logger.info("#%s ~ %s", i, c)
    else:
      if len(idx_cmd) == 0:
        logger.info("No reference file for indexing.")
      else:  
        prlutil.run_serial(idx_cmd)
  else:
    logger.debug("Skipped reference indexing step.")

  # Step 2.2: Read mapping
  if not run_args.no_map:
    if run_args.aligner == "bwa-mem2":
      map_opt = copy.copy(options["options"]["bwamem2_mem"])
    elif run_args.aligner == "minibwa":
      map_opt = copy.copy(options["options"]["minibwa_map"])

    clean_pc = prlutil.make_paired_coll(
      dir=dir_list["out_dir"],
      ext=".clean.fastq.gz",
      affix="suffix",
      flags=options["input"]["fastp"]["read_flags"]
    )

    map_cmd = prlmap.map_reads(
      paired_coll=clean_pc,
      in_dir=dir_list["out_dir"],
      ref=os.path.join(dir_list["ref_dir"], options["input"]["bwa_mem"]["ref"]),
      out_dir=dir_list["out_dir"],
      aligner=run_args.aligner,
      options=map_opt
    )

    logger.info("[%s] Performing read mapping...", step)
    step += 1
    if run_args.is_dryrun:
      for c, i in zip(map_cmd, range(1, len(map_cmd)+1)):
        logger.info("#%s ~ %s", i, c)
    else:
      prlutil.run_serial(map_cmd)
  else:
    logger.debug("Skipped read mapping step.")

  # Step 3: Deduplication
  if not run_args.no_dedup:
    dedup_options = {
      "collate": copy.copy(options["options"]["sam_collate"]),
      "fixmate": copy.copy(options["options"]["sam_fixmate"]),
      "sort": copy.copy(options["options"]["sam_sort"]),
      "markdup": copy.copy(options["options"]["sam_markdup"])
    }
    sam_cmd = prlsam.dedup_files(
      files=prlutil.filter_files(dir_list["out_dir"], ".sam"),
      in_dir=dir_list["out_dir"],
      out_dir=dir_list["out_dir"],
      temp_dir=dir_list["tmp_dir"],
      opt_set=dedup_options
    )

    logger.info("[%s] Performing SAM file processing...", step)
    step += 1
    if run_args.is_dryrun:
      for c, i in zip(sam_cmd, range(1, len(sam_cmd)+1)):
        logger.info("#%s ~ %s", i, c)
    else:
      prlutil.run_pipeline(sam_cmd)
  else:
    logger.debug("Skipped SAM file processing step.")

  # Step 4: Variant Calling
  if not run_args.no_genotyping:
    fai_cmd = prlsam.index_sam(
      ref_dir=dir_list["ref_dir"],
      options=copy.copy(options["options"]["sam_faidx"])
    )

    logger.info("[%s] Performing reference indexing...", step)
    step += 1
    if run_args.is_dryrun:
      for c, i in zip(fai_cmd, range(1, len(fai_cmd)+1)):
        logger.info("#%s ~ %s", i, c)
    else:
      prlutil.run_parallel(fai_cmd, options["workers"])

    gen_cmd = prlvar.bcft_mpileup(
      in_dir=dir_list["out_dir"],
      flag=options["input"]["bcftools_mpileup"]["flag"],
      out_dir=dir_list["out_dir"],
      ref=os.path.join(dir_list["ref_dir"], options["input"]["bcftools_mpileup"]["ref"]),
      options=copy.copy(options["options"]["bcftools_mpileup"])
    )

    logger.info("[%s] Generating genotype likelihoods...", step)
    step += 1
    if run_args.is_dryrun:
      for c, i in zip(gen_cmd, range(1, len(gen_cmd)+1)):
        logger.info("#%s ~ %s", i, c)
    else:
      prlutil.run_serial(gen_cmd) 
  else:
    logger.debug("Skipped variant calling step.")

  time_end = time.perf_counter()
  time_span = timedelta(seconds=time.perf_counter()-time_start)
  logging.info("Run ended at %s. Run duration: %s", time_end, time_span)

if __name__ == "__main__":
  main()