"""
Cyclone Phase Space classification criteria — single source of truth.

Every threshold set below is transcribed from a peer-reviewed source. No
threshold in this module is invented, tuned, or fitted to our data. Where a
threshold is quoted through a secondary source (a review or a table in a later
paper), both the originating and the transcribing reference are recorded.

Sign convention (Hart 2003, Eqs. 2, 5, 6)
----------------------------------------
    B      = h[ (Z600 - Z900)_R - (Z600 - Z900)_L ]   over 500-km semicircles,
             h = +1 (Northern Hemisphere), h = -1 (Southern Hemisphere)
    -V_T^L = d(dZ)/d ln p  over 900 -> 600 hPa
    -V_T^U = d(dZ)/d ln p  over 600 -> 300 hPa,   dZ = (Zmax - Zmin) within 500 km

    B > 0      -> thermally asymmetric (frontal)
    -V_T  > 0  -> warm core in the layer;  -V_T < 0 -> cold core in the layer

In this module (and everywhere in `cps_analysis`) the columns `VTL` and `VTU`
hold Hart's -V_T^L and -V_T^U, i.e. the SIGNED slope, NOT its negative. This is
the convention plotted by every CPS diagram in the cited literature.

References
----------
Hart, R. E. (2003). A cyclone phase space derived from thermal wind and thermal
    asymmetry. Mon. Wea. Rev., 131(4), 585-616.
    doi:10.1175/1520-0493(2003)131<0585:ACPSDF>2.0.CO;2

Evans, J. L., & Guishard, M. P. (2009). Atlantic subtropical storms. Part I:
    Diagnostic criteria and composite analysis. Mon. Wea. Rev., 137(7),
    2065-2080. doi:10.1175/2009MWR2468.1

Gozzo, L. F., da Rocha, R. P., Reboita, M. S., & Sugahara, S. (2014).
    Subtropical cyclones over the southwestern South Atlantic: Climatological
    aspects and case study. J. Climate, 27(22), 8543-8562.
    doi:10.1175/JCLI-D-14-00149.1

Cavicchia, L., Pepler, A., Dowdy, A., & Walsh, K. (2019). A physically based
    climatology of the occurrence and intensification of Australian east coast
    lows. J. Climate, 32(10), 2823-2841. doi:10.1175/JCLI-D-18-0549.1

Marrafon, V. H., Reboita, M. S., da Rocha, R. P., & de Jesus, E. M. (2022).
    Classificacao dos tipos de ciclones sobre o Oceano Atlantico Sul em
    projecoes com o RegCM4 e MCGs. Rev. Bras. Climatol., 30, 1-25.
    doi:10.55761/abclima.v30i18.14603

Conrado, E. T. de C., da Rocha, R. P., Reboita, M. S., & Cardoso, A. A. (2024).
    Cyclone classification over the South Atlantic Ocean in centenary
    reanalysis. Atmosphere, 15(12), 1533. doi:10.3390/atmos15121533

Reboita, M. S., Nogueira, N. C. de O., Gomes, I. B. dos S., Palma, L. L. da C.,
    & da Rocha, R. P. (2024). Assessment of a tropical transition over the
    southwestern South Atlantic Ocean: The case of cyclone Akara.
    J. Mar. Sci. Eng., 12(11), 1934. doi:10.3390/jmse12111934

Reboita, M. S., Crespo, N. M., Dutra, L. M. M., Silva, B. A., Capucin, B. C., &
    da Rocha, R. P. (2021). Iba: The first pure tropical cyclogenesis over the
    western South Atlantic Ocean. J. Geophys. Res. Atmos., 126(1),
    e2020JD033431. doi:10.1029/2020JD033431

Author: Danilo Couto de Souza
Date: August 2026
"""

from typing import Dict, List, Optional, Tuple

# =============================================================================
# THRESHOLD SETS
# =============================================================================
# Each class is an open interval per parameter: (low, high), None = unbounded.
# A timestep belongs to the class when   low < value < high   for all three
# parameters. Bounds are treated as strict, matching the way the sources are
# written ("B < 10", "-VTL > 0", ...).

Interval = Tuple[Optional[float], Optional[float]]
ClassSpec = Dict[str, Interval]

