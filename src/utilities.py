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

# def prompt_flag(msg):
#   msg_flag = ""
#   while msg_flag.lower() not in ("y", "yes", "n", "no"):
#     msg_flag = input(msg)

#   return (msg_flag == "y" or msg_flag == "yes")

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