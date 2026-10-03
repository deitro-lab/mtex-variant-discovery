import os.path as op
from .utils import log, to_optstring

def is_indexed(path, aligner):
  if aligner == "bwa-mem2":
    idxext = (".0123", ".amb", ".ann", ".bwt.2bit.64", ".pac")
  elif aligner == "minibwa":
    idxext = (".l2b", ".mbw")
  else:
    idxext = ()

  for ext in idxext:
    if not op.exists(path + ext):
      return False

  return True

def index_ref(ref, aligner = "bwa-mem2", options=dict()):
  if aligner == "bwa-mem2":
    cmd = f"bwa-mem2 index"
  elif aligner == "minibwa":
    cmd = "minibwa index"

  for opt in to_optstring(options):
    cmd += " " + opt
  cmd += " " + ref.get_path()

  return cmd

def map_read(paired_coll, ref, out_dir = None, aligner = "bwa-mem2", is_compress = False, options = dict()):
  if out_dir == None:
    log.warning("No output directory specified.")
    out_dir = "."
  if not op.isdir(out_dir):
    log.error("Specified output directory not found.")
    raise ValueError
  if paired_coll.base.format != "fq" or ref.format != "fa":
    log.error("Invalid file type(s) detected.")
    raise ValueError
  if not is_indexed(ref.get_path(), aligner):
    log.error("Missing index file(s). Perform reference indexing first.")
    raise ValueError

  if aligner == "bwa-mem2":
    cmd = "bwa-mem2 mem"
  elif aligner == "minibwa":
    cmd = "minibwa map"
  else:
    cmd = None
  for opt in to_optstring(options):
    cmd += " " + opt

  r1_in, r2_in = paired_coll.get_paths()
  if aligner == "bwa-mem2" or aligner == "minibwa":
    if is_compress:
      cmd += f" {ref.get_path()} {r1_in} {r2_in} | samtools view -b -o {op.join(out_dir, paired_coll.base.name + '.bam')}"
    else:
      cmd += f" {ref.get_path()} {r1_in} {r2_in} > {op.join(out_dir, paired_coll.base.name + '.sam')}"

  return cmd