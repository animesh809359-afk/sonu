#!/usr/bin/env bash
# Runs the full subset pipeline (no feature-selection benchmark, no Part C') for one config.
# usage: ./run_subset.sh configs/subsets/01_Date_11-02-2026.yaml [first_stage]
set -euo pipefail
cfg="$1"; first="${2:-data}"
name="$(basename "$cfg" .yaml)"
export SP_CONFIG="$cfg"
export SP_WORK="$(pwd)/work_subsets/$name"
mkdir -p "$SP_WORK"
cd analysis
stages=(data A K K3b_joinfree C compare figures conclusions excel recalc)
go=0
for s in "${stages[@]}"; do
  [[ "$s" == "$first" ]] && go=1
  [[ $go == 1 ]] || continue
  echo "[$(date +%T)] $name: $s"
  case "$s" in
    figures) python make_figures.py > "$SP_WORK/figures.log" 2>&1 ;;
    conclusions) python auto_conclusions.py > "$SP_WORK/conclusions.log" 2>&1 ;;
    excel) python build_excel.py > "$SP_WORK/excel.log" 2>&1 ;;
    recalc) python /mnt/skills/public/xlsx/scripts/recalc.py "$(python -c 'from common import cfg; c=cfg(); print(c["output"]["dir"] + "/" + c["output"]["stem"] + "_FourTier_CART_RF_K_Combined.xlsx")')" 300 > "$SP_WORK/recalc.log" 2>&1 ;;
    *) python "stage_$s.py" > "$SP_WORK/stage_$s.log" 2>&1 ;;
  esac
done
echo "[$(date +%T)] $name: finished"
