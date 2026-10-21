#!/bin/bash
# Waits for the main CV, then runs the summary and the supporting experiments in sequence.
cd "$(dirname "$0")"
while [ ! -f ../cache/cv_main.pkl ]; do sleep 30; done
python3 p05_summarise.py > ../cache/p05.log 2>&1
for e in E1 E2 E3 E4 E6 E7 E9 E5 E8; do
  python3 -u p04_experiments.py $e > ../cache/$e.log 2>&1
done
echo ALLDONE > ../cache/rest.done
