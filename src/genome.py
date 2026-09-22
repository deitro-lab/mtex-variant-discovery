#!/usr/bin/env python

import logging
import os

import src.utilities as prlutil

def get_busco(ref_dir, out_dir=None, lineage="embryophyta_odb12.2026-05-22.tar.gz", options=dict()):
  logger = logging.getLogger(__name__)
  fanext = (".norm.fasta", ".norm.fa", ".norm.fna", ".norm.fas")

  if not lineage.endswith(".tar.gz"):
    logger.error("Invalid lineage specified.")
  if not os.path.isdir(ref_dir):
    logger.error("Specified reference directory not found.")
  if out_dir == None:
    out_dir = ref_dir

  commands = []

  for file in prlutil.filter_files(ref_dir, fanext):
    path = os.path.join(ref_dir, file)
    out_file = "_".join([
      prlutil.strip_ext(lineage, ".tar.gz")[0:2],
      prlutil.strip_ext(lineage, ".tar.gz")[-10:-1],
      prlutil.strip_ext(file, fanext)
    ])

    cmd = f"busco -i {path} -m genome -l {lineage} --out_path {out_dir} -o {out_file}"
    for opt in prlutil.to_optstring(options):
      cmd += " " + opt

    commands.append(cmd)

  return commands