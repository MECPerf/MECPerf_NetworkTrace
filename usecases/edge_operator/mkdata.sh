#!/bin/bash

mkdir data 2> /dev/null
rm data/migrations.dat data/rtts*.dat data/tmp.* 2> /dev/null

percentiles="0.5 0.75 0.9 0.95 0.98 0.99"
for (( i = 0 ; i <= 80 ; i+=10 )) ; do
  echo "$i $(cat outdir/migrations.percentile=$i.seed=*.dat | scripts/percentile.py --mean)" >> data/migrations.dat

  for p in $percentiles ; do
    for (( s = 0 ; s < 20 ; s++ )) ; do
      echo "$i $(scripts/percentile.py --quantiles $p < outdir/rtts.percentile=$i.seed=$s.dat | cut -f 2 -d ' ')" >> data/tmp.$p.$s
    done
  done
done

for p in $percentiles ; do
  scripts/confidence.py data/tmp.$p.* > data/rtts.$p.dat
done

rm data/tmp.* 2> /dev/null
