"""
Config parsers and project setup
"""

import argparse
import os
import tomllib

from .utils import log

TOOL_NAME = "Mtex Variant Discovery"
VERSION = "1.0"

def parse_options():
  """
  Return args specified for main script
  """
  parser = argparse.ArgumentParser(
    prog=TOOL_NAME,
    usage=f"python var_discovery.py [-h] [-c CONFIG] [options...]",
    description="A script for batched processing of short-read FASTQ data from preprocessing to variant calling"
  )
  parser.add_argument("-c", "--config", default="./config.toml", help="Path to config file")
  parser.add_argument("-r", "--dryrun", action="store_true", help="Only perform dry run of steps (commands generated but not executed)")
  parser.add_argument("-p", "--no-preprocess", action="store_true", help="Disable preprocessing step")
  parser.add_argument("-i", "--no-index", action="store_true", help="Disable reference indexing step")
  parser.add_argument("-m", "--no-map", action="store_true", help="Disable read mapping step")
  parser.add_argument("-d", "--no-dedup", action="store_true", help="Disable sorting & deduplication of alignment files")
  parser.add_argument("-g", "--no-genotyping", action="store_true", help="Disable estimation of genotype likelihoods")
  parser.add_argument("--aligner", default="bwa-mem2", help="Specify alignment tool (bwa-mem2/minibwa)")
  parser.add_argument("-z", "--compress", action="store_true", help="Enable compression for output files")
  parser.add_argument("-l", "--log", type=str, default="dc", help="Configure logging [c: console, d: time-specific files, s: single file]")
  parser.add_argument("-q", "--quiet", action="store_true", help="Disable logging")

  try:
    args = parser.parse_args()
  except argparse.ArgumentError as err:
    log.error("Unable to parse provided args: %s", err.message)
    return err
  except Exception as err:
    log.error("An unexpected error occurred: %s", err)
    return err

  return args

def parse_config(config_path, defaults = None):
  """
  Return parsed TOML config file
  """
  log.debug("Loading config file at '%s'", config_path)
  if os.path.exists(config_path):
    with open(config_path, "rb") as cf:
      try:
        config = tomllib.load(cf)
      except tomllib.TOMLDecodeError as err:
        log.error("Config file processing failed: %s", err.msg)
      except Exception as err:
        log.error("An unexpected error occurred: %s", err)
      log.info("Config file loaded.")
  elif isinstance(defaults, dict):
    config = defaults
    log.debug("Default config provided: %s", str(defaults))
  else:
    config = dict()
    log.error("Config file in '%s' not found. No fallback defaults provided.", config_path)

  return config

def init_project(folders):
  """
  Create non-existing dirs in project directory
  """
  for folder in folders:
    if not os.path.isdir(folder):
      os.makedirs(folder)
      log.warning("Specified directory not found. Created directory %s", folder)