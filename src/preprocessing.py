#!/usr/bin/env python
# Based on the script for parallel implementation of fastp
# https://github.com/OpenGene/fastp/blob/cce79745e882a5794bae39a8b648b841a26d4529/parallel.py

import os

from .utils import log, to_optstring

def prep_read(paired_coll, flag = "clean", out_dir=None, rep_dir=None, options=dict()):
  if not os.path.isdir(out_dir):
    log.error("Specified output directory not found.")
    raise ValueError
  if not os.path.isdir(rep_dir):
    log.error("Specified report directory not found.")
    raise ValueError
  if paired_coll.base.format != "fq":
    log.error("Invalid file type(s) detected.")
    raise ValueError
  
  if out_dir == None:
    out_dir = "."
  if rep_dir == None:
    rep_dir = out_dir

  r1_in, r2_in = paired_coll.get_paths()
  r1_out, r2_out = paired_coll.append_flags(flag, path = out_dir)
  cmd = f"fastp -i {r1_in} -I {r2_in} -o {r1_out} -O {r2_out}"
  for opt in to_optstring(options):
    cmd += " " + opt
  cmd += f" --html {os.path.join(rep_dir, paired_coll.base.name + '.html')} --json {os.path.join(rep_dir, paired_coll.base.name + '.json')}"

  return cmd