CRITERIA: Dict[str, Dict[str, ClassSpec]] = {
    # -------------------------------------------------------------------------
    # C01 - "classical" CPS partition.
    # Originating source: Cavicchia et al. (2019), Australian east coast lows.
    # Transcribed from Conrado et al. (2024), their Fig. 2a, column C01, which
    # applies it to the South Atlantic. Equivalent to the textbook description
    # in Hart (2003) and repeated by Reboita et al. (2024) for Akara:
    # "A cyclone is classified as extratropical when B >> 10 m, -|VTL| < 0 and
    #  -|VTU| < 0, and as tropical when B < 10 m, -|VTL| > 0 and -|VTU| > 0".
    # -------------------------------------------------------------------------
    "C01": {
        "tropical":      {"B": (None, 10.0), "VTL": (0.0, None), "VTU": (0.0, None)},
        "subtropical":   {"B": (None, 10.0), "VTL": (0.0, None), "VTU": (None, 0.0)},
        "extratropical": {"B": (10.0, None), "VTL": (None, 0.0), "VTU": (None, 0.0)},
    },

    # -------------------------------------------------------------------------
    # GOZZO14 - South-Atlantic-specific subtropical definition.
    # Gozzo et al. (2014), section 2c, verbatim: the system "presents horizontal
    # thermal symmetry and hybrid structure for more than 36 consecutive hours.
    # Both conditions are diagnosed by using the CPS parameters, with B < 25 m,
    # -VT^U < -10 and -VT^L > -50."
    # The -VT^L bound is deliberately relaxed from the North Atlantic value of
    # -10 (Evans and Guishard 2009) to -50, because "the CPS can sometimes give
    # a very low or negative value of this parameter even for pure tropical
    # cyclones (Braun 2009)".
    # The same set is quoted for the South Atlantic by Reboita et al. (2024):
    # "For subtropical cyclones over the South Atlantic Ocean, the thresholds
    #  are B < 25 m, -|VTL| > -50, and -|VTU| < -10".
    # Tropical and extratropical rows are inherited from C01: Gozzo et al. give
    # only descriptive ("B ~ 0, -VT^L > 0, -VT^U > 0") tropical bounds.
    # -------------------------------------------------------------------------
    "GOZZO14": {
        "tropical":      {"B": (None, 10.0), "VTL": (0.0, None), "VTU": (0.0, None)},
        "subtropical":   {"B": (None, 25.0), "VTL": (-50.0, None), "VTU": (None, -10.0)},
        "extratropical": {"B": (10.0, None), "VTL": (None, 0.0), "VTU": (None, 0.0)},
    },

    # -------------------------------------------------------------------------
    # YANASE14 - global, all basins. Yanase et al. (2014), verbatim:
    # "cyclones are classified as TCs for -V_T^L > 0 and -V_T^U > -10, HCs for
    #  -V_T^L > 0 and -V_T^U < -10, ECs for -V_T^L < -50, and ill-defined
    #  cyclones for the others, where the threshold of -V_T^U is based on
    #  Guishard et al. (2009)."
    # Note: thermal wind ONLY - B is not used. Their "HC" (hybrid cyclone)
    # is the subtropical class; their "ill-defined" class is our UNCLASSIFIED.
    # This is the most permissive tropical definition in the literature
    # (-V_T^U > -10, looser even than C03's -50).
    # -------------------------------------------------------------------------
    "YANASE14": {
        "tropical":      {"B": (None, None), "VTL": (0.0, None), "VTU": (-10.0, None)},
        "subtropical":   {"B": (None, None), "VTL": (0.0, None), "VTU": (None, -10.0)},
        "extratropical": {"B": (None, None), "VTL": (None, -50.0), "VTU": (None, None)},
    },

    # -------------------------------------------------------------------------
    # CAVICCHIA19 - Australian east coast lows. Cavicchia et al. (2019),
    # verbatim: "three classes of cyclones are defined based on the thermal
    # wind parameters V_T^U and V_T^L only: the cold-cored cyclone is
    # associated with -V_T^L < 0 and -V_T^U < 0, the warm-cored cyclone with
    # -V_T^L > 0 and -V_T^U > 0, and the hybrid cyclone with -V_T^L > 0 and
    # -V_T^U < 0."
    # IMPORTANT: Cavicchia et al. deliberately name their classes
    # cold-cored / hybrid / warm-cored, NOT extratropical / subtropical /
    # tropical, because they study a mid-latitude population and state
    # explicitly that "cyclone phase space alone does not distinguish tropical
    # cyclones from warm-seclusion extratropical cyclones (Hart 2003)".
    # The class names are kept aligned with the other sets here only so the
    # tables are comparable; read "tropical" as "deep warm core".
    # -------------------------------------------------------------------------
    "CAVICCHIA19": {
        "tropical":      {"B": (None, None), "VTL": (0.0, None), "VTU": (0.0, None)},
        "subtropical":   {"B": (None, None), "VTL": (0.0, None), "VTU": (None, 0.0)},
        "extratropical": {"B": (None, None), "VTL": (None, 0.0), "VTU": (None, 0.0)},
    },

    # -------------------------------------------------------------------------
    # GUISHARD09 - North Atlantic subtropical storms. Guishard et al. (2009),
    # their list of required characteristics, verbatim: the cyclone must
    # "exhibit a hybrid structure, determined by the CPS criteria of
    #  -|V_T^L| > -10 and -|V_T^U| < -10".
    # This is the set Gozzo et al. (2014) started from before relaxing the
    # -V_T^L bound from -10 to -50 for the South Atlantic.
    # Tropical/extratropical rows from C01 (Guishard et al. define only the
    # hybrid class).
    # -------------------------------------------------------------------------
    "GUISHARD09": {
        "tropical":      {"B": (None, 10.0), "VTL": (0.0, None), "VTU": (0.0, None)},
        "subtropical":   {"B": (None, None), "VTL": (-10.0, None), "VTU": (None, -10.0)},
        "extratropical": {"B": (10.0, None), "VTL": (None, 0.0), "VTU": (None, 0.0)},
    },

    # -------------------------------------------------------------------------
    # C03 - relaxed tropical definition for the South Atlantic.
    # Originating source: Marrafon et al. (2022). Transcribed from Conrado et
    # al. (2024), their Fig. 2a, column C03.
    # Physical justification, from Reboita et al. (2024) discussing Akara:
    # "Some studies, such as Reboita et al. [Iba, 2021] and their references,
    #  have shown tropical cyclones with a moderately warm core, even with
    #  -60 < -|VTU| < 10, which means that the vertical wind shear between 300
    #  and 600 hPa is not so weak compared to the classical definition."
    # The subtropical row is GOZZO14 (Conrado et al. pair C03's tropical row
    # with a South Atlantic subtropical row).
    # -------------------------------------------------------------------------
    "C03": {
        "tropical":      {"B": (-10.0, 10.0), "VTL": (0.0, None), "VTU": (-50.0, None)},
        "subtropical":   {"B": (None, 25.0), "VTL": (-50.0, None), "VTU": (None, -10.0)},
        "extratropical": {"B": (10.0, None), "VTL": (None, 0.0), "VTU": (None, 0.0)},
    },
}

