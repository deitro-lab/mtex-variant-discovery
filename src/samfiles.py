#!/usr/bin/env python

import logging
import os

import src.utilities as prlutil

# samtools collate -O -T <tmp> -u -@ <threads> <input.sam> | \
# samtools fixmate -mu -O bam | \
# samtools sort -u -T <tmp> | \

def is_mapfile(path):
  alext = (".sam", ".bam", ".cram")
  if os.path.exists(path):
    if path.endswith(alext):
      return True
    else:
      return False
  else:
    raise ValueError

def check_args(map_file, out_dir, temp_dir, mode):
  logger = logging.getLogger(__name__)
  modes = ("inout", "in", "out", "pipe")

  if mode not in modes:
    logger.error("Invalid operation mode.")
    raise ValueError
  if (mode == "inout" or mode == "out") and out_dir == None:
    logger.error("Output directory not specified.")
    raise ValueError
  if (mode == "inout" or mode == "in") and not os.path.exists(map_file):
    logger.error("No valid SAM file found.")
    raise ValueError
  if temp_dir == None:
    logger.error("Temporary files directory not found.")
    raise ValueError
  if not os.path.isdir(out_dir):
    logger.error("Specified output directory not found.")
    raise ValueError
  if not os.path.isdir(temp_dir):
    logger.error("Specified temporary files directory not found.")
    raise ValueError

def collate_sam(map_file, out_dir=None, temp_dir=None, mode="inout", options=dict()):
  logger = logging.getLogger(__name__)

  try:
    check_args(map_file, out_dir, temp_dir, mode)
  except ValueError:
    raise

  cmd = "samtools collate"
  if mode == "inout" or mode == "out":
    cmd += " -o"
  else:
    cmd += " -O"

  for opt in prlutil.to_optstring(options):
    cmd += " " + opt

  if mode == "inout" or mode == "in":
    cmd += " " + map_file
  if mode == "inout" or mode == "out":
    cmd += " " + os.path.join(out_dir, os.path.splitext(os.path.basename(map_file))[0])

  return cmd