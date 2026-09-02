#!/usr/bin/env python
# Based on the script for parallel implementation of fastp
# https://github.com/OpenGene/fastp/blob/cce79745e882a5794bae39a8b648b841a26d4529/parallel.py

import os
import copy

import src.utilities as prlutil

def process_folder(folder, infiles, options):
  fqext = (".fq", ".fastq", ".fq.gz", ".fastq.gz")
  flag_type = 'suffix'

  if 'flag_type' in infiles:
    flag_type = infiles['flag_type']  
  r1_flag = infiles['read1_flag']
  r2_flag = infiles['read2_flag']
  
  if not os.path.isdir(folder):
    return
      
  options_list = []
  processed = set()
  
  files = os.listdir(folder)
  for f in files:
    path = os.path.join(folder, f)
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
      opt = copy.copy(options)
      opt['read1_file'] = path
      read_dir, base_name = os.path.dirname(path), os.path.basename(path)
      mate_path = os.path.join(read_dir, base_name.replace(r1_flag, r2_flag))        
      if os.path.exists(mate_path):
        opt['read2_file'], opt['read_name'] = mate_path, prlutil.strip_ext(base_name, fqext).replace(r1_flag, '')
        processed.add(mate_path)
        options_list.append(opt)

  commands = []
  for opt in options_list:
    cmd = "fastp -i " + opt['read1_file']
    if 'read2_file' in opt:
      cmd += " -I " + opt['read2_file']
    if opt['out_dir']:
      if not os.path.exists(opt['out_dir']):
        os.makedirs(opt.out_dir)
      out_prefix1 = os.path.join(opt['out_dir'], os.path.basename(prlutil.strip_ext(opt['read1_file'], fqext)))
      cmd += " -o " + out_prefix1 + ".clean.fastq.gz"
      out_prefix2 = os.path.join(opt['out_dir'], os.path.basename(prlutil.strip_ext(opt['read2_file'], fqext)))
      cmd += " -O " + out_prefix2 + ".clean.fastq.gz"

    for arg_k, arg_v in opt['args'].items():
      if arg_v:
        cmd += " --" + arg_k
      elif len(arg_v) > 0:
        cmd += " --" + arg_k + "=" + str(arg_v)

    if 'rep_dir' in opt:
      if not os.path.exists(opt['rep_dir']):
        os.makedirs(opt['rep_dir'])
    
    report_file = os.path.join(opt['rep_dir'], opt['read_name'])
    cmd += " --html=" + report_file + ".html --json=" + report_file + ".json"
    
    commands.append(cmd)
  
  if len(options_list) == 0:
      print("No FASTQ file found, do you call the program correctly?")
      print("See -h for help")
      return

  return commands
    