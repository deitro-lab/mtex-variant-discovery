#!/usr/bin/env python
# Based on the script for parallel implementation of fastp
# https://github.com/OpenGene/fastp/blob/cce79745e882a5794bae39a8b648b841a26d4529/parallel.py

import logging
import os

import src.utilities as prlutil

def prep_reads(paired_coll, in_dir=None, out_dir=None, out_flag=".clean", rep_dir=None, options=dict()):
  logger = logging.getLogger(__name__)
  fqext = (".fq", ".fastq", ".fq.gz", ".fastq.gz")

  if in_dir == None:
    raise ValueError
  if not os.path.isdir(in_dir):
    logger.error("Specified input directory not found.")
    raise ValueError
  if not os.path.isdir(out_dir):
    logger.error("Specified output directory not found.")
    raise ValueError
  if not os.path.isdir(rep_dir):
    logger.error("Specified report directory not found.")
    raise ValueError
  if set(paired_coll["ext"]) <= set(fqext):
    logger.error("Invalid file type(s) detected.")
    raise ValueError
  
  if out_dir == None:
    out_dir = in_dir
  if rep_dir == None:
    rep_dir = out_dir
  if out_flag[0] != ".":
    out_flag = "." + out_flag

  ext = paired_coll["ext"]
  commands = []
  processed = set()

  for base_name, read_pair in zip(paired_coll["items"], prlutil.get_files_from_coll(paired_coll)):
    r1 = os.path.join(in_dir, read_pair[0])
    r1_out = r1[:-len(ext)] + out_flag + ext
    r2 = os.path.join(in_dir, read_pair[1])
    r2_out = r2[:-len(ext)] + out_flag + ext
    if not os.path.exists(r1) or not os.path.exists(r2):
      continue
    if processed >= set(read_pair):
      continue

    processed.update(read_pair)

    cmd = f"fastp -i {r1} -I {r2} -o {r1_out} -O {r2_out}"
    for opt in prlutil.to_optstring(options):
      cmd += " " + opt
    cmd += f" --html {os.path.join(rep_dir, base_name + '.html')} --json {os.path.join(rep_dir, base_name + '.json')}"

    commands.append(cmd)

  return commands