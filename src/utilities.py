from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import logging
import os
import subprocess
import tomllib

def parse_config(config_path, defaults = None):
  logger = logging.getLogger(__name__)
  logger.debug("Loading config file at '%s'", config_path)
  if os.path.exists(config_path):
    with open(config_path, "rb") as cf:
      try:
        config = tomllib.load(cf)
      except tomllib.TOMLDecodeError as err:
        logger.error(f"Config file processing failed: {err.msg}")
      except Exception as err:
        logger.error("An unexpected error occurred: %s", err)
      logger.info("Config file loaded.")
  elif isinstance(defaults, dict):
    config = defaults
    logger.debug("Default config provided: %s", str(defaults))
  else:
    config = dict()
    logger.error("Config file in '%s' not found. No fallback defaults provided.", config_path)

  return config

def init_project(folders):
  logger = logging.getLogger(__name__)
  for folder in folders:
    if not os.path.isdir(folder):
      os.makedirs(folder)
      logger.warning("Specified directory not found. Created directory '%s'", folder)

def strip_ext(path, ext):
  if isinstance(ext, str):
    ext = (ext,)

  for e in ext:
    if e[0] != '.':
      e = "." + e

    if path.endswith(e):
      return path[:-len(e)]
    
  return path
    
def filter_files(dir, ext):
  files = os.listdir(dir)

  if isinstance(ext, str):
    ext = (ext,)

  if not os.path.exists(dir):
    raise ValueError
  for e in ext:
    if e[0] != '.':
      raise ValueError

  # filter files
  filtered = []
  for f in files:
    if os.path.isdir(f):
      continue
    if f.endswith(ext):
      filtered.append(f)

  return filtered

def strip_flag(fname, ext, affix, flags):
  base_name = strip_ext(fname, ext)

  if affix != "prefix" and affix != "suffix":
      raise ValueError
  if len(flags) != 2:
    raise ValueError

  if affix == "prefix":
    for flg in flags:
      if base_name.startswith(flg):
        return base_name[len(flg):]
  elif affix == "suffix":
    for flg in flags:
      if base_name.endswith(flg):
        return base_name[:-len(flg)]

  return base_name

def make_paired_coll(dir, ext, affix="suffix", flags=("_1","_2")):
  if not os.path.exists(dir):
    raise ValueError
  if ext[0] != '.':
    raise ValueError
  if affix != "prefix" and affix != "suffix":
    raise ValueError
  if len(flags) != 2:
    raise ValueError

  paired_coll = {
    "affix": affix,
    "f1": flags[0],
    "f2": flags[1],
    "ext": ext,
    "items": []
  }

  files = [strip_flag(f, ext, affix, flags) for f in filter_files(dir, ext)]
  paired_coll["items"] = [f for f, i in Counter(files).items() if i > 1]

  return paired_coll

def get_files_from_coll(paired_coll):
  ext = paired_coll["ext"]
  affix = paired_coll["affix"]
  f1 = paired_coll["f1"]
  f2 = paired_coll["f2"]
  if affix == "prefix":
    fnames = [[f1 + b + ext, f2 + b + ext] for b in paired_coll["items"]]
  elif affix == "suffix":
    fnames = [[b + f1 + ext,  b + f2 + ext] for b in paired_coll["items"]]
  return fnames

def to_optstring(options):
  optstring = []
  for opt, val in options.items():
    if len(opt) > 1:
      prefix = "--"
    else:
      prefix = "-"

    if isinstance(val, bool):
      if val:
        optstring.append(prefix + opt)
    else:
      optstring.append(prefix + opt + " " + str(val))

  return optstring

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

def run_command(cmd):
  logger = logging.getLogger(__name__)
  logger.info("Running command: %s", cmd)
  try:
    run_result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
  except subprocess.CalledProcessError as err:
    if err.returncode == 127:
      logger.error(f"Command execution failed: Command not found. (127)")
    elif err.returncode == 126:
      logger.error(f"Command execution failed: Command can't be executed. (126)")
    elif err.returncode == 130:
      logger.error(f"Command execution failed: Command run interrupted. (130)")
    else:
      logger.error(f"Command execution failed: Shell raised exit code {err.returncode}")
    return None
  except Exception as err:
    logger.error("An unexpected error occurred: %s", err)
    return None

  if run_result.stderr != "":
    logger.error(run_result.stderr)

  logger.debug("Command execution completed.")
  return run_result.stdout

def run_pipeline(cmd_set):
  logger = logging.getLogger(__name__)
  logger.info("Queuing %s command(s):", len(cmd_set))

  result_set = []

  for pipeline in cmd_set:
    logger.info("Running pipeline - %s step(s):", len(pipeline))
    try:
      logger.info("Running command: %s", pipeline[0])
      pipe_in = subprocess.run(pipeline.pop(0), shell=True, capture_output=True, text=True, check=True)
      for c in pipeline:
        logger.info("Running command: %s", c)
        run_result = subprocess.run(c, shell=True, input=pipe_in.stdout, capture_output=True, text=True, check=True)
        pipe_in = run_result
    except subprocess.CalledProcessError as err:
      if err.returncode == 127:
        logger.error(f"Command execution failed: Command not found. (127)")
      elif err.returncode == 126:
        logger.error(f"Command execution failed: Command can't be executed. (126)")
      elif err.returncode == 130:
        logger.error(f"Command execution failed: Command run interrupted. (130)")
      else:
        logger.error(f"Command execution failed: Shell raised exit code {err.returncode}")
      return None
    except Exception as err:
      logger.error("An unexpected error occurred: %s", err)
      return None

    if run_result.stderr != "":
      logger.error(run_result.stderr)

    result_set.append(run_result.stdout)
  
  return result_set

def run_parallel(cmd_queue, procs=None):
  logger = logging.getLogger(__name__)
  if procs is None:
    procs = max(1, os.cpu_count() // 4)
  elif procs <= 0:
    procs = 1

  logger.debug("Performing %s tasks with %s worker(s)", len(cmd_queue), procs)
  with ProcessPoolExecutor(max_workers=procs) as executor:
    process_out = []
    try:
      futures = executor.map(run_command, cmd_queue)
      for res in futures:
        if res != None:
          process_out.append(res)
    except Exception as err:
      logger.error("An unexpected error occurred: %s", err)
  
  return process_out

def run_serial(cmd_queue):
  logger = logging.getLogger(__name__)
  process_out = []
  for cmd in cmd_queue:
    try:
      res = run_command(cmd)
      if res != None:
        process_out.append(res)
    except Exception as err:
      logger.error("An unexpected error occurred: %s", err)
  return process_out