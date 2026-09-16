#!/bin/bash
shopt -s extglob
refs=./refs
ext=('fa' 'fasta' 'fas' 'fna')

LC_ALL=C

if [ ! -d ./logs ]; then
  mkdir ./logs
fi
> ./logs/refnorm-ln-check.txt

for ex in ${ext[@]}; do
  for f in $refs/!(*.norm.*); do
    if [ ${f##*.} == $ex ]; then
      bname=$(basename -s .$ex $f)
      norm=$refs/$bname.norm.fa
      if [ ! -f $norm ]; then
        picard NormalizeFasta \
        LINE_LENGTH=100 \
        I=$f \
        O=$norm \
        VERBOSITY=ERROR \
        TMP_DIR=${JOB_TMPDIR:-"./tmp/"} || :
      fi
      echo "$f processing completed"
      awk -b 'BEGIN{print ARGV[1]} /^>/ {print;next;} {print length($0)} END{print "========"}' $f | uniq >> ./logs/refnorm-ln-check.txt
      awk -b 'BEGIN{print ARGV[1]} /^>/ {print;next;} {print length($0)} END{print "========"}' $norm | uniq >> ./logs/refnorm-ln-check.txt
    fi
  done
done