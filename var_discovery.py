#!/usr/bin/env python

import time, os
from datetime import timedelta
import copy
import src.utilities as prlutil
import src.preprocessing as prlprep

def main():
  time_start = time.perf_counter()

  config_dir = input("Enter path for config file: ")
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
  fastp_cmd = prlprep.process_folder(dir_list['in_dir'], options['PARAM:INPUT'], {**dir_list, 'args': copy.copy(options['OPTIONS:FASTP'])})

  time_span = timedelta(seconds=time.perf_counter()-time_start)
  print('Time used: ', time_span)

if __name__ == "__main__":
  main()