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

    fig, axes = plt.subplots(2, 2, figsize=(16, 8), dpi=300)
    axes = axes.flatten()

    panel_labels1 = ['(a)', '(c)', '(e)', '(g)']
    panel_labels2 = ['(b)', '(d)', '(f)', '(h)']

    for ax, img, lab1, lab2 in zip(axes, imgs, panel_labels1, panel_labels2):
        ax.imshow(img)
        ax.axis('off')
        y = 0.99
        ax.text(0.05, y, lab1, transform=ax.transAxes,
                fontsize=10, fontweight='bold', va='top')
        ax.text(0.92, y, lab2, transform=ax.transAxes,
                fontsize=10, fontweight='bold', va='top')
    plt.subplots_adjust(wspace=0.02, hspace=0.00)
    fig.savefig(OUT_PATH, dpi=300, bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)


if __name__ == '__main__':
    make_2x2()
    print('Saved 2x2 phase density figure to:', OUT_PATH)
