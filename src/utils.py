"""
Utility functions for general use
"""

import logging

LOG_FORMAT = logging.Formatter(
  fmt="[%(asctime)s] %(levelname)s: %(message)s",
  datefmt="%Y-%m-%d %H:%M:%S"
)

def get_logger(name, level=logging.DEBUG):
  """
  Return basic logger with console handler
  """
  logging.basicConfig(level=level)
  logger = logging.getLogger(name)
  if logger.hasHandlers():
    logger.handlers.clear()
  logger.propagate = False

  handler = logging.StreamHandler()
  handler.setLevel(logging.INFO)
  handler.setFormatter(LOG_FORMAT)
  logger.addHandler(handler)

  return logger

log = get_logger("vardis")

def to_optstring(options=dict()):
  """
  Convert dictionary of options into args string for
  appending to cmds
  """
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