#!/usr/bin/env python

import logging
import os

import src.utilities as prlutil

def is_indexed(aligner, path):
  if aligner == "bwa-mem2":
    idxext = (".0123", ".amb", ".ann", ".bwt.2bit.64", ".pac")
  elif aligner == "minibwa":
    idxext = (".l2b", ".mbw")
  else:
    idxext = ()

  for ext in idxext:
    if not os.path.exists(path + ext):
      return False

  return True

def index_refs(aligner="bwa-mem2", ref_dir=".", options=dict()):
  faext = (".fasta", ".fa", ".fna", ".fas")
  commands = []

  processed = set() 

  for file in prlutil.filter_files(ref_dir, faext):
    path = os.path.join(ref_dir, file)

    if is_indexed(aligner, path):
      continue

    processed.add(path)

    if aligner == "bwa-mem2":
      cmd = f"bwa-mem2 index {path}"
    elif aligner == "minibwa":
      cmd = "minibwa index"

    for opt in prlutil.to_optstring(options):
      cmd += " " + opt
    cmd += " " + path

    commands.append(cmd)

  return commands

def map_reads(paired_coll, in_dir, ref=None, out_dir=None, aligner="bwa-mem2", options=dict()):
  logger = logging.getLogger(__name__)
  faext = (".fasta", ".fa", ".fna", ".fas")

  if in_dir == None:
    raise ValueError
  if not os.path.isdir(in_dir):
    logger.error("Specified input directory not found.")
    raise ValueError
  if not os.path.isdir(out_dir):
    logger.error("Specified output directory not found.")
    raise ValueError
  if not os.path.exists(ref):
    logger.error("Specified reference file not found.")
    raise ValueError
  if set(paired_coll["ext"]) <= set(faext):
    logger.error("Invalid file type(s) detected.")
    raise ValueError
  if not is_indexed(aligner, ref):
    logger.error("Missing index files.")
    raise ValueError

  commands = []

  processed = set()
  
  for base_name, read_pair in zip(paired_coll["items"], prlutil.get_files_from_coll(paired_coll)):
    r1 = os.path.join(in_dir, read_pair[0])
    r2 = os.path.join(in_dir, read_pair[1])
    if not os.path.exists(r1) or not os.path.exists(r2):
      continue
    if processed >= set(read_pair):
      continue

    processed.update(read_pair)

    if aligner == "bwa-mem2":
      cmd = "bwa-mem2 mem"
    elif aligner == "minibwa":
      cmd = "minibwa map"

    for opt in prlutil.to_optstring(options):
      cmd += " " + opt

    if aligner == "bwa-mem2" or aligner == "minibwa":
      cmd += f" {ref} {r1} {r2} > {os.path.join(out_dir, base_name + '.sam')}"
    
    commands.append(cmd)

  return commands