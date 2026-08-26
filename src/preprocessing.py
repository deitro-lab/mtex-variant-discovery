#!/usr/bin/env python
# Based on the script for parallel implementation of fastp
# https://github.com/OpenGene/fastp/blob/cce79745e882a5794bae39a8b648b841a26d4529/parallel.py

import os
import copy 

def match_flag(filename, flag, pos):
  if pos == 'prefix':
    if flag.endswith('.') or flag.endswith('_') or flag.endswith('-'):
        return flag in filename
    else:
      return (flag + "." in filename) or (flag + "_" in filename) or (flag + "-" in filename)
  elif pos == 'suffix':
    if flag.startswith('.') or flag.startswith('_') or flag.startswith('-'):
        return flag in filename
    else:
      return ("." + flag in filename) or ("_" + flag in filename) or ("-" + flag in filename)

def strip_fqext(filename):
  fqext = (".fq.gz", ".fastq.gz", ".fq", ".fastq")
  for ext in fqext:
    if filename.endswith(ext):
      return filename[:-len(ext)]

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

    if match_flag(f, r2_flag, flag_type):
      continue

    processed.add(path)

    if f.startswith("Undetermined"):
      continue

    if match_flag(f, r1_flag, flag_type):
      opt = copy.copy(options)
      opt['read1_file'] = path
      read_dir, base_name = os.path.dirname(path), os.path.basename(path)
      mate_path = os.path.join(read_dir, base_name.replace(r1_flag, r2_flag))        
      if os.path.exists(mate_path):
        opt['read2_file'], opt['read_name'] = mate_path, strip_fqext(base_name).replace(r1_flag, '')
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
      out_prefix1 = os.path.join(opt['out_dir'], os.path.basename(strip_fqext(opt['read1_file'])))
      cmd += " -o " + out_prefix1 + ".clean.fastq.gz"
      out_prefix2 = os.path.join(opt['out_dir'], os.path.basename(strip_fqext(opt['read2_file'])))
      cmd += " -O " + out_prefix2 + ".clean.fastq.gz"

    for arg_k, arg_v in opt['args'].items():
      if arg_v.upper() == 'TRUE':
        cmd += " --" + arg_k
      elif len(arg_v) > 0:
        cmd += " --" + arg_k + "=" + arg_v

    if 'report_dir' in opt:
      if not os.path.exists(opt['report_dir']):
        os.makedirs(opt['report_dir'])
    
    report_file = os.path.join(opt['report_dir'], opt['read_name'])
    cmd += " --html=" + report_file + ".html --json=" + report_file + ".json"
    
    commands.append(cmd)
  
  if len(options_list) == 0:
      print("No FASTQ file found, do you call the program correctly?")
      print("See -h for help")
      return

  return commands
    