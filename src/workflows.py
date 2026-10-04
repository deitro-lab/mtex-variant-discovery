import os.path as op
from .preprocessing import prep_read
from .mapping import is_indexed, index_ref, map_read
from .formats import SeqFile, get_paired_reads, filter_files, EXT_FA
from .utils import log

def batch_preprocess(in_dir, in_flags = ("_1", "_2"), out_flag = "clean", out_dir = None, rep_dir = None, options = dict()):
  if not op.isdir(in_dir):
    log.error("Specified input directory not found.")
    raise ValueError

  commands = []

  for rpair in get_paired_reads(in_dir, in_flags):
    try:
      cmd = prep_read(rpair, out_flag, out_dir, rep_dir, options)
      commands.append(cmd)
    except Exception as e:
      log.error("Batch preprocessing encountered an unexpected error. %s", e)
    
  return commands

def batch_index(ref_dir, aligner = "bwa-mem2", options = dict()):
  if not op.isdir(ref_dir):
    log.error("Specified reference directory not found.")
    raise ValueError

  commands = []

  for rpath in filter_files(ref_dir, EXT_FA):
    ref = SeqFile(ref_dir, rpath)
    if is_indexed(ref.get_path(), aligner):
      log.info("Reference file %s already indexed.", ref)
    else:
      try:
        cmd = index_ref(ref, aligner, options)
        commands.append(cmd)
      except Exception as e:
        log.error("Batch indexing encountered an unexpected error. %s", e)

  return commands

def batch_map(in_dir, ref_path, in_flags = ("_1", "_2"), prep_flag = ".clean", out_dir = None, aligner = "bwa-mem2", is_compress = False, options = dict()):
  if not op.isdir(in_dir):
    log.error("Specified input directory not found.")
    raise ValueError
  if not op.exists(ref_path):
    log.error("Reference file does not exist.")
    raise ValueError
  
  commands = []

  ref = SeqFile(*op.split(ref_path))
  for rpair in get_paired_reads(in_dir, in_flags, prep_flag):
    try:
      cmd = map_read(rpair, ref, out_dir, aligner, is_compress, options)
      commands.append(cmd)
    except Exception as e:
      log.error("Batch mapping encountered an unexpected error. %s", e)

  return commands