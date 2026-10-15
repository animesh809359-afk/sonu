#!/bin/bash
cd /home/user/sonu/white_rust_analysis
echo "E7 $(date)"; NJOBS=4 python3 scripts/s11_ofc.py 25 > cache/s11.log 2>&1; echo "E7 exit $?"
echo "E1-E6 $(date)"; NJOBS=4 python3 scripts/s05_experiments.py E1,E2,E3,E4,E5,E6 > cache/s05.log 2>&1; echo "E1-E6 exit $?"
until [ -f scripts/s12_fs_methods.py ]; do sleep 10; done
echo "E8 $(date)"; NJOBS=4 python3 scripts/s12_fs_methods.py 5 > cache/s12.log 2>&1; echo "E8 exit $?"
echo "all done $(date)"
