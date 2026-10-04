from concurrent.futures import ProcessPoolExecutor
import logging
import os
import subprocess
import tomllib

def get_logger(name, level=logging.INFO):
  logging.basicConfig(level=level)
  logger = logging.getLogger(name)
  if logger.hasHandlers():
    logger.handlers.clear()
  logger.propagate = False

  handler = logging.StreamHandler()
  handler.setLevel(level)
  handler.setFormatter(logging.Formatter(
    fmt="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
  ))
  logger.addHandler(handler)

  return logger

log = get_logger("vardis")

def parse_config(config_path, defaults = None):
  log.debug("Loading config file at '%s'", config_path)
  if os.path.exists(config_path):
    with open(config_path, "rb") as cf:
      try:
        config = tomllib.load(cf)
      except tomllib.TOMLDecodeError as err:
        log.error(f"Config file processing failed: {err.msg}")
      except Exception as err:
        log.error("An unexpected error occurred: %s", err)
      log.info("Config file loaded.")
  elif isinstance(defaults, dict):
    config = defaults
    log.debug("Default config provided: %s", str(defaults))
  else:
    config = dict()
    log.error("Config file in '%s' not found. No fallback defaults provided.", config_path)

  return config

def init_project(folders):
  for folder in folders:
    if not os.path.isdir(folder):
      os.makedirs(folder)
      log.warning("Specified directory not found. Created directory '%s'", folder)

def to_optstring(options=dict()):
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

def run_command(cmd, stdin=None):
  log.info("Running command: %s", cmd)
  try:
    if stdin == None:
      run_result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
    else:
      run_result = subprocess.run(cmd, shell=True, input=stdin, capture_output=True, text=True, check=True)
  except subprocess.CalledProcessError as err:
    if err.returncode == 127:
      log.error(f"Command execution failed: Command not found. (127)")
    elif err.returncode == 126:
      log.error(f"Command execution failed: Command can't be executed. (126)")
    elif err.returncode == 130:
      log.error(f"Command execution failed: Command run interrupted. (130)")
    else:
      log.error(f"Command execution failed: Shell raised exit code {err.returncode}")
    return None
  except Exception as err:
    log.error("An unexpected error occurred: %s", err)
    return None

  if run_result.stderr != "":
    log.error(run_result.stderr)

  log.debug("Command execution completed.")
  return run_result.stdout

def run_pipeline(cmd_set):
  log.info("Queuing %s command(s):", len(cmd_set))

  result_set = []

  pipe_in = run_command(cmd_set.pop(0))
  for cmd in cmd_set:
    run_result = run_command(cmd, pipe_in)
    pipe_in = run_result

    result_set.append(run_result)
  
  return result_set

def run_parallel(cmd_queue, procs=None):
  logger = logging.getLogger(__name__)
  if procs is None:
    procs = max(1, os.cpu_count() // 4)
  elif procs <= 0:
    procs = 1

  log.debug("Performing %s tasks with %s worker(s)", len(cmd_queue), procs)
  with ProcessPoolExecutor(max_workers=procs) as executor:
    process_out = []
    try:
      if any(isinstance(c, list) for c in cmd_queue):
        futures = executor.map(run_pipeline, cmd_queue)
      else:
        futures = executor.map(run_command, cmd_queue)

      for res in futures:
        if res != None:
          process_out.append(res)
    except Exception as err:
      log.error("An unexpected error occurred: %s", err)
  
  return process_out

def run_serial(cmd_queue):
  process_out = []
  
  if any(isinstance(c, list) for c in cmd_queue):
    try:
      res = run_pipeline(cmd_queue)
      if res != None:
        process_out.append(res)
    except Exception as err:
      log.error("An unexpected error occurred: %s", err)
  else:
    for cmd in cmd_queue:
      try:
        res = run_command(cmd)
        if res != None:
          process_out.append(res)
      except Exception as err:
        log.error("An unexpected error occurred: %s", err)

  return process_out