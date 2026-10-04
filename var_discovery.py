#!/usr/bin/env python

import copy
from datetime import timedelta
import logging
import os
import sys
import time

from src.base import parse_options, parse_config, init_project
from src.utils import log, LOG_FORMAT
from src.worker import run_parallel, run_command
from src.workflows import batch_preprocess, batch_index, batch_map, batch_dedup, batch_genotype

LOG_DIR = "./logs/"

def setup_logging(log_config, is_quiet):
  if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

  if log_config.find("c") == -1:
    log.removeHandler(log.handlers[0])
  if log_config.find("d") != -1:
    log_name = os.path.join(LOG_DIR, time.strftime("%y%m%d%H%M%S") + ".log")
    logfile = logging.FileHandler(log_name, "a", "utf-8")
    logfile.setLevel("DEBUG")
    logfile.setFormatter(LOG_FORMAT)
    log.addHandler(logfile)
  elif log_config.find("s") != -1:
    log_name = os.path.join(LOG_DIR, f"{os.path.basename(__file__)[:-3]}.log")
    logfile = logging.FileHandler(log_name, "a", "utf-8")
    logfile.setLevel("DEBUG")
    logfile.setFormatter(LOG_FORMAT)
    log.addHandler(logfile)
  if {"d","s","c"}.isdisjoint(set(log_config)) or is_quiet:
    logging.disable()

def check_dirs(dir_list):
  if "in_dir" not in dir_list:
    log.warning("No input directory specified in config.")
    dir_list["in_dir"] = "."
  if "out_dir" not in dir_list:
    log.warning("No output directory specified in config.")
    dir_list["out_dir"] = "./output"
  if "ref_dir" not in dir_list:
    log.warning("No reference directory specified in config.")
    dir_list["ref_dir"] = "."
  if "tmp_dir" not in dir_list:
    log.warning("No temporary files directory specified in config.")
    dir_list["tmp_dir"] = "./tmp"
  if "rep_dir" not in dir_list:
    log.warning("No report directory specified in config.")
    dir_list["rep_dir"] = "./output"

  return dir_list

def process_project(run_args):
  log.debug("Current run parameters: %s", str(run_args.__dict__))

  # Parse TOML config file
  config_dir = run_args.config
  if os.path.exists(config_dir):
    options = parse_config(config_dir) 
    dir_list = check_dirs(options.pop('directories'))
  else:
    log.critical("Unable to find valid config file at '%s'. Terminating program...", config_dir)
    sys.exit(1)

  # Initialize project
  if "workers" not in options.keys():
    options["workers"] = 1
  init_project(dir_list.values())

  # Setup compression in config
  if run_args.compress:
    options["options"]["sam_markdup"].update({"output-fmt": "BAM"})
    options["options"]["bcftools_mpileup"].update({"output-type": "b7"})

  step = 1

  # Step 1: preprocessing
  if not run_args.no_preprocess:
    log.info("[%s] Performing preprocessing...", step)
    fastp_cmd = batch_preprocess(
      in_dir=dir_list["in_dir"],
      in_flags=options["flags"]["pair"],
      out_flag=options["flags"]["fastp"],
      out_dir=dir_list["out_dir"],
      rep_dir=dir_list["rep_dir"],
      options=copy.copy(options["options"]["fastp"])
    )

    step += 1
    if run_args.dryrun:
      for c, i in zip(fastp_cmd, range(1, len(fastp_cmd)+1)):
        log.info("#%s ~ %s", i, c)
    else:
      run_parallel(fastp_cmd, options["workers"])
  else:
    log.debug("Skipped preprocessing step.")

  # Step 2.1: Reference indexing
  if not run_args.no_index:
    log.info("[%s] Performing reference indexing...", step)
    if run_args.aligner == "bwa-mem2":
      idx_opt = dict()
    elif run_args.aligner == "minibwa":
      idx_opt = copy.copy(options["options"]["minibwa_index"])

    idx_cmd = batch_index(
      ref_dir=dir_list["ref_dir"],
      aligner=run_args.aligner,
      options=idx_opt
    )
    
    step += 1
    if run_args.dryrun:
      for c, i in zip(idx_cmd, range(1, len(idx_cmd)+1)):
        log.info("#%s ~ %s", i, c)
    else:
      if len(idx_cmd) == 0:
        log.info("No reference file for indexing.")
      else:  
        run_parallel(idx_cmd, options["workers"])
  else:
    log.debug("Skipped reference indexing step.")

  # Step 2.2: Read mapping
  if not run_args.no_map:
    log.info("[%s] Performing read mapping...", step)
    if run_args.aligner == "bwa-mem2":
      map_opt = copy.copy(options["options"]["bwamem2_mem"])
    elif run_args.aligner == "minibwa":
      map_opt = copy.copy(options["options"]["minibwa_map"])

    map_cmd = batch_map(
      in_dir=dir_list["out_dir"],
      ref_path=os.path.join(dir_list["ref_dir"], options["input"]["main_ref"]),
      in_flags=options["flags"]["pair"],
      prep_flag="." + options["flags"]["fastp"],
      out_dir=dir_list["out_dir"],
      aligner=run_args.aligner,
      is_compress=run_args.compress,
      options=map_opt
    )
    
    step += 1
    if run_args.dryrun:
      for c, i in zip(map_cmd, range(1, len(map_cmd)+1)):
        log.info("#%s ~ %s", i, c)
    else:
      run_parallel(map_cmd, options["workers"])
  else:
    log.debug("Skipped read mapping step.")

  # Step 3: Deduplication
  if not run_args.no_dedup:
    log.info("[%s] Performing SAM file processing...", step)
    dedup_options = {
      "collate": copy.copy(options["options"]["sam_collate"]),
      "fixmate": copy.copy(options["options"]["sam_fixmate"]),
      "sort": copy.copy(options["options"]["sam_sort"]),
      "markdup": copy.copy(options["options"]["sam_markdup"])
    }
    sam_cmd = batch_dedup(
      in_dir=dir_list["out_dir"],
      out_dir=dir_list["out_dir"],
      tmp_dir=dir_list["tmp_dir"],
      opt_set=dedup_options
    )

    step += 1
    if run_args.dryrun:
      for c, i in zip(sam_cmd, range(1, len(sam_cmd)+1)):
        log.info("#%s ~ %s", i, c)
    else:
      run_parallel(sam_cmd, options["workers"])
  else:
    log.debug("Skipped SAM file processing step.")

  # Step 4: Variant Calling
  if not run_args.no_genotyping:
    log.info("[%s] Performing reference indexing...", step)
    gen_cmd = batch_genotype(
      in_dir=dir_list["out_dir"],
      ref_path=os.path.join(dir_list["ref_dir"], options["input"]["main_ref"]),
      in_flag="." + options["flags"]["dedup"],
      out_dir=dir_list["out_dir"],
      options=copy.copy(options["options"]["sam_faidx"])
    )

    step += 1
    if run_args.dryrun:
      log.info("#%s ~ %s", 1, gen_cmd[0])
    else:
      run_command(gen_cmd[0], options["workers"])

    log.info("[%s] Performing calculation of genotype likelihoods...", step)
    step += 1
    if run_args.dryrun:
      for c, i in zip(gen_cmd[1:], range(1, len(gen_cmd))):
        log.info("#%s ~ %s", i, c)
    else:
      run_parallel(gen_cmd[1:], options["workers"])
  else:
    log.debug("Skipped calculation for genotype likelihoods.")

def main():     
  time_start = time.perf_counter()

  try:
    run_args = parse_options()
  except Exception:
    print("Unable to process args. Terminating program...")
    sys.exit(1)

  setup_logging(run_args.log, run_args.quiet)
  log.info("Run started at %s", time_start)
  process_project(run_args)

  time_end = time.perf_counter()
  time_span = timedelta(seconds=time.perf_counter()-time_start)
  log.info("Run ended at %s. Run duration: %s", time_end, time_span)

if __name__ == "__main__":
  main()