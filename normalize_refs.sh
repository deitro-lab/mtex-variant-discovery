#!/bin/bash
for f in ./refs/*.fa
do
  picard NormalizeFasta \
    LINE_LENGTH=100 \
    I=$f \
    O=./refs/$(basename -s .fa $f).norm.fa 
done
awk '/^>/ {print;next;} {print length($0);}' ./refs/*.fa  | uniq > ref-ln-check.txt
awk '/^>/ {print;next;} {print length($0);}' ./refs/*.norm.fa  | uniq > refnorm-ln-check.txt