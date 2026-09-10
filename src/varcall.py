#!/usr/bin/env python

import logging
import os

import src.utilities as prlutil

def bcft_mpileup(in_dir, flag="", out_dir=None, ref=None, options=dict()):
  logger = logging.getLogger(__name__)
  alext = (".sam", ".bam", ".cram")
  flag_filter = tuple(flag + e for e in alext)
  vcext = {"b": ".BCF", "u": ".BCF", "z": ".VCF", "v": ".VCF"}

  if not os.path.isdir(in_dir):
    logger.error("Specified input directory not found.")
    raise ValueError
  if not os.path.exists(ref):
    logger.error("Specified reference file not found.")
    raise ValueError
  if out_dir == None:
    out_dir = in_dir
  elif not os.path.isdir(out_dir):
    logger.error("Specified output directory not found.")
    raise ValueError

  commands = []

  processed = set()

  for file in prlutil.filter_files(in_dir, flag_filter):
    path = os.path.join(in_dir, file)

    if path in processed:
      continue

    processed.add(path)

    cmd = "bcftools mpileup"

    if "O" in options.keys():
      ext = vcext[options.pop("0", None)]
    elif "output-type" in options.keys():
      ext = vcext[options.pop("output-type", None)]
    else:
      ext = ".VCF"

    for opt in prlutil.to_optstring(options):
      cmd += " " + opt

    out_vcf = prlutil.strip_ext(os.path.basename(path), alext) + ext
    cmd += f" --fasta-ref {ref} --output {os.path.join(out_dir, out_vcf)} {path}"
    commands.append(cmd)

  return commands