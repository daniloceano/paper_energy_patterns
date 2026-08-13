#!/usr/bin/env bash
# Wait for a running step2 download to finish, then re-run the downstream chain
# (steps 3-7) so the tables and figures reflect every MSLP file that landed.
#
# step2 is resumable and can take hours against a saturated CDS queue, so this
# exists to avoid babysitting it: launch under nohup and the results refresh
# themselves once the download process exits. Safe to run even if some
# downloads never succeed — step3 simply processes whatever is present.
#
# Usage:
#   nohup bash scripts/explosive_cyclones_analysis/finalize_after_download.sh <PID> &
#   nohup bash scripts/explosive_cyclones_analysis/finalize_after_download.sh &   # auto-detect
#
# Author: Danilo Couto de Souza
# Date: August 2026

set -u
cd "$(dirname "$0")/../.." || exit 1

WORKERS="${WORKERS:-100}"
PID="${1:-}"

if [[ -z "${PID}" ]]; then
    PID=$(pgrep -f "step2_download_mslp_tracks.py" | head -1)
fi

if [[ -n "${PID}" ]]; then
    echo "[$(date -Is)] waiting for step2 download (PID ${PID}) to finish..."
    while kill -0 "${PID}" 2>/dev/null; do
        sleep 120
    done
    echo "[$(date -Is)] step2 finished."
else
    echo "[$(date -Is)] no step2 download running; going straight to step3."
fi

N_NC=$(ls data/era5_explosive_cyclones/*_mslp.nc 2>/dev/null | wc -l)
echo "[$(date -Is)] MSLP files present: ${N_NC} / 3820"

set -e
python scripts/explosive_cyclones_analysis/step3_assign_central_pressure.py --workers "${WORKERS}"
python scripts/explosive_cyclones_analysis/step4_compute_ndr_classify.py
python scripts/explosive_cyclones_analysis/step5_figures_tables.py
python scripts/explosive_cyclones_analysis/step6_bomb_relative_frequency.py
python scripts/explosive_cyclones_analysis/step6_bomb_relative_frequency.py --scope intensification
python scripts/explosive_cyclones_analysis/step7_bomb_density_maps.py

echo "[$(date -Is)] chain complete on ${N_NC} cyclones."
