#!/usr/bin/env python

import time, os

import src.utilities as prlutil

def main():
  time_start = time.time()

  # config_dir = input("Enter path for config file: ")
  config_dir = './var.config'
  options = prlutil.parse_config(config_dir)
  dir_list = options['DIRECTORIES']

  if 'in_dir' not in options.keys():
    options.update({'in_dir': '.'})
  if 'report_dir' not in options.keys():
    if 'out_dir' in options.keys():
      options.update({'report_dir': options['out_dir']})
    else:
      options.update({'report_dir': options['in_dir']})    

  prlutil.init_project(dir_list.values())

  # print(options)

  
  time_end = time.time()
  print('Time used: ' + str(time_end-time_start))

if __name__ == "__main__":
  main()