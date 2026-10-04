"""
Generate commands for bcftools
"""

import os.path as op

from .utils import log, to_optstring

def bcft_mpileup(map_file, ref, out_dir = None, options = dict()):
  """
  Format input as bcftools mpileup cmd
  """
  vcext = {"b": ".bcf", "u": ".bcf", "z": ".vcf", "v": ".vcf"}

  if out_dir == None:
    log.warning("No output directory specified.")
    out_dir = "."
  if not op.isdir(out_dir):
    log.error("Specified output directory not found.")
    raise ValueError
  if map_file.format != "sam" or ref.format != "fa":
    log.error("Invalid file type(s) detected.")
    raise ValueError

  if "O" not in options.keys() and "output-type" not in options.keys():
    options.update({"O": "b8"})

  cmd = f"bcftools mpileup"
  for opt in to_optstring(options):
    cmd += " " + opt

  out_vcf = op.join(out_dir, map_file.name)
  if "O" in options.keys():
    out_vcf += vcext[options["O"][0]]
  elif "output-type" in options.keys():
    out_vcf += vcext[options["output-type"][0]]
  else:
    out_vcf += ".vcf"
  cmd += f" --fasta-ref {ref.get_path()} --output {out_vcf} {map_file.get_path()}"

  return cmd