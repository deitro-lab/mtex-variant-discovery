#!/bin/bash
shopt -s extglob
refs=./refs
ext=('fa' 'fasta' 'fas' 'fna')

if [ ! -d ./logs ]; then
  mkdir ./logs
fi
> ./logs/refnorm-ln-check.txt

for ex in ${ext[@]}; do
  echo "======="
  for f in $refs/!(*.norm.*); do
    if [ ${f##*.} == $ex ]; then
      bname=$(basename -s .$ex $f)
      if [ ! -f $refs/$bname.norm.fa ]; then
        echo ">"
        picard NormalizeFasta \
        LINE_LENGTH=100 \
        I=$f \
        O=$refs/$bname.norm.fa \
        VERBOSITY=ERROR \
        TMP_DIR=${JOB_TMPDIR:-"./tmp/"}
      fi
      awk 'BEGIN{print ARGV[1]} /^>/ {print;next;} {print length($0)} END{print "========"}' $f | uniq >> ./logs/refnorm-ln-check.txt
    fi
  done
done