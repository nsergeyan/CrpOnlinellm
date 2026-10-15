"""Numbers reported in the paper (Durasevic, Dumic & Gil-Gala, 2026) that this code reproduces.

All are total relocations over the 840 Caserta test instances.
"""

TLP_TOTAL = 36_024  # lowest-stack rule; the same at every alpha

# PU1 / PU2 (hand-made unrestricted rules), Maximum strategy: (variant, alpha) -> total.
# alpha 1.0 means every container ID is known.
PU_TOTALS = {
    (1, 1.0): 25_049, (2, 1.0): 24_962,
    (1, 0.5): 25_116, (2, 0.5): 25_027,
    (1, 0.3): 25_905, (2, 0.3): 25_826,
    (1, 0.1): 31_719, (2, 0.1): 31_763,
}

# GP, unrestricted scheme, Maximum, terminal set C: median of 30 runs per alpha.
GP_MEDIANS = {0.5: 24_094, 0.3: 24_733, 0.1: 28_985}
