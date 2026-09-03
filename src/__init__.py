"""This is designed as a streamlined program for parallel handling of
short read NGS data within a variant discovery workflow.

Modules:

  - utilities.py        Provides general-use helper functions
  - preprocessing.py    Handles QC, trimming, and filtering via fastp
  - mapping.py          Generate reference index and align reads to ref
"""

__version__ = '0.1'