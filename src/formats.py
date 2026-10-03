from dataclasses import dataclass

EXT_FQ = (".fastq", ".fq")
EXT_FA = (".fasta", ".fas", ".fna", ".fa")
EXT_SAM = (".sam", ".bam", ".cram")
EXT_VCF = (".vcf", ".bcf")

@dataclass
class SeqFile:
  name: str
  ext: str
  flags: tuple[str]
  format: str
  is_zip: bool = False

  def __init__(self, fpath):
    ext_map = {
      "fq": EXT_FQ, "fa": EXT_FA,
      "sam": EXT_SAM, "vcf": EXT_VCF
    }

    tokens = fpath.split(".")
    self.name = tokens[0]
    if tokens[-1] == "gz":
      self.ext = "." + tokens[-2]
      self.flags = tokens[1:-2]
      self.is_zip = True
    else:
      self.ext = "." + tokens[-1]
      self.flags = tokens[1:-1]

    for fmt in ext_map.keys():
      if self.ext in ext_map[fmt]:
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
    if ("." + seq.flags[-1]) == flags[0]:
      seq.flags = seq.flags[:-1]

    self.base = seq
    self.flags = flags

  def get_reads(self, idx = 0):
    rname =  self.base.getname()
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