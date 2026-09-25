#!/bin/bash
shopt -s extglob
refs=refs
ext=('fa' 'fasta' 'fas' 'fna')

LC_ALL=C

if [[ ! -d ./logs ]]; then
  mkdir ./logs
fi
> ./logs/refnorm-ln-check.txt

echo "==========================================="
echo "Normalize line lengths for FASTA files"
echo "==========================================="
# Normalize line lengths
for ex in ${ext[@]}; do
  for f in $refs/!(*.norm.*); do
    if [ ${f##*.} == $ex ]; then
      bname=$(basename -s .$ex $f)
      norm=$refs/norm/$bname.norm.fa
      if [ ! -f $norm ]; then
        picard NormalizeFasta \
        LINE_LENGTH=100 \
        I=$f \
        O=$norm \
        VERBOSITY=ERROR \
        TMP_DIR=${JOB_TMPDIR:-"./tmp/"} || :
      fi
      echo "$f processing completed"
      awk -b 'BEGIN{print ARGV[1]} /^>/ {print;next;} {print length($0)} END{print "========"}' $f | uniq >> logs/refnorm-ln-check.txt
      awk -b 'BEGIN{print ARGV[1]} /^>/ {print;next;} {print length($0)} END{print "========"}' $norm | uniq >> logs/refnorm-ln-check.txt
    fi
  done
done

echo "==========================================="
echo "Minimize headers for LTR analysis"
echo "==========================================="
nd=$refs
for fn in $nd/*.norm.fa; do
  bname=$(basename $fn .norm.fa)

  # Extract original headers
  echo "Extracting original headers from $fn..."
  echo "primary" > $nd/$bname.primary.head
  awk '/^>/ { print }' $fn >> $nd/$bname.primary.head

  # Normalize headers
  echo "Normalizing headers for $fn..."
  awk 'BEGIN { c = 0 } { if ($0 ~ /^>/) { printf "%.4s%0.6i\n", $1, c; c += 1 } else { print } }' $fn > $fn

  # Extract normalized headers
  echo "Extracting normalized headers from $fn..."
  echo "norm" > $nd/$bname.norm.head
  awk '/^>/ { print }' $fn >> $nd/$bname.norm.head

  # Generate header index and perform cleanup
  echo "Generating header index for $fn..."
  paste $nd/$bname.norm.head $nd/$bname.primary.head > $nd/$bname.head.tsv
  rm $nd/$bname.norm.head $nd/$bname.primary.head
done