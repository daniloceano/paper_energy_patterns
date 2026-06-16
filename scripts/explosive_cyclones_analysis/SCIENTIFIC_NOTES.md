# Scientific Notes — Explosive Cyclones by Energy Pattern

### 2026-06-16 — Analysis design (validated with PI before implementation)

---

## Research Questions

1. What fraction of the cyclones in each Energy Pattern (EP1, EP2, EP3) undergo
   **explosive cyclogenesis** ("bombs"), and how does this fraction differ across EPs?
2. How do the explosive systems distribute among intensity classes (weak / moderate /
   intense) by EP?
3. Does explosive deepening preferentially occur **during the intensification phase**, and
   does the surface-pressure picture corroborate the energetic-pathway interpretation of the
   EPs (EP1 strong conversions, EP2 moderate, EP3 weak)?

## Physical / Statistical Framework

A cyclone is "explosive" when its central-pressure deepening reaches **at least 1 Bergeron**
(Sanders & Gyakum 1980). The deepening rate is geostrophically normalized with the **sine** of
latitude (the threshold scales with the Coriolis parameter, f ≈ 2Ω sin φ), referenced to 60°:

$$
\mathrm{NDR} = \frac{\Delta p_{24\mathrm{h}}}{24\ \mathrm{hPa}} \cdot
\frac{\sin 60^\circ}{\lvert \sin \varphi \rvert} \quad [\text{Bergeron}],
\qquad \Delta p_{24\mathrm{h}} = p(t) - p(t+24\,\mathrm{h}),
$$

with φ the mean latitude over the 24-h window (Δp > 0 for deepening). NDR ≥ 1 ⇒ bomb. The
local threshold is ≈ 13.9 hPa/24 h at 30° and ≈ 27.7 hPa/24 h at the pole. **Note:** the
adjustment uses **sin φ, not cos φ** — all standard formulations (Sanders & Gyakum; Lim &
Simmonds; Allen et al.; the South Atlantic AABC study) use the sine. The "updates" in the
literature concern the reference latitude (60° vs 45°), the time window, and the combined
criterion of Allen et al. (2010) — not a switch to cosine.

Intensity classes (AABC 2024): weak [1.0, 1.3), moderate [1.3, 1.8], intense (> 1.8).

## Datasets and Variables

- **Cyclone tracks**: *Atlantic Extratropical Cyclone Tracks Database* (Gramcianinov et al.
  2020), TRACK algorithm on 850-hPa relative vorticity ζ₈₅₀; 1979–2020; **1-hourly**.
  Columns used: `date`, `lat vor`, `lon vor`, `period` (CycloPhaser phases), `region`.
  Tracks provide **no central pressure** — hence the MSLP step below.
- **EP membership**: K-Means clustering on phase-mean LEC diagnostics
  (`results/cluster/kmeans_clustered_data.csv`); full populations **EP1 = 444, EP2 = 979,
  EP3 = 2397** (total 3820). This is the authoritative population and is used here in full
  (**not** the reduced composite subset of 332/776/1625, which excludes intensification < 24 h).
- **MSLP**: ERA5 `mean_sea_level_pressure`, 0.25°, hourly, downloaded storm-following over each
  full track (genesis→lysis, padded ±12 h), in a box = track envelope + 6°.

## Methodology

1. **Population (step1).** Map clusters → EPs; extract the full hourly tracks for all 3820
   cyclones.
2. **MSLP download (step2).** Storm-following `msl` over each full track. Light CDS parallelism.
3. **Central-pressure assignment — "A+B" (step3).** At each track timestep, start at the ζ₈₅₀
   centre and **descend the MSLP gradient** to the bottom of the pressure basin the centre
   drains into; accept it only if that bottom is a **local interior minimum** within a search
   radius R0 = 3° ("A"). If none is found within R0, expand once to R1 = 5°. If the descent
   leaves the radius (open wave / displaced surface low / boundary-touching minimum), the
   timestep is **flagged and set to NaN** rather than forced to a boundary value. A
   continuity check flags centres that jump > 4° between consecutive steps. Because descent
   follows the basin topology, a deeper minimum belonging to a neighbouring system (across a
   col) never hijacks the centre. A best-effort `over_land` flag marks continental positions.
4. **NDR and classification (step4).** Reindex central pressure to a regular hourly grid
   (interpolate gaps ≤ 2 h); slide a **centred 24-h window** and take the **maximum NDR** per
   cyclone, reported over the full life cycle **and** restricted to the intensification phase
   (`period` starting with "intensification"). A 6-hourly-subsampled NDR is also reported for
   comparison with synoptic-resolution climatologies. Flag bombs and assign intensity classes;
   aggregate by EP.
5. **Figures (step5).** Results (bomb frequency, NDR distribution, intensity composition by EP)
   plus validation (offset distribution, flag fraction by phase).

## Assumptions

- The 850-hPa vorticity centre and the surface low lie within R0–R1 of each other for closed,
  deepening systems (validated a posteriori via the offset distribution).
- ERA5 0.25° hourly MSLP resolves the central-pressure evolution of these systems adequately.
- φ in the NDR may be taken at the central/vorticity position (the two differ by ≲ a few
  degrees; the sin factor is insensitive to this).
- Short-gap (≤ 2 h) linear interpolation of central pressure does not bias the 24-h deepening.

## Results and Interpretation

*[PRELIMINARY — to be filled after the remote run.]* Expected, given the energetic ordering:
the largest explosive fraction in EP1/EP2 and the smallest in EP3. The offset distribution
(median ~1–2°, short tail) and the concentration of flags in the incipient (open-wave) phase
will be reported as method-validation evidence.

## Caveats and Limitations

- **Vortex tilt / displacement.** A radius too small biases the central pressure high
  (deepening underestimated); R0 = 3° with the A+B interior-minimum rule mitigates this, and
  the offset histogram is the diagnostic.
- **Multiple/secondary centres & merging.** Mitigated by basin-respecting descent and the
  continuity flag, but complex multi-centre systems remain a source of noise.
- **Open waves.** Early life-cycle timesteps often lack a closed low; these are flagged/NaN by
  design and rarely affect the bomb signal (explosive deepening is a closed-low phenomenon).
- **Topography / MSLP reduction.** Many systems have genesis over land (ARG, SE-BR); MSLP
  reduction over high terrain (Andes) is unreliable. The `over_land` flag is best-effort and a
  finer orography mask is a possible refinement.
- **Latitude span.** Subtropical genesis (30° S) implies a low local threshold (≈13.9 hPa/24 h);
  φ is taken as the window-mean latitude for migrating systems.
- **Window length.** Short-lived cyclones may not span 24 h of valid central pressure → no NDR;
  these count as non-explosive (recorded via `n_valid_central` / `n_steps`).

## Next Steps

- Run step2/step3 on the remote server (full 3820 population), sync, and populate Results.
- Inspect the offset distribution and flag fractions; tune R0/R1 if the tail is long.
- Optional: add an ERA5 orography mask for an explicit high-terrain flag; compare hourly vs
  6-hourly NDR; cross-check against the AABC (2024) South Atlantic explosive-cyclone counts.

## References

- Sanders, F., & Gyakum, J. R. (1980). Synoptic-dynamic climatology of the "bomb". *Mon. Wea.
  Rev.*, 108, 1589–1606.
- Lim, E.-P., & Simmonds, I. (2002). Explosive cyclone development in the Southern Hemisphere…
  *Mon. Wea. Rev.*, 130, 2188–2209.
- Allen, J. T., Pezza, A. B., & Black, M. T. (2010). Explosive cyclogenesis: a global
  climatology comparing multiple reanalyses. *J. Climate*, 23, 6468–6484.
- Reale, M., et al. (2019). A global climatology of explosive cyclones using a multi-tracking
  approach. *Tellus A*, 71, 1611340.
- de Jesus, E. M., et al. (2024). Explosive cyclones between 2010 and 2020 in the South Atlantic
  under two detection schemes. *An. Acad. Bras. Ciênc.* (AABC).
- Gramcianinov, C. B., et al. (2020). Atlantic extratropical cyclone tracks database. (Tracks
  used in this study.)
