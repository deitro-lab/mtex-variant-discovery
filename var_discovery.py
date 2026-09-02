#!/usr/bin/env python

import time
from datetime import timedelta
import copy

import src.utilities as prlutil
import src.preprocessing as prlprep
import src.mapping as prlmap

def main():
  time_start = time.perf_counter()
  mock = True

  # config_dir = input("Enter path for config file: ")
  config_dir = './config.toml'
  options = prlutil.parse_config(config_dir)
  dir_list = options['directories']

  if 'in_dir' not in options:
    options.update({'in_dir': '.'})
  if 'report_dir' not in options:
    if 'out_dir' in options:
      options.update({'report_dir': options['out_dir']})
    else:
      options.update({'report_dir': options['in_dir']})    

  prlutil.init_project(dir_list.values())

  # Step 1: preprocessing
  if prlutil.prompt_flag("Perform preprocessing step? (Y/N): "):
    fastp_cmd = prlprep.process_folder(dir_list['in_dir'], options['input'], {**dir_list, 'args': copy.copy(options['options']['fastp'])})
    if not mock:
      prlutil.run_parallel(fastp_cmd, 6)
    else:
      print(fastp_cmd)

  # Step 2.1: Reference indexing
  if prlutil.prompt_flag("Perform reference indexing? (Y/N): "):
    idx_cmd = prlmap.index_ref(dir_list['ref_dir'])
    if not mock:
      prlutil.run_parallel(idx_cmd)
    else:
      print(idx_cmd)

  # Step 2.2: Read mapping
  # if prlutil.prompt_flag("Map reads to reference? (Y/N): "):
  #   map_cmd = prlmap.map_reads(dir_list['in_dir'], options['PARAM:INPUT'], options['OPTIONS:BWA-MEM'])
  #   if not mock:
  #     prlutil.run_parallel(idx_cmd)
  #   else:
  #     print(map_cmd)

  time_span = timedelta(seconds=time.perf_counter()-time_start)
  print('Time used: ', time_span)

if __name__ == "__main__":
  main()