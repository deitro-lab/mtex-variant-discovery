from dataclasses import dataclass
import os

from .utils import log

EXT_FQ = (".fastq", ".fq")
EXT_FA = (".fasta", ".fas", ".fna", ".fa")
EXT_SAM = (".sam", ".bam", ".cram")
EXT_VCF = (".vcf", ".bcf")

@dataclass
class SeqFile:
  name: str
  ext: str
  format: str
  flags: tuple[str] = ()
  is_zip: bool = False

  def __init__(self, fpath):
    ext_map = {
      "fq": EXT_FQ, "fa": EXT_FA,
      "sam": EXT_SAM, "vcf": EXT_VCF
    }

    tokens = fpath.split(".")
    self.name = tokens[0]
    if tokens[-1] == "gz":
      self.ext = "." + tokens[-2] + ".gz"
      self.flags = tokens[1:-2]
      self.is_zip = True
    else:
      self.ext = "." + tokens[-1]
      self.flags = tokens[1:-1]

    for fmt in ext_map.keys():
      if self.is_zip:
        ex = self.ext[:-3]
      else:
        ex = self.ext
      if ex in ext_map[fmt]:
        self.format = fmt
        break
      self.format = "unknown"

  def __repr__(self):
    return self.name + "." + ".".join(self.flags) + self.ext

  def get_name(self):
    return self.name + ".".join(self.flags)

@dataclass
class PairedCollection:
  base: SeqFile
  flags: tuple[str] = ('_1', '_2')

  def __init__(self, seq, flags):
    if len(seq.flags) > 0:
      if ("." + seq.flags[-1]) == flags[0]:
        seq.flags = seq.flags[:-1]

    seq.name = seq.name[:-len(flags[0])]
    self.base = seq
    self.flags = flags

  def __repr__(self):
    r1 = self.base.get_name() + self.flags[0] + self.base.ext
    r2 = self.base.get_name() + self.flags[1] + self.base.ext
    return r1 + " " + r2

  def get_reads(self, idx = 0):
    rname =  self.base.get_name()
    if idx == 0:
      return (
        rname + self.flags[0] + self.base.ext,
        rname + self.flags[1] + self.base.ext
      )
    elif idx == 1:
      return rname + self.flags[0] + self.base.ext
    elif idx == 2:
      return rname + self.flags[1] + self.base.ext
    else:
      return None

def filter_files(dir, ext, check_zip = True):
  if not os.path.exists(dir):
    log.error("Specified directory %s doesn't exist.", dir)
    return None

  files = os.listdir(dir)
  if isinstance(ext, str):
    ext = (ext,)
  if check_zip:
    ext += tuple([e + ".gz" for e in ext])

  filtered = []
  for f in files:
    if os.path.isdir(f):
      continue
    if f.endswith(ext):
      filtered.append(f)

  return filtered

def get_paired_reads(dir, flags):
  if not os.path.exists(dir):
    log.error("Specified directory %s doesn't exist.", dir)
    return None

  query = tuple([flags[0] + ex for ex in EXT_FQ])
  
  base_reads = filter_files(dir, query)

  paired_reads = []
  for r in base_reads:
    read = PairedCollection(SeqFile(r), flags)
    mate = os.path.join(dir, read.get_reads(2))

    if os.path.exists(mate):
      paired_reads.append(read)

  return paired_reads