CRITERIA_SOURCES: Dict[str, str] = {
    "C01": "Cavicchia et al. (2019), via Conrado et al. (2024) Fig. 2a",
    "GOZZO14": "Gozzo et al. (2014) subtropical; C01 tropical/extratropical",
    "C03": "Marrafon et al. (2022) tropical, via Conrado et al. (2024) Fig. 2a; "
           "Gozzo et al. (2014) subtropical",
    "YANASE14": "Yanase et al. (2014), global, thermal wind only",
    "CAVICCHIA19": "Cavicchia et al. (2019), Australian east coast lows, "
                   "thermal wind only",
    "GUISHARD09": "Guishard et al. (2009), North Atlantic subtropical storms",
}

CRITERIA_DESCRIPTIONS: Dict[str, str] = {
    "C01": "Strict/classical partition. Tropical requires a warm core through "
           "the whole troposphere (-VTU > 0).",
    "GOZZO14": "South Atlantic subtropical definition (wider B, relaxed -VTL, "
               "explicit upper cold core -VTU < -10). Primary set for "
               "subtropical counts.",
    "C03": "Relaxed tropical definition, admitting moderately warm upper cores "
           "(-VTU > -50). Sensitivity test on the tropical count.",
    "YANASE14": "Cross-basin control. Global thresholds, most permissive "
                "tropical bound (-VTU > -10), with an explicit ill-defined "
                "class. B is not used.",
    "CAVICCHIA19": "Cross-basin control from a mid-latitude population like "
                   "ours (Australian ECLs). B is not used. Their own class "
                   "names are cold-cored / hybrid / warm-cored.",
    "GUISHARD09": "Cross-basin control, North Atlantic. The parent of the "
                  "Gozzo (2014) set before the -VTL relaxation.",
}

# Sets used for the South Atlantic headline results.
PRIMARY_CRITERIA: List[str] = ["C01", "GOZZO14", "C03"]
# Sets applied only to check that the South Atlantic conclusions are not an
# artefact of one basin's threshold choices.
CROSS_BASIN_CRITERIA: List[str] = ["YANASE14", "CAVICCHIA19", "GUISHARD09"]

DEFAULT_CRITERION = "GOZZO14"

# Precedence when a timestep or a cyclone satisfies more than one class.
# The classes overlap by construction (see Conrado et al. 2024, Fig. 2b), so an
# explicit order is required. "Most tropical wins" mirrors the way tropical
# transition studies report their populations: a system is counted as tropical
# if it ever attains tropical structure.
CLASS_PRECEDENCE: List[str] = ["tropical", "subtropical", "extratropical"]

# Fallback label for timesteps satisfying none of the three classes (e.g. the
# "warm tilted", "cold shallow" and "warm symmetrical" corners of Conrado et
# al. 2024, Fig. 2b, which are named but not assigned to a cyclone type).
UNCLASSIFIED = "unclassified"

ALL_CLASSES: List[str] = CLASS_PRECEDENCE + [UNCLASSIFIED]

# =============================================================================
# CANONICAL CLASSIFICATION  (the analysis of record)
# =============================================================================
# Everything above this point is the SENSITIVITY set: six threshold sets crossed
# with four identification rules, used to establish the methodology. The
# canonical analysis uses ONE threshold set and one classification scheme,
# defined here.
#
# Thresholds follow de Souza et al. (2026), who state them as:
#
#   "systems are classified as extratropical when B >> 10 m, -|V_T^L| < 0, and
#    -|V_T^U| < 0; tropical when B < 10 m, -|V_T^L| > 0, and -|V_T^U| > 0
#    (Wood et al., 2023). For subtropical cyclones over the South Atlantic
#    Ocean, the thresholds are -25 < B < 25 m, -|V_T^L| > -50, and
#    -|V_T^U| < -10 (Gozzo et al., 2014, 2017; de Jesus et al., 2022;
#    Cardoso et al., 2022)."
#
# Note the B bound for the subtropical class is TWO-SIDED here (-25 < B < 25),
# following de Souza et al. (2026) and consistent with the two-sided symmetry
# definition of Evans and Hart (2003) ("If -10 m < B < 10 m, the system is
# classified as symmetric"). Gozzo et al. (2014) write it one-sided ("B < 25 m").
# The two-sided form retains 97.1% of subtropical timesteps in this population;
# the 2.9% it removes sit at a median latitude of -45.8 deg and are dominated by
# the decay phase, i.e. exactly the contamination the class should exclude.

CANONICAL: Dict[str, ClassSpec] = {
    "tropical":      {"B": (None, 10.0), "VTL": (0.0, None), "VTU": (0.0, None)},
    "subtropical":   {"B": (-25.0, 25.0), "VTL": (-50.0, None), "VTU": (None, -10.0)},
    "extratropical": {"B": (10.0, None), "VTL": (None, 0.0), "VTU": (None, 0.0)},
}

CANONICAL_SOURCE = ("de Souza et al. (2026), following Wood et al. (2023) for "
                    "extratropical/tropical and Gozzo et al. (2014) for subtropical")

# The three class definitions overlap (e.g. B in (10, 25) with -50 < VTL < 0 and
# VTU < -10 satisfies both the extratropical and the subtropical spec), so a
# precedence is required at timestep level. Same order as the sensitivity runs.
CANONICAL_PRECEDENCE: List[str] = ["tropical", "subtropical", "extratropical"]

# --- Phase classes ----------------------------------------------------------
# A cyclone's state sequence is built from PERSISTENT states only: a class counts
# as a state only when held for >= MIN_PERSISTENCE_HOURS consecutively. This is
# what makes the scheme workable. Without it, 75.5% of the population visits two
# or more classes and the single most common sequence is EC -> SC -> EC, i.e. a
# transient excursion rather than a transition; there is then no defined answer
# for "genesis as X, later Y".

