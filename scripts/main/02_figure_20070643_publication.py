#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create publication-ready figure for cyclone 20070643 by combining
its LPS conversion, LPS imports, and track images into a single figure.

This script assumes the individual images have already been created by
scripts/exploratory/figure_three_intense_cyclones_individual.py. It reads
those images, arranges them in a 2x1 layout (two images on top, one on bottom),
adds panel labels, and saves the final figure.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

BASE_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = BASE_DIR / 'figures' / 'exploratory' / 'three_most_intense_cyclones_zoom'
OUT_DIR = BASE_DIR / 'figures' / 'main'
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRACK_ID = '20070643'
FILES = {
    'conv': SRC_DIR / f'{TRACK_ID}_lps_conversion_zoom.png',
    'imp': SRC_DIR / f'{TRACK_ID}_lps_imports_zoom.png',
    'track': SRC_DIR / f'{TRACK_ID}_track.png',
}

# Verify source files
missing = [p for p in FILES.values() if not p.exists()]
if missing:
    print('Missing source images:')
    for p in missing:
        print(' -', p)
    raise SystemExit('Run scripts/exploratory/figure_three_intense_cyclones_individual.py first')

# Read images
img_conv = mpimg.imread(FILES['conv'])
img_imp = mpimg.imread(FILES['imp'])
img_track = mpimg.imread(FILES['track'])

# Create figure with manual GridSpec layout to control spacing
fig = plt.figure(figsize=(10, 9))
import matplotlib.gridspec as gridspec
# Use tight spacing and manual margins to avoid white space
gs = gridspec.GridSpec(2, 2, figure=fig, height_ratios=[1, 0.3],
                       top=0.98, bottom=0.02, left=0.02, right=0.98,
                       hspace=-0.35, wspace=-0.171)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, :])

# Display images
ax1.imshow(img_conv)
ax1.axis('off')
ax1.text(0.14, 0.995, '(a)', transform=ax1.transAxes,
         fontsize=10, fontweight='bold', va='top', ha='left')

ax2.imshow(img_imp)
ax2.axis('off')
ax2.text(0.17, 0.995, '(b)', transform=ax2.transAxes,
         fontsize=10, fontweight='bold', va='top', ha='left')

ax3.imshow(img_track)
ax3.axis('off')
ax3.text(0.33, 0.99, '(c)', transform=ax3.transAxes,
         fontsize=10, fontweight='bold', va='top', ha='left')


# Save
out_file = OUT_DIR / f'2_{TRACK_ID}_lps_track_publication.png'
plt.savefig(out_file, dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f'✓ Saved: {out_file}')
