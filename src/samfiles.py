import os.path as op
from .utils import log, to_optstring

def collate_sam(map_file, out_dir = None, out_flag = ".coll", tmp_dir = None, mode = "inout", options = dict()):
  if out_dir == None:
    log.warning("No output directory specified.")
    out_dir = "."
  if tmp_dir == None:
    log.warning("No temp files directory specified.")
    tmp_dir = "."
  if map_file.format != "sam":
    log.error("Invalid file type detected.")
    raise ValueError
  if mode not in ("pipe", "in", "out", "inout"):
    log.error("Invalid mode specified.")
    raise ValueError

  f_out = ""
  cmd = f"samtools collate -T {op.join(tmp_dir, map_file.name)}"
  for opt in to_optstring(options):
    cmd += " " + opt

  if mode == "inout" or mode == "out":
    f_out = op.join(out_dir, map_file.name + out_flag)
    if "output-fmt" in options.keys():
      f_out += "." + options["output-fmt"].lower()
    else:
      if "u" in options.keys():
        f_out += ".sam"
      else:
        f_out += ".bam"
    cmd += f" -o {f_out}"

  if mode == "inout" or mode == "in":
    cmd += " " + map_file.get_path()
  else:
    cmd += " -"

  return (cmd, f_out)

def fixmate_sam(map_file, out_dir = None, out_flag = ".fm", mode = "inout", options = dict()):
  if out_dir == None:
    log.warning("No output directory specified.")
    out_dir = "."
  if map_file.format != "sam":
    log.error("Invalid file type detected.")
    raise ValueError
  if mode not in ("pipe", "in", "out", "inout"):
    log.error("Invalid mode specified.")
    raise ValueError
  
  f_out = ""
  cmd = "samtools fixmate"
  for opt in to_optstring(options):
    cmd += " " + opt

  if mode == "inout" or mode == "in":
    cmd += " " + map_file.get_path()
  else:
    cmd += " -"

  if mode == "inout" or mode == "out":
    f_out = op.join(out_dir, map_file.name + out_flag)
    if "O" in options.keys():
      f_out += "." + options["O"].lower()
    elif "output-fmt" in options.keys():
      f_out += "." + options["output-fmt"].lower() 
    else:
      if "u" in options.keys():
        f_out += ".sam"
      else:
        f_out += ".bam"
    cmd += " " + f_out
  else:
    cmd += " -"

  return (cmd, f_out)

def sort_sam(map_file, out_dir = None, out_flag = ".sort", tmp_dir = None, sorting = "", mode = "inout", options = dict()):
  if out_dir == None:
    log.warning("No output directory specified.")
    out_dir = "."
  if tmp_dir == None:
    log.warning("No temp files directory specified.")
    tmp_dir = "."
  if map_file.format != "sam":
    log.error("Invalid file type detected.")
    raise ValueError
  if mode not in ("pipe", "in", "out", "inout"):
    log.error("Invalid mode specified.")
    raise ValueError
  
  f_out = ""
  cmd = f"samtools sort -T {op.join(tmp_dir, map_file.name)}"
  if sorting.lower() == "n" or (sorting.startswith("t ") and len(sorting.strip()) > 2):
    cmd += " -" + sorting
    options.pop("n", None)
    options.pop("N", None)
    options.pop("t", None)

  for opt in to_optstring(options):
    cmd += " " + opt

  if mode == "inout" or mode == "out":
    f_out = op.join(out_dir, map_file.name + out_flag)
    if "O" in options.keys():
      f_out += "." + options["O"].lower()
    elif "output-fmt" in options.keys():
      f_out = "." + options["output-fmt"].lower()
      cmd += " -o " + f_out
    else:
      if "u" in options.keys():
        f_out += ".sam"
      else:
        f_out += ".bam"
    cmd += " -o " + f_out

  if mode == "inout" or mode == "in":
    cmd += " " + map_file.get_path()
  else:
    cmd += " -"

  return (cmd, f_out)

def markdup_sam(map_file, out_dir = None, out_flag = ".dedup", tmp_dir = None, mode = "inout", options = dict()):
  if out_dir == None:
    log.warning("No output directory specified.")
    out_dir = "."
  if tmp_dir == None:
    log.warning("No temp files directory specified.")
    tmp_dir = "."
  if map_file.format != "sam":
    log.error("Invalid file type detected.")
    raise ValueError
  if mode not in ("pipe", "in", "out", "inout"):
    log.error("Invalid mode specified.")
    raise ValueError

  f_out = ""
  cmd = f"samtools markdup -T {op.join(tmp_dir, map_file.name)}"
  for opt in to_optstring(options):
    cmd += " " + opt

  if mode == "inout" or mode == "in":
    cmd += " " + map_file.get_path()
  else:
    cmd += " -"

  if mode == "inout" or mode == "out":
    f_out = op.join(out_dir, map_file.name + out_flag)
    if "O" in options.keys():
      f_out += "." + options["O"].lower()
    elif "output-fmt" in options.keys():
      f_out = "." + options["output-fmt"].lower()
      cmd += " -o " + f_out
    else:
      if "u" in options.keys():
        f_out += ".sam"
      else:
        f_out += ".bam"
    cmd += " -o " + f_out
  else:
    cmd += " -"
    
  return (cmd, f_out)

def index_sam(ref, options=dict()):
  cmd = f"samtools faidx {ref.get_path()}"
  for opt in to_optstring(options):
    cmd += " " + opt

  return cmd