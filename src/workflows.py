import os.path as op
from .preprocessing import prep_read
from .formats import get_paired_reads
from .utils import log

def batch_preprocess(in_dir, in_flags, out_flag = "clean", out_dir = None, rep_dir = None, options = dict()):
  if not op.isdir(in_dir):
    log.error("Specified input directory not found.")
    raise ValueError

  commands = []

  for rpair in get_paired_reads(in_dir, in_flags):
    try:
      cmd = prep_read(rpair, out_flag, out_dir, rep_dir, options)
    except Exception as e:
      log.error("Preprocessing workflow encountered an unexpected error. %s", e)
    commands.append(cmd)
    
  return commands