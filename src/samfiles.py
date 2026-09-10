#!/usr/bin/env python

import logging
import os

import src.utilities as prlutil

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
  if (mode == "inout" or mode == "out") and not os.path.isdir(out_dir):
    logger.error("Specified output directory not found.")
    raise ValueError
  if not os.path.isdir(temp_dir):
    logger.error("Specified temporary files directory not found.")
    raise ValueError

def collate_sam(map_file=None, out_dir=None, temp_dir=None, mode="inout", options=dict()):
  logger = logging.getLogger(__name__)

  try:
    check_args(map_file, out_dir, temp_dir, mode)
  except ValueError:
    raise

  base_name = os.path.splitext(os.path.basename(map_file))[0]
  f_out = ""
  cmd = f"samtools collate -T {os.path.join(temp_dir, base_name)}"
  if mode == "inout" or mode == "out":
    cmd += " -o"
  else:
    cmd += " -O"

  for opt in prlutil.to_optstring(options):
    cmd += " " + opt

  if mode == "inout" or mode == "in":
    cmd += " " + map_file
  if mode == "inout" or mode == "out":
    f_out = os.path.join(out_dir, base_name + ".coll")
    cmd += " " + f_out

  return (cmd, f_out)

def fixmate_sam(map_file, out_dir=None, temp_dir=".", mode="inout", options=dict()):
  logger = logging.getLogger(__name__)

  try:
    check_args(map_file, out_dir, temp_dir, mode)
  except ValueError:
    raise

  f_out = ""
  cmd = "samtools fixmate"
  for opt in prlutil.to_optstring(options):
    cmd += " " + opt

  base_name = os.path.splitext(os.path.basename(map_file))[0] + ".fm"
  if mode == "inout" or mode == "in":
    cmd += " " + map_file

  if "O" in options.keys():
    f_out = os.path.join(out_dir, base_name + "." + options["O"].lower())
    cmd += " " + f_out
  elif "output-fmt" in options.keys():
    f_out = os.path.join(out_dir, base_name + "." + options["output-fmt"].lower())
    cmd += " " + f_out
  else:
    f_out = os.path.join(out_dir, base_name + ".bam")
    cmd += " " + f_out

  return (cmd, f_out)

def sort_sam(map_file=None, out_dir=None, temp_dir=None, sorting="", mode="inout", options=dict()):
  logger = logging.getLogger(__name__)

  try:
    check_args(map_file, out_dir, temp_dir, mode)
  except ValueError:
    raise
  if not isinstance(sorting, str):
    raise ValueError
  
  base_name = os.path.splitext(os.path.basename(map_file))[0]
  f_out = ""
  cmd = f"samtools sort -T {os.path.join(temp_dir, base_name)}"
  if sorting.lower() == "n" or (sorting.startswith("t ") and len(sorting.strip()) > 2):
    cmd += " -" + sorting

  for opt in prlutil.to_optstring(options):
    cmd += " " + opt

  if mode == "inout" or mode == "out":
    base_name += ".sorted"
    if "O" in options.keys():
      f_out = os.path.join(out_dir, base_name + "." + options["O"].lower())
      cmd += " -o " + f_out
    elif "output-fmt" in options.keys():
      f_out = os.path.join(out_dir, base_name + "." + options["output-fmt"].lower())
      cmd += " -o " + f_out
    else:
      f_out = os.path.join(out_dir, base_name + ".bam")
      cmd += " -o " + f_out
  if mode == "inout" or mode == "in":
    cmd += " " + map_file

  return (cmd, f_out)

def markdup_sam(map_file=None, out_dir=None, temp_dir=None, mode="inout", options=dict()):
  logger = logging.getLogger(__name__)

  try:
    check_args(map_file, out_dir, temp_dir, mode)
  except ValueError:
    raise

  base_name = os.path.splitext(os.path.basename(map_file))[0]
  f_out = ""
  cmd = f"samtools markdup -T {os.path.join(temp_dir, base_name)}"
  for opt in prlutil.to_optstring(options):
    cmd += " " + opt

  if mode == "inout" or mode == "in":
    cmd += " " + map_file

  base_name += ".dedup"
  if "O" in options.keys():
    f_out = os.path.join(out_dir, base_name + "." + options["O"].lower())
    cmd += " " + f_out
  elif "output-fmt" in options.keys():
    f_out = os.path.join(out_dir, base_name + "." + options["output-fmt"].lower())
    cmd += " " + f_out
  else:
    f_out = os.path.join(out_dir, base_name + ".bam")
    cmd += " " + f_out
    
  return (cmd, f_out)

def index_sam(ref_dir, options=dict()):
  faext = (".fasta", ".fa", ".fa.gz", ".fasta.gz")
  commands = []

  if not os.path.isdir(ref_dir):
    raise ValueError

  processed = set() 

  for file in prlutil.filter_files(ref_dir, faext):
    path = os.path.join(ref_dir, file)

    if os.path.exists(path + ".fai"):
      continue

    processed.add(path)

    cmd = f"samtools faidx {path}"

    for opt in prlutil.to_optstring(options):
      cmd += " " + opt

    commands.append(cmd)

  return commands

def dedup_files(files, in_dir, out_dir, temp_dir, opt_set):
  logger = logging.getLogger(__name__)

  if not os.path.isdir(in_dir):
    logger.error("Specified input directory not found.")
    raise ValueError
  if not os.path.isdir(out_dir):
    logger.error("Specified output directory not found.")
    raise ValueError
  if not os.path.isdir(temp_dir):
    logger.error("Specified temporary files directory not found.")
    raise ValueError
  if not {"collate","fixmate","sort","markdup"} <= set(opt_set.keys()):
    logger.error("Missing options for samtools collate/fixmate/sort/markdup.")
    raise ValueError

  if not "m" in opt_set["fixmate"].keys():
    opt_set["fixmate"].update({"m": True})
  for k in ("n", "N", "t"):
    opt_set["sort"].pop(k, None)

  commands = []

  processed = set()

  for f in files:
    cmd_set = []
    path = os.path.join(in_dir, f)

    if not os.path.exists(path):
      continue
    if path in processed:
      continue

    processed.add(path)

    cmd_set.append(collate_sam(
      map_file=path,
      out_dir=out_dir,
      temp_dir=temp_dir,
      mode="in",
      options=opt_set["collate"]
    )[0])
    fm_cmd = fixmate_sam(
      map_file=path,
      out_dir=out_dir,
      temp_dir=temp_dir,
      mode="pipe",
      options=opt_set["fixmate"]
    )
    sort_cmd = sort_sam(
      map_file=fm_cmd[1],
      temp_dir=temp_dir,
      mode="in",
      options=opt_set["sort"]
    )[0]
    cmd_set.append(fm_cmd[0] + " && " + sort_cmd)
    cmd_set.append(markdup_sam(
      map_file=path,
      out_dir=out_dir,
      temp_dir=temp_dir,
      mode="out",
      options=opt_set["markdup"]
    )[0])

    commands.append(cmd_set)
  return commands