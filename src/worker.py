"""
Manager for running generated command strings
via subprocess module
"""

from concurrent.futures import ProcessPoolExecutor
import os
import subprocess

from .utils import log

def run_command(cmd, stdin=None):
  """
  Execute single command string
  """
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
  """
  Execute list of commands as a pipeline
  Note: unsuitable for processes with heavy output,
  may exceed buffer limit
  """
  log.info("Queuing %s command(s):", len(cmd_set))

  result_set = []

  pipe_in = run_command(cmd_set.pop(0))
  for cmd in cmd_set:
    run_result = run_command(cmd, pipe_in)
    pipe_in = run_result

    result_set.append(run_result)
  
  return result_set

def run_parallel(cmd_queue, procs=None):
  """
  Execute multiple commands in parallel via
  multiprocessing
  Specify procs as max number of parallel tasks
  """
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
  """
  Execute multiple commands sequentially
  Can be used as alternative for run_parallel in
  low-resource setting
  """
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