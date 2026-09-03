#!/usr/bin/env python
# Based on the script for parallel implementation of fastp
# https://github.com/OpenGene/fastp/blob/cce79745e882a5794bae39a8b648b841a26d4529/parallel.py

import os

import src.utilities as prlutil

def prep_reads(in_dir, out_dir, rep_dir = None, flags = {"flag_type": "suffix", "read1_flag": "_1", "read2_flag": "_2"}, **options):
  fqext = (".fq", ".fastq", ".fq.gz", ".fastq.gz")
  flag_type = flags["flag_type"]
  r1_flag = flags["read1_flag"]
  r2_flag = flags["read2_flag"]
  
  if not os.path.isdir(in_dir):
    return
      
  options_list = []
  processed = set()
  
  files = os.listdir(in_dir)
  for f in files:
    path = os.path.join(in_dir, f)
    if os.path.isdir(path): # skip subdir
      continue
    
    if not f.endswith(fqext):
      continue

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
        opt["read2_file"], opt["read_name"] = mate_path, prlutil.strip_ext(base_name, fqext).replace(r1_flag, '')
        processed.add(mate_path)
        options_list.append(opt)
      else:
        continue

  commands = []
  for opt in options_list:
    cmd = "fastp -i " + opt["read1_file"] + " -I " + opt["read2_file"]
    if not os.path.exists(out_dir):
      os.makedirs(out_dir)
    out_prefix1 = os.path.join(out_dir, os.path.basename(prlutil.strip_ext(opt["read1_file"], fqext)))
    cmd += " -o " + out_prefix1 + ".clean.fastq.gz"
    out_prefix2 = os.path.join(out_dir, os.path.basename(prlutil.strip_ext(opt["read2_file"], fqext)))
    cmd += " -O " + out_prefix2 + ".clean.fastq.gz"

    for arg_k, arg_v in opt["args"].items():
      if type(arg_v) == bool:
        if arg_v:
          cmd += " --" + arg_k
      else:
        cmd += " --" + arg_k + "=" + str(arg_v)

    if rep_dir != None:
      if not os.path.exists(rep_dir):
        os.makedirs(rep_dir)
      
      report_file = os.path.join(rep_dir, opt["read_name"])
      cmd += " --html=" + report_file + ".html --json=" + report_file + ".json"
    
    commands.append(cmd)

  if len(options_list) == 0:
      print("No FASTQ file found, do you call the program correctly?")
      print("See -h for help")
      return

  return commands