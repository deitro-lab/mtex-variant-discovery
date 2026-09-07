#!/usr/bin/env python

import os
import copy

import src.utilities as prlutil

def index_refs(aligner="bwa-mem2", ref_dir=".", **options):
  faext = (".fasta", ".fa", ".fna", ".fas")
  idxext = (".0123", ".amb", ".ann", ".bwt.2bit.64", ".pac")
  commands = []

  processed = set() 

  files = os.listdir(ref_dir)
  for file in files:
    path = os.path.join(ref_dir, file)
    if os.path.isdir(path):
      continue
        
    if os.path.exists(path):
      if not path.endswith(faext):
        continue

      is_indexed = True
      for ext in idxext:
        if not os.path.exists(path + ext):
          is_indexed = False
          break

      processed.add(path)
      if not is_indexed:
        if aligner == "bwa-mem2":
          cmd = f"bwa-mem2 index {path}"
        elif aligner == "minibwa":
          cmd = "minibwa index"
          for arg_k, arg_v in options.items():
            if type(arg_v) == bool:
              if arg_v:
                cmd += " -" + arg_k
            else:
              cmd += " -" + arg_k + " " + str(arg_v)

          cmd += " " + path

        commands.append(cmd)

  return commands

def map_reads(aligner, in_dir, ref_dir, in_opts, **options):
  faext = (".fasta", ".fa", ".fna", ".fas")
  flag_type = in_opts["flag_type"]
  r1_flag = in_opts["read1_flag"]
  r2_flag = in_opts["read2_flag"]
  prep_ext = in_opts["prep_ext"]

  if not os.path.isdir(in_dir):
    print("Input directory not found.")
    return
  
  if "ref_file" not in in_opts:
    print("No valid reference file found.")
    return
  else:
    ref = os.path.join(ref_dir, in_opts["ref_file"])
    if not ref.endswith(faext) or not os.path.exists(ref):
      print("Specified reference file is invalid.")
      return
  
  options_list = []
  processed = set()
  
  files = filter(lambda c: c.endswith(prep_ext), os.listdir(in_dir))
  for f in files:
    path = os.path.join(in_dir, f)
    
    if path in processed:
      continue

    if prlutil.match_flag(f, r2_flag, flag_type):
      continue

    processed.add(path)

    if f.startswith("Undetermined"):
      continue

    if prlutil.match_flag(f, r1_flag, flag_type):
      opt = {"args": options}
      opt["read1_file"] = path
      read_dir, base_name = os.path.dirname(path), os.path.basename(path)
      mate_path = os.path.join(read_dir, base_name.replace(r1_flag, r2_flag))        
      if os.path.exists(mate_path):
        # TODO: more robust extraction of read_name
        opt["read2_file"], opt["read_name"] = mate_path, prlutil.strip_ext(base_name, [prep_ext]).replace(r1_flag, '')
        processed.add(mate_path)
        options_list.append(opt)
      else:
        continue

  commands = []
  for opt in options_list:
    if aligner == "bwa-mem2":
      cmd = "bwa-mem2 mem"
    elif aligner == "minibwa":
      cmd = "minibwa map"

    for arg_k, arg_v in opt["args"].items():
      if type(arg_v) == bool:
        if arg_v:
          cmd += " -" + arg_k
      else:
        cmd += " -" + arg_k + " " + str(arg_v)

    cmd += " " + ref + " " + opt["read1_file"] + " " + opt["read2_file"]
    
    commands.append(cmd)
  
  if len(options_list) == 0:
    print("No FASTQ file found. Check your specified input directory.")
    return

  return commands