#!/usr/bin/env python

import time
from datetime import timedelta
import copy
import src.utilities as prlutil
import src.preprocessing as prlprep
import src.mapping as prlmap

def main():
  time_start = time.perf_counter()

  # config_dir = input("Enter path for config file: ")
  config_dir = './var.local.config'
  options = prlutil.parse_config(config_dir)
  dir_list = options['DIRECTORIES']

  if 'in_dir' not in options:
    options.update({'in_dir': '.'})
  if 'report_dir' not in options:
    if 'out_dir' in options:
      options.update({'report_dir': options['out_dir']})
    else:
      options.update({'report_dir': options['in_dir']})    

  prlutil.init_project(dir_list.values())

  # Step 1: preprocessing
  has_prep = ''
  while has_prep.lower() not in ('y', 'yes', 'n', 'no'):
    has_prep = input("Perform preprocessing step? (Y/N): ")
  if has_prep == 'y' or has_prep == 'yes':
    fastp_cmd = prlprep.process_folder(dir_list['in_dir'], options['PARAM:INPUT'], {**dir_list, 'args': copy.copy(options['OPTIONS:FASTP'])})
    prlutil.run_parallel(fastp_cmd, 6)

  # Step 2.1: Reference indexing
  has_idx = ''
  while has_idx.lower() not in ('y', 'yes', 'n', 'no'):
    has_idx = input("Perform reference indexing? (Y/N): ")
  if has_idx == 'y' or has_idx == 'yes':
    idx_cmd = prlmap.index_ref(dir_list['ref_dir'])
    prlutil.run_parallel(idx_cmd)

  time_span = timedelta(seconds=time.perf_counter()-time_start)
  print('Time used: ', time_span)

if __name__ == "__main__":
  main()