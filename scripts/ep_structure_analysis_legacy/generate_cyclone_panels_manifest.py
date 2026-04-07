"""
Generate manifest of cyclone explorer panels for web consumption.
Outputs a CSV and JSON in results/ep_structure.
"""
from pathlib import Path
import json
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIG_DIR = PROJECT_ROOT / 'figures' / 'cyclone_explorer'
OUT_DIR = PROJECT_ROOT / 'results' / 'ep_structure'
OUT_DIR.mkdir(parents=True, exist_ok=True)

manifest = { 'metadata': {'panel_size_deg': 30, 'inner_box_deg': 15}, 'cyclones': {} }
rows = []
for ep_label in ['ep1','ep2']:
    ep_dir = FIG_DIR / ep_label
    if not ep_dir.exists():
        continue
    for track_dir in sorted(ep_dir.iterdir()):
        if not track_dir.is_dir():
            continue
        panels = sorted([p.name for p in track_dir.glob('panel_t*.png')])
        track_id = track_dir.name
        manifest['cyclones'][track_id] = {
            'track_id': track_id,
            'ep_label': ep_label.upper(),
            'n_panels': len(panels),
            'panels': [str(p) for p in sorted(track_dir.glob('panel_t*.png'))]
        }
        rows.append([track_id, ep_label.upper(), len(panels), ';'.join([str(p) for p in sorted(track_dir.glob('panel_t*.png'))])])

# write JSON
with open(OUT_DIR / 'cyclone_panels_manifest.json','w') as fh:
    json.dump(manifest, fh, indent=2)

# write CSV
with open(OUT_DIR / 'cyclone_panels_manifest.csv','w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['track_id','ep_label','n_panels','panel_paths_semicolon'])
    w.writerows(rows)

print('Manifest written:', OUT_DIR / 'cyclone_panels_manifest.json')
print('CSV written:', OUT_DIR / 'cyclone_panels_manifest.csv')