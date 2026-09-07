from concurrent.futures import ProcessPoolExecutor
import logging
import os
import subprocess
import tomllib

def parse_config(config_path, defaults = None):
  logger = logging.getLogger(__name__)
  if os.path.exists(config_path):
    with open(config_path, "rb") as cf:
      config = tomllib.load(cf)
  elif isinstance(defaults, dict):
    config = defaults
    logger.info("Default config provided: %s", str(defaults))
  else:
    config = dict()
    print(f"Config file in '{config_path}' not found.")
    logger.error("Config file in '%s' not found. No fallback defaults provided.", config_path)
  return config

def init_project(folders):
  for folder in folders:
    if not os.path.isdir(folder):
      os.makedirs(folder)

def prompt_flag(msg):
  msg_flag = ""
  while msg_flag.lower() not in ("y", "yes", "n", "no"):
    msg_flag = input(msg)

  return (msg_flag == "y" or msg_flag == "yes")

def match_flag(filename, flag, pos):
  if pos == "suffix":
    if flag.endswith(".") or flag.endswith("_") or flag.endswith("-"):
        return flag in filename
    else:
      return (flag + "." in filename) or (flag + "_" in filename) or (flag + "-" in filename)
  elif pos == "prefix":
    if flag.startswith(".") or flag.startswith("_") or flag.startswith("-"):
        return flag in filename
    else:
      return ("." + flag in filename) or ("_" + flag in filename) or ("-" + flag in filename)

def strip_ext(filename, ext):
  for e in ext:
    if filename.endswith(e):
      return filename[:-len(e)]

def run_command(cmd):
  print("Running command: " + cmd)
  try:
    run_result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
  except Exception as err:
    print(f"Execution failed: {err}")
    return err

  if run_result.stderr != "":
    print(run_result.stderr)

  return run_result.stdout

def run_parallel(cmd_queue, procs=None):
  if procs is None:
    procs = max(1, os.cpu_count() // 4)

  with ProcessPoolExecutor(max_workers=procs) as executor:
    process_out = []
    try:
      futures = executor.map(run_command, cmd_queue)
      for res in futures:
        process_out.append(res)
    except Exception as err:
      print(f"Error occurred: {err}")
  
  return process_out

def run_serial(cmd_queue):
  process_out = []
  for cmd in cmd_queue:
    try:
      process_out.append(run_command(cmd))
    except Exception as err:
      print(f"Error occurred: {err}")
  return process_out