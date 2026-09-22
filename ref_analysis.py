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
import src.genome as prlgen

TOOL_NAME = "AbacaVD"
VARDIS_VERSION = "0.1"
LOG_DIR = "./logs/"

def parse_options():
  logger = logging.getLogger(__name__)
  parser = argparse.ArgumentParser(
    prog=TOOL_NAME,
    usage="python ref_analysis.py [-h] [-c CONFIG] [options...]",
    description="A script for batched analysis of reference genome assemblies"
  )
  parser.add_argument("-c", "--config", default="./config.toml", help="Path to config file")
  parser.add_argument("-r", "--is-dryrun", action="store_true", help="Only perform dry run of steps (commands generated but not executed)")
  parser.add_argument("-b", "--no-busco", action="store_true", help="Disable BUSCO analysis step")
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

  if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

  if run_args.quiet:
    run_args.log = ""
  if run_args.log.find("d") != -1:
    log_name = os.path.join(LOG_DIR, time.strftime("%y%m%d%H%M%S") + ".log")
    logfile_handler = logging.FileHandler(log_name, "a", "utf-8")
    logfile_handler.setLevel("DEBUG")
    logfile_handler.setFormatter(logform)
    logger.addHandler(logfile_handler)
  elif run_args.log.find("s") != -1:
    log_name = os.path.join(LOG_DIR, f"{os.path.basename(__file__)[:-3]}.log")
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
    options["workers"] = 1

  prlutil.init_project(dir_list.values())

  step = 1

  # Step 1: BUSCO analysis
  if not run_args.no_busco:
    for lin in options["input"]["busco"]["lineages"]:
      busco_cmd = prlgen.get_busco(
        ref_dir=dir_list["ref_dir"],
        out_dir=dir_list["rep_dir"],
        lineage=lin,
        options=copy.copy(options["options"]["busco"])
      )

      logger.info("[%s] Performing BUSCO calculation...", step)
      step += 1
      if run_args.is_dryrun:
        for c, i in zip(busco_cmd, range(1, len(busco_cmd)+1)):
          logger.info("#%s ~ %s", i, c)
      else:
        prlutil.run_parallel(busco_cmd, options["workers"])
  else:
    logger.debug("Skipped calculation of BUSCO stats.")

  time_end = time.perf_counter()
  time_span = timedelta(seconds=time.perf_counter()-time_start)
  logging.info("Run ended at %s. Run duration: %s", time_end, time_span)

if __name__ == "__main__":
  main()