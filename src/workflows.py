import os.path as op
from .preprocessing import prep_read
from .mapping import is_indexed, index_ref, map_read
from .formats import SeqFile, get_paired_reads, filter_files, EXT_FA, EXT_SAM
from .samfiles import collate_sam, fixmate_sam, markdup_sam, sort_sam, index_sam
from .utils import log
from .varcall import bcft_mpileup

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

def batch_dedup(in_dir, out_dir = None, tmp_dir = None, opt_set = dict()):
  if not op.isdir(in_dir):
    log.error("Specified input directory not found.")
    raise ValueError
  if len(opt_set) == 0:
    opt_set.update({"collate": dict()})
    opt_set.update({"fixmate": dict()})
    opt_set.update({"sort": dict()})
    opt_set.update({"markdup": dict()})

  if "m" not in opt_set["fixmate"].keys():
    opt_set["fixmate"].update({"m": True})
  for k in ("n", "N", "t"):
    opt_set["sort"].pop(k, None)
  
  commands = []

  for spath in filter_files(in_dir, EXT_SAM):
    sam = SeqFile(in_dir, spath)

    if len(sam.flags) > 0:
      continue

    try:
      cmd_pipe = collate_sam(
        map_file=sam,
        out_dir=out_dir,
        tmp_dir=tmp_dir,
        mode="in",
        options=opt_set["collate"]
      )[0]
      fm_cmd = fixmate_sam(
        map_file=sam,
        out_dir=out_dir,
        mode="pipe",
        options=opt_set["fixmate"]
      )[0]
      sort_cmd = sort_sam(
        map_file=sam,
        out_dir=out_dir,
        tmp_dir=tmp_dir,
        mode="pipe",
        options=opt_set["sort"]
      )[0]
      cmd_pipe += " | " + fm_cmd + " | " + sort_cmd
      cmd_pipe += " | " + markdup_sam(
        map_file=sam,
        out_dir=out_dir,
        tmp_dir=tmp_dir,
        mode="out",
        options=opt_set["markdup"]
      )[0]
      commands.append(cmd_pipe)
    except Exception as e:
      log.error("Batch deduplication encountered an unexpected error. %s", e)

  return commands

def batch_genotype(in_dir, ref_path, in_flag = ".dedup", out_dir = None, options = dict()):
  if not op.isdir(in_dir):
    log.error("Specified input directory not found.")
    raise ValueError
  if not op.exists(ref_path):
    log.error("Reference file does not exist.")
    raise ValueError
  
  commands = []

  ref = SeqFile(*op.split(ref_path))
  try:
    commands.append(index_sam(ref))
  except Exception as e:
    log.error("Indexing step encountered an unexpected error. %s", e)
    return commands

  query = tuple([in_flag + ex for ex in EXT_SAM])
  for spath in filter_files(in_dir, query, False):
    sam = SeqFile(in_dir, spath)
    try:
      cmd = bcft_mpileup(sam, ref, out_dir, options)
      commands.append(cmd)
    except Exception as e:
      log.error("Batch calculation of genotype likelihood encountered an unexpected error. %s", e)

  return commands