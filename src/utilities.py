import os
import configparser
from concurrent.futures import ProcessPoolExecutor, wait, ALL_COMPLETED
import subprocess

def parse_config(config_path, config_defaults = None):
  config = configparser.ConfigParser()
  config['DEFAULT'] = dict()
  config_set = {}
  if config_defaults is not None:
    config.update(config_defaults)

  if os.path.exists(config_path):
    config.read(config_path)
    for sec in config.sections():
      config_set.update({sec: dict(config.items(sec))})
  else:
    print(f"Config file in {config_path} not found.")

  return config_set

def init_project(folders):
  for folder in folders:
    if not os.path.isdir(folder):
      os.makedirs(folder)

def run_command(cmd):
  print("Running command: " + cmd)
  try:
    run_result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
  except Exception as err:
    print(f"Execution failed: {err}")
    return err

  return run_result.stdout

def run_parallel(cmd_queue, procs=None):
  if procs is None:
    procs = max(1, os.cpu_count() // 4)

  subprocess.run('set -euo pipefail', shell=True)
  with ProcessPoolExecutor(max_workers=procs) as executor:
    try:
      run_results = executor.map(run_command, cmd_queue)
      wait(run_results, return_when=ALL_COMPLETED)
    except Exception as err:
      print(f"Error occurred: {err}")
  
  return run_results