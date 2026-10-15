#!/bin/bash
set -e
cd /home/user/sonu/white_rust_analysis
until [ -f cache/cv_main.pkl ]; do sleep 20; done
sleep 5
echo "summarise $(date)"; python3 scripts/s06_summarise.py > cache/s06.log 2>&1
echo "E7 $(date)"; NJOBS=4 python3 scripts/s11_ofc.py 25 > cache/s11.log 2>&1
echo "E1-E6 $(date)"; NJOBS=4 python3 scripts/s05_experiments.py E1,E2,E3,E4,E5,E6 > cache/s05.log 2>&1
echo "all done $(date)"
