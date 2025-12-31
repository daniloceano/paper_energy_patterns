import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SRC_DIR = os.path.join(BASE_DIR, 'figures', 'exploratory', 'density_ge', 'by_phase')
OUT_DIR = os.path.join(BASE_DIR, 'figures', 'main')
os.makedirs(OUT_DIR, exist_ok=True)

FILES = [
    'inc.png',
    'int.png',
    'mat.png',
    'dec.png',
]

OUT_PATH = os.path.join(OUT_DIR, 'phase_density_2x2.png')


def make_2x2():
    paths = [os.path.join(SRC_DIR, f) for f in FILES]
    imgs = [mpimg.imread(p) for p in paths]

    h, w = imgs[0].shape[0], imgs[0].shape[1]
    # set figure size so final image has good resolution at 300 dpi
    # scale: use approx 100 px per inch baseline and double it for readability
    figsize = (w * 2 / 100, h * 2 / 100)

    fig, axes = plt.subplots(2, 2, figsize=figsize, dpi=300)
    axes = axes.flatten()

    panel_labels = ['(a)', '(b)', '(c)', '(d)']

    for ax, img, lab in zip(axes, imgs, panel_labels):
        ax.imshow(img)
        ax.axis('off')
        ax.text(0.02, 0.96, lab, transform=ax.transAxes,
                fontsize=12, fontweight='bold', va='top')

    plt.subplots_adjust(wspace=0.02, hspace=0.02)
    fig.savefig(OUT_PATH, dpi=300, bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)


if __name__ == '__main__':
    make_2x2()
    print('Saved 2x2 phase density figure to:', OUT_PATH)