# NOTE ON THE WORD "PURE". In the South Atlantic literature "pure" qualifies the
# GENESIS, not the whole life. Silva et al. (2022) describe Guara as having
# "genese subtropical pura" and Lexi as "transicao subtropical" - and they say of
# Guara, the exemplar of a pure subtropical genesis, that "ao longo do ciclo de
# vida o sistema sofreu transicao para extratropical e posteriormente decaiu".
# Reboita et al. (2021) likewise title their paper "the first pure tropical
# CYCLOGENESIS". So a "pure subtropical cyclone" in that vocabulary is one that
# was BORN subtropical; it may well end its life as something else.
#
# The classes below are therefore NOT called "pure". They say what they are: a
# cyclone with a single persistent state. Pure genesis is reported separately,
# as `pure_genesis` in the step-2 output.
SINGLE_STATE_CLASSES: Dict[str, str] = {
    "EC": "extratropical throughout (no other persistent state)",
    "SC": "subtropical throughout (no other persistent state)",
    "TC": "tropical throughout (no other persistent state)",
}

# A cyclone has "pure X genesis" when its FIRST persistent state is X and that
# state begins within 24 h of genesis - the same window Guishard et al. (2009)
# and Gozzo et al. (2014) use to separate a structure present from the start
# from one acquired through a transition.
PURE_GENESIS_MAX_ONSET_HOURS: float = 24.0

# Transition names. ET is restricted to its established meaning - Evans and Hart
# (2003): "46% of Atlantic tropical storms undergo a process of extratropical
# transition in which the storm evolves FROM A TROPICAL CYCLONE to a baroclinic
# system" - so SC -> EC gets its own name rather than being folded into ET.
TRANSITIONS: Dict[str, str] = {
    "TT": "tropical transition (EC or SC -> TC)",
    "ET": "extratropical transition (TC -> EC)",
    "ST": "subtropical transition (EC -> SC)",
    "SD": "subtropical decay (SC -> EC)",
}

# Precedence when a cyclone shows more than one transition, e.g. EC->SC->TC->SC
# ->EC. The rarest and most physically consequential wins.
TRANSITION_PRECEDENCE: List[str] = ["TT", "ET", "ST", "SD"]

# --- Characteristic classes -------------------------------------------------
# A cyclone that never holds any class for 36 h is not thereby structureless. It
# usually has a clear dominant structure that simply never lasted long enough to
# be IDENTIFIED under the literature threshold. Leaving all of them in one
# undifferentiated "indeterminate" bucket throws that information away.
#
# These classes therefore describe CHARACTERISTICS, not identifications. The
# 36 h requirement of Guishard et al. (2009) and Gozzo et al. (2014) is left
# untouched for the named classes; a cyclone here is explicitly NOT being called
# subtropical, only "showing hybrid characteristics".
#
# Yanase et al. (2014) carry a comparable catch-all ("ill-defined cyclones for
# the others"); this is the same idea, resolved rather than pooled.
CHARACTERISTIC_CLASSES: Dict[str, str] = {
    "EC_like": "extratropical characteristics, not sustained for 36 h",
    "SC_like": "hybrid characteristics, not sustained for 36 h",
    "TC_like": "warm-core characteristics, not sustained for 36 h",
}

# A characteristic class is assigned only when one structure dominates the
# cyclone's classifiable timesteps by at least this share. Below it, the
# structure is genuinely mixed and the cyclone is `undetermined`.
MIN_DOMINANCE: float = 0.5

UNDETERMINED = "undetermined"

# Outcomes for a persistent tropical run that fails the tropical-transition test.
SECLUSION = "warm_seclusion"
INDETERMINATE_WARM = "indeterminate_warm_core"
INDETERMINATE = "indeterminate"

