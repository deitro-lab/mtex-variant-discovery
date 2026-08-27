#!/usr/bin/env python

from genericpath import isdir
import os

def index_ref(*refs):
  faext = ('.fasta', '.fa', '.fna', '.fas')
  commands = []

  processed = set() 

  for ref in refs:
    if os.path.isdir(ref):
      files = os.listdir(ref)
      for f in files:
        path = os.path.join(ref, f)
        if os.path.isdir(path):
          continue

        if not f.endswith(faext):
          continue

        processed.add(path)
        commands.append(f'bwa-mem2 index {path}')
        
    elif os.path.exists(ref):
      if not ref.endswith(faext):
        continue

      processed.add(ref)
      commands.append(f'bwa-mem2 index {ref}')

  return commands
  
