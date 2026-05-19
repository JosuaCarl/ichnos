#!/bin/bash

mkdir ts

sudo turbostress/main --load-step 10 | tee ts-1.csv
sudo turbostress/main --load-step 10 | tee ts-2.csv
sudo turbostress/main --load-step 10 | tee ts-3.csv

for source_file in ts-1.csv ts-2.csv ts-3.csv
do
  tail -n 15 ./$source_file >> ./ts/$source_file
done