# --- Tropical-transition test ------------------------------------------------
# A persistent tropical run is a genuine TT only if EITHER:
#
#   (A) the persistent state immediately preceding it is SUBTROPICAL. The system
#       has already demonstrated hybrid structure, which is the documented route:
#       Gozzo et al. (2014) on Catarina - "Hurricane Catarina, which began as an
#       extratropical precursor and presented subtropical structure before the
#       transition into a tropical cyclone" - and Reboita et al. (2024) on Akara.
#
#   (B) otherwise (preceded by an extratropical state, or by nothing), the
#       TROPICAL RUN ITSELF must lie in the 20-40 S band and over ocean.
#
# ---------------------------------------------------------------------------
# SUPERSEDED. Branch (A) was removed after testing showed it does not
# discriminate. The Shapiro-Keyser occlusion sequence passes THROUGH hybrid
# structure on its way to the warm seclusion - cold core -> hybrid -> symmetric
# warm core - so "preceded by a subtropical state" is what a seclusion does too.
# With a relaxed persistence gate, branch (A) admitted warm seclusions at 60.2 S
# and 56.9 S, while both plausible cases sat at 29 S and were caught by (B)
# anyway. The path (EC -> TC or SC -> TC) is now RECORDED as a descriptor and no
# longer acts as an alternative acceptance route.
#
# The surviving rule: a persistent tropical run is a tropical transition only if
# it lies equatorward of TT_MAX_POLEWARD_LAT and is mostly over ocean.
# ---------------------------------------------------------------------------
#
# Two design points, both established empirically on this population:
#
#   * The geographic test is applied to the position DURING the tropical run,
#     not at genesis. Six of the sixteen persistent tropical runs here belong to
#     cyclones that formed inside the 20-40 S band, travelled ~30 deg poleward,
#     and only then acquired a warm core at 55-62 S. A genesis-latitude gate
#     lets every one of them through.
#
#   * The life-cycle phase of the tropical run (mature/decay vs
#     incipient/intensification) is RECORDED but is NOT a gate. It is close to
#     tautological - a Shapiro-Keyser warm seclusion is by definition the
#     occluded stage - and used alone it admits a case at 54.7 S while rejecting
#     everything else. Track 20160337, the single case a phase-only rule accepts,
#     was checked against satellite imagery and is a classic extratropical
#     cyclone.
# Guishard et al. (2009) and Gozzo et al. (2014) use a 20-40 deg BAND, bounded on
# both sides, because they are building a SUBTROPICAL climatology and the
# equatorward bound keeps genuinely tropical systems out of it.
#
# For a tropical-transition test the equatorward bound is not merely unnecessary,
# it is wrong: the further equatorward a warm core sits, the more plausible it is
# as tropical. Iba, the first documented pure tropical cyclogenesis in the
# western South Atlantic (Reboita et al. 2021), formed at about 20 S - exactly on
# the edge of that band - and a system at 15 S would be excluded outright.
#
# Only the POLEWARD bound is retained. Its job is to keep Southern Ocean warm
# seclusions out, which is what the sensitivity work showed it does: the
# rejected runs in this population sit at 54-68 S.
TT_MAX_POLEWARD_LAT: float = -40.0
# Fraction of the tropical run that must be over ocean for criterion (B).
TT_MIN_OCEAN_FRACTION: float = 0.5

# Class colours. The subtropical family is GREEN, not the yellow used in the
# first draft: in the shaded phase diagrams a faint yellow sits between the blue
# extratropical and the red tropical region, and where two regions overlap the
# eye reads the blend rather than the class. Green is unambiguous against both
# neighbours and against the grey used for the overlap.
#
# Each transition takes the colour family of its DESTINATION class, lightened:
# ST and SD end subtropical and extratropical respectively.
PHASE_COLORS: Dict[str, str] = {
    "EC": "#1f4e9c",
    "SC": "#1b9e77",
    "TC": "#c0392b",
    "ST": "#66c2a4",
    "TT": "#e74c3c",
    "ET": "#2980b9",
    "SD": "#7fb3d5",
    SECLUSION: "#8e44ad",
    INDETERMINATE_WARM: "#b39ddb",
    INDETERMINATE: "#9e9e9e",
    # Characteristic classes: same hue as the class they resemble, lightened,
    # so a reader sees the kinship and the lower confidence at once.
    "EC_like": "#9db8e0",
    "SC_like": "#a8ddcb",
    "TC_like": "#e8a49c",
    UNDETERMINED: "#cfcfcf",
}


# =============================================================================
# PERSISTENCE, GEOGRAPHIC AND TIMING CRITERIA
# =============================================================================
# Guishard et al. (2009), "Required characteristics of an Atlantic subtropical
# storm", list five conditions. Gozzo et al. (2014) adapt the same structure to
# the South Atlantic. Three of them are implemented here.

