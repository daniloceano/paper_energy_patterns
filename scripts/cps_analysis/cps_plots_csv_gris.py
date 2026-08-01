"""
Cyclone Phase Space (CPS) Diagrams - Furacão Akara (ERA5 2024)
Gera dois gráficos: VTL vs B e VTU vs B em uma única figura.
Versão SEM presión/intensidade: os marcadores e linhas usam cor cinza fixa.

Uso:
    python3 cps_plots_gris.py --csv CPS_output.csv --output CPS_diagrams.png

Argumentos:
    --csv      Archivo CSV de entrada con los datos CPS (columnas: time,B_left,B_right,dir,SIZE,VTL,VTU)
    --output   Archivo PNG de salida para los gráficos

Ejemplo de generación de datos CPS:
    python cps_calculator_a.py --nc akara_new.nc --track trackfilen --dt 3

"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import argparse

# ── 1. CARREGAR DADOS ──────────────────────────────────────────────────────────
# Configurar argumentos de línea de comandos
parser = argparse.ArgumentParser(description='Genera gráficos CPS (Cyclone Phase Space)')
parser.add_argument('--csv', required=True, help='Archivo CSV de entrada (ej: CPS_ERA5_BIGUA.csv)')
parser.add_argument('--output', required=True, help='Archivo PNG de salida (ej: CPS_diagrams_ibax.png)')
args = parser.parse_args()

INPUT  = args.csv
OUTPUT = args.output

df = pd.read_csv(INPUT)
#df.replace(-9e8, np.nan, inplace=True)
# 1. Seleccionamos solo los nombres de las columnas numéricas
cols_numericas = df.select_dtypes(include=[np.number]).columns

# 2. Aplicamos el cambio solo en esas columnas
df[cols_numericas] = df[cols_numericas].mask(df[cols_numericas] < -999, np.nan)

# Variáveis derivadas (consistente com scripts GrADS)
df['B']   = (df['B_left'] - df['B_right']) / 1.0
df['VTL'] = df['VTL'] / 1.0
df['VTU'] = df['VTU'] / 1.0
df['hour'] = df['time'].astype(str).str[:2].astype(int)
df['day']  = df['time'].astype(str).str[3:5].astype(int)

# Suavização temporal ±2 passos (smooth=2 → janela=5, como no GrADS)
def smooth(arr, w=5):
    return pd.Series(arr).rolling(w, center=True, min_periods=1).mean().values

df['B_sm']    = smooth(df['B'].values)
df['VTL_sm']  = smooth(df['VTL'].values)
df['VTU_sm']  = smooth(df['VTU'].values)
df['SIZE_sm'] = smooth(df['SIZE'].values)

# ── 2. COR FIXA (SEM DADOS DE PRESSÃO/INTENSIDADE) ───────────────────────────
MARKER_COLOR = '#808080'  # cinza para bolas e linhas
MARKER_SIZE  = 40         # tamanho fixo do marcador (não depende de SIZE)

def get_color(idx):
    """Cor fixa cinza (não há dado de intensidade/presión disponible)."""
    return MARKER_COLOR

def marker_size(size_km):
    """Tamanho fixo do marcador (independente do raio de ventos de gale)."""
    return MARKER_SIZE

# ── 3. FIGURA ─────────────────────────────────────────────────────────────────
GREY = '#d3d3d3'

# Crear figura con GridSpec para dimensiones específicas por subplot
# Ambos subplots con las mismas dimensiones (20,7 cada uno)
fig = plt.figure(figsize=(20, 7), facecolor='white')
gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1], figure=fig)
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])
# Ajustar márgenes: gráficos a la izquierda, menos espacio entre ellos, espacio a la derecha para leyenda
fig.subplots_adjust(left=0.05, right=0.97, bottom=0.10, top=0.93, wspace=0.15)

# Configuración de fondo para Gráfico 1: VTL vs B
ax1.set_facecolor('white')
ax1.axhspan(9, 11, color=GREY, alpha=0.9, zorder=0)  # B (eje Y): -10 a 10
ax1.axvspan(-5, 5, color=GREY, alpha=0.9, zorder=0)    # VTL (eje X): -2 a 2
#ax1.axhline(0, color='k', lw=0.6, zorder=1)
#ax1.axvline(0, color='k', lw=0.6, zorder=1)

# Configuración de fondo para Gráfico 2: VTL vs VTU
ax2.set_facecolor('white')
ax2.axhspan(-5, 5, color=GREY, alpha=0.9, zorder=0)    # VTU (eje Y): -2 a 2
ax2.axvspan(-5, 5, color=GREY, alpha=0.9, zorder=0)    # VTL (eje X): -2 a 2
#ax2.axhline(0, color='k', lw=0.7, zorder=1)
#ax2.axvline(0, color='k', lw=0.7, zorder=1)

# ── GRÁFICO 1: VTL (eje X) vs B (eje Y) ───────────────────────────────────────
mask1 = df['VTL_sm'].notna() & df['B_sm'].notna()
sub1  = df[mask1].copy().reset_index(drop=False)
x1, y1, oi1 = sub1['VTL_sm'].values, sub1['B_sm'].values, sub1['index'].values

# Dibujar líneas primero con clip_on para evitar que se dibujen fuera del área
for i in range(len(sub1) - 1):
    ax1.plot([x1[i], x1[i+1]], [y1[i], y1[i+1]], color=get_color(oi1[i]),
             lw=1.2, zorder=2, clip_on=True)

# Dibujar scatter points ENCIMA de las líneas
for i in range(len(sub1)):
    ax1.scatter(x1[i], y1[i],
                c=[get_color(oi1[i])], s=marker_size(sub1['SIZE_sm'].iloc[i]),
                edgecolors='none', zorder=3)

# Etiquetas de días
for i in range(len(sub1)):
    if sub1['hour'].iloc[i] == 0:
        ax1.text(x1[i], y1[i] + 0.8, str(sub1['day'].iloc[i]),
                 ha='center', va='bottom', fontsize=7.5, fontweight='bold', zorder=5)

# Etiqueta 'A' sobre el primer punto (sin marco ni fondo)
ax1.text(x1[0], y1[0] + 0.8, 'A', fontsize=12, fontweight='bold',
         ha='center', va='bottom', zorder=6, color='black')

# Etiqueta 'Z' sobre el último punto (sin marco ni fondo)
ax1.text(x1[-1], y1[-1] + 0.8, 'Z', fontsize=12, fontweight='bold',
         ha='center', va='bottom', zorder=6, color='black')

# Calcular dinámicamente los límites basados en los datos
# Se incluye siempre el rango de la franja gris (VTL -5..5, B 9..11) para que
# el umbral quede visible en el gráfico aunque los datos no lo alcancen.
x1_min, x1_max = np.nanmin(x1), np.nanmax(x1)
y1_min, y1_max = np.nanmin(y1), np.nanmax(y1)
x1_min, x1_max = min(x1_min, -5), max(x1_max, 5)
y1_min, y1_max = min(y1_min, 9), max(y1_max, 11)
ax1.set_xlim(x1_min - 20, x1_max + 20)
ax1.set_ylim(y1_min - 20, y1_max + 20)
ax1.set_xticks(np.arange(x1_min - 20, x1_max + 20, 25))
ax1.set_yticks(np.arange(y1_min - 20, y1_max + 20, 10))
ax1.tick_params(labelsize=12)
# Este bucle recorre todas las etiquetas y las pone en negrita
for label in (ax1.get_xticklabels() + ax1.get_yticklabels()):
    label.set_fontweight('bold')
ax1.set_xlabel(r'VTL [900-600hPa Thermal Wind]', fontsize=13, color='blue', fontweight='bold')
ax1.set_ylabel(r'B [900-600hPa Storm-Relative Thickness Symmetry]', fontsize=13, color='blue', fontweight='bold')
#ax1.set_title('VTL vs B - ERA5(2024)', fontsize=14, color='green', pad=6, fontweight='bold')

# Posicionar textos dinámicamente basados en los límites calculados
# Asymmetric: parte superior (B > 10)
if y1_max + 20 > 10:
    ax1.text(x1_min - 18, y1_max + 14, 'Asymmetric', fontsize=12, color='purple', fontstyle='italic', fontweight='bold', va='top')
# Symmetric: parte inferior (B < 10)
if y1_min - 20 < 10:
    ax1.text(x1_min - 18, y1_min - 14, 'Symmetric', fontsize=12, color='purple', fontstyle='italic', fontweight='bold', va='bottom')
# Cold Core: parte izquierda (VTL < 0)
if x1_min - 20 < 0:
    ax1.text(x1_min - 18, min(10, y1_max + 10), 'Cold Core', fontsize=12, color='red', fontstyle='italic', fontweight='bold')
# Warm Core: parte derecha (VTL > 0)
if x1_max + 20 > 0:
    ax1.text(x1_max + 5, min(10, y1_max + 10), 'Warm Core', fontsize=12, color='green', fontstyle='italic', fontweight='bold')

# ── GRÁFICO 2: VTL (eje X) vs VTU (eje Y) ─────────────────────────────────────
mask2 = df['VTL_sm'].notna() & df['VTU_sm'].notna()
sub2  = df[mask2].copy().reset_index(drop=False)
x2, y2, oi2 = sub2['VTL_sm'].values, sub2['VTU_sm'].values, sub2['index'].values

# Dibujar líneas primero con clip_on para evitar que se dibujen fuera del área
for i in range(len(sub2) - 1):
    ax2.plot([x2[i], x2[i+1]], [y2[i], y2[i+1]], color=get_color(oi2[i]),
             lw=1.2, zorder=2, clip_on=True)

# Dibujar scatter points ENCIMA de las líneas
for i in range(len(sub2)):
    ax2.scatter(x2[i], y2[i],
                c=[get_color(oi2[i])], s=marker_size(sub2['SIZE_sm'].iloc[i]),
                edgecolors='none', zorder=3)

# Etiquetas de días
for i in range(len(sub2)):
    if sub2['hour'].iloc[i] == 0:
        ax2.text(x2[i], y2[i] + 3.5, str(sub2['day'].iloc[i]),
                 ha='center', va='bottom', fontsize=7.5, fontweight='bold', zorder=5)

# Etiqueta 'A' sobre el primer punto (sin marco ni fondo)
ax2.text(x2[0], y2[0] + 3.5, 'A', fontsize=12, fontweight='bold',
         ha='center', va='bottom', zorder=6, color='black')

# Etiqueta 'Z' sobre el último punto (sin marco ni fondo)
ax2.text(x2[-1], y2[-1] + 3.5, 'Z', fontsize=12, fontweight='bold',
         ha='center', va='bottom', zorder=6, color='black')

# Calcular dinámicamente los límites basados en los datos
# Se incluye siempre el rango de la franja gris (VTL y VTU -5..5) para que
# el umbral quede visible en el gráfico aunque los datos no lo alcancen.
x2_min, x2_max = np.nanmin(x2), np.nanmax(x2)
y2_min, y2_max = np.nanmin(y2), np.nanmax(y2)
x2_min, x2_max = min(x2_min, -5), max(x2_max, 5)
y2_min, y2_max = min(y2_min, -5), max(y2_max, 5)
ax2.set_xlim(x2_min - 40, x2_max + 40)
ax2.set_ylim(y2_min - 40, y2_max + 40)
ax2.set_xticks(np.arange(x2_min - 40, x2_max + 40, 25))
ax2.set_yticks(np.arange(y2_min - 40, y2_max + 40, 25))
ax2.tick_params(labelsize=12)
# Este bucle recorre todas las etiquetas y las pone en negrita
for label in (ax2.get_xticklabels() + ax2.get_yticklabels()):
    label.set_fontweight('bold')
ax2.set_xlabel(r'VTL [900hPa-600hPa Thermal Wind]', fontsize=13, color='blue', fontweight='bold')
ax2.set_ylabel(r'VTU [600hPa-300hPa Thermal Wind]', fontsize=13, color='blue', fontweight='bold')
#ax2.set_title('VTL vs VTU - ERA5(2024)', fontsize=14, color='green', pad=6, fontweight='bold')
#ax2.text( 50,  45,  'DEEP WARM CORE',      fontsize=12, color='navy', style='italic', fontweight='bold')
#ax2.text( 50,   5,  'MODERATE', fontsize=12, color='navy', style='italic', fontweight='bold')
#ax2.text(-48, -95,  'DEEP COLD CORE',      fontsize=12, color='navy', style='italic', fontweight='bold')
#ax2.text( 50, -60,  'SHALLOW',  fontsize=12, color='navy', style='italic', fontweight='bold')

# Posicionar textos dinámicamente basados en los límites calculados
# Cold Core (VTL < 0): parte izquierda
if x2_min - 20 < 0:
    ax2.text(x2_min - 18, -10, 'Cold Core', fontsize=12, color='red', style='italic', fontweight='bold', va='center')
# Warm Core (VTL > 0): parte derecha
if x2_max + 20 > 0:
    ax2.text(x2_max + 5, -10, 'Warm Core', fontsize=12, color='green', style='italic', fontweight='bold', va='center')
# Cold Core (VTU < 0): parte inferior
if y2_min - 20 < 0:
    ax2.text(2, y2_min - 15, 'Cold Core', fontsize=12, color='red', style='italic', rotation=90, fontweight='bold', ha='center', va='bottom')
# Warm Core (VTU > 0): parte superior
if y2_max + 20 > 0:
    ax2.text(2, y2_max + 5, 'Warm Core', fontsize=12, color='green', style='italic', rotation=90, fontweight='bold', ha='center', va='bottom')

# ── 4. LEGENDA ────────────────────────────────────────────────────────────────
# (Sin leyenda de intensidad/presión: no se dispone de esa variable en esta versión)

# # Raio de ventos de gale
# fig.text(0.845, 0.48, 'Mean radius of\n925hPa gale\nforce wind (km):',
#          fontsize=7.5, fontweight='bold', va='top')
# ax_leg = fig.add_axes([0.840, 0.10, 0.15, 0.35])
# ax_leg.set_axis_off()
# ax_leg.set_xlim(0, 1); ax_leg.set_ylim(0, 1)
# rrs    = [100, 200, 300, 500, 750]
# labels = ['<100', '200', '300', '500', '750']
# for i, (rr, lbl) in enumerate(zip(rrs, labels)):
#     y = 0.88 - i * 0.20
#     ax_leg.scatter([0.15], [y], s=marker_size(rr), c=['k'], zorder=5, clip_on=False)
#     ax_leg.text(0.38, y, lbl, fontsize=7.5, va='center')

# ── 5. SALVAR ─────────────────────────────────────────────────────────────────
fig.savefig(OUTPUT, dpi=300, facecolor='white')
print(f'Figura salva em: {OUTPUT}')