# (i) PERSISTENCE.
# Guishard et al. (2009): the cyclone must "persist in its hybrid form for at
# least 36 h (i.e., more than one diurnal cycle)".
# Gozzo et al. (2014): "for more than 36 consecutive hours".
MIN_PERSISTENCE_HOURS: float = 36.0

# (ii) GENESIS LATITUDE BAND.
# Guishard et al. (2009): "attain gales in the 20-40 N latitude band to reduce
# the possibility of tropical and extratropical systems being introduced into
# the dataset".
# Gozzo et al. (2014), criterion 1: "The SC forms between 20 and 40 S."
GENESIS_LAT_BAND: Tuple[float, float] = (-40.0, -20.0)

# (iii) ONSET TIMING RELATIVE TO GENESIS  --  the anti-warm-seclusion filter.
# Guishard et al. (2009): the cyclone must "become subtropical (i.e., attain
# hybrid structure) within 24 h if identified first as a purely cold- or
# warm-cored system", with the rationale stated verbatim:
#
#   "Systems that begin as robust tropical or extratropical cyclones have been
#    rejected because they are deemed in this methodology to only be able to
#    attain the hybrid structure via extratropical transition (ET; Hart and
#    Evans 2001) or tropical transition (Davis and Bosart 2003), respectively."
#
# Gozzo et al. (2014), criterion 3: the thresholds must be attained "within
# 24 h after its genesis if first tracked as an extratropical system".
#
# This is the criterion that separates a genuine hybrid/warm-core GENESIS from
# a warm core acquired LATE in a baroclinic life cycle, i.e. a Shapiro-Keyser
# warm seclusion. Persistence alone cannot do this: a warm seclusion routinely
# persists well beyond 36 h. Cavicchia et al. (2019) state the underlying
# problem directly: "cyclone phase space alone does not distinguish tropical
# cyclones from warm-seclusion extratropical cyclones (Hart 2003)".
MAX_ONSET_HOURS: float = 24.0

# Plot colours, kept consistent across every figure in this analysis.
TYPE_COLORS: Dict[str, str] = {
    "tropical": "#c0392b",
    "subtropical": "#1b9e77",
    "extratropical": "#1f4e9c",
    UNCLASSIFIED: "#9e9e9e",
}


# =============================================================================
# HELPERS
# =============================================================================

def _in_interval(series, interval: Interval):
    """Strict open-interval test, NaN-safe (NaN -> False)."""
    low, high = interval
    mask = series.notna()
    if low is not None:
        mask &= series > low
    if high is not None:
        mask &= series < high
    return mask


def class_mask(df, criterion: str, cyclone_class: str):
    """Boolean mask of timesteps in `df` matching `cyclone_class` under `criterion`.

    Args:
        df: DataFrame with columns B, VTL, VTU (Hart's B, -V_T^L, -V_T^U).
        criterion: key of CRITERIA, e.g. "GOZZO14".
        cyclone_class: "tropical", "subtropical" or "extratropical".

    Returns:
        Boolean Series aligned with df.index.
    """
    spec = CRITERIA[criterion][cyclone_class]
    mask = None
    for param, interval in spec.items():
        m = _in_interval(df[param], interval)
        mask = m if mask is None else (mask & m)
    return mask


def describe_interval(interval: Interval, name: str) -> str:
    """Human-readable rendering of one threshold, e.g. '-50 < VTL'."""
    low, high = interval
    if low is not None and high is not None:
        return f"{low:g} < {name} < {high:g}"
    if low is not None:
        return f"{name} > {low:g}"
    if high is not None:
        return f"{name} < {high:g}"
    return f"{name} unbounded"


def describe_criterion(criterion: str) -> str:
    """Multi-line description of a threshold set, for logs and reports."""
    lines = [f"{criterion}  [{CRITERIA_SOURCES[criterion]}]"]
    for cyclone_class in CLASS_PRECEDENCE:
        spec = CRITERIA[criterion][cyclone_class]
        terms = ", ".join(describe_interval(iv, p) for p, iv in spec.items())
        lines.append(f"    {cyclone_class:<14s} {terms}")
    return "\n".join(lines)


if __name__ == "__main__":
    for key in CRITERIA:
        print(describe_criterion(key))
        print()
