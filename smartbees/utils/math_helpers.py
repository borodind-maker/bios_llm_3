import math
import statistics
from typing import List

def calculate_z_scores(values: List[float]) -> List[float]:
    """
    Normative Definition 2: Reward Scale = Z-score.
    """
    if len(values) < 2:
        return [0.0] * len(values)
    mu = statistics.mean(values)
    sigma = statistics.stdev(values)
    if sigma == 0:
        return [0.0] * len(values)
    return [(v - mu) / sigma for v in values]

def to_ternary_symbol(z_score: float, uncertainty: float, threshold: float = 1.0) -> int:
    """
    Normative Definition 2: Encoding Schema.
    """
    if uncertainty > 0.7:
        return 0
    if z_score < -threshold:
        return -1
    elif z_score > threshold:
        return 1
    else:
        return 0

def empirical_entropy_base3(trace: List[int]) -> float:
    """Calculates empirical entropy H (base 3)."""
    if not trace: return 0.0
    counts = {s: trace.count(s) for s in [-1, 0, 1]}
    total = len(trace)
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log(p, 3)
    return entropy

def calculate_eta_v3(trace: List[int], energy_wh: float, price_per_wh: float) -> float:
    """
    Normative Definition 1: η (eta) calculation.
    """
    if not trace: return 0.0
    N = len(trace)
    H = empirical_entropy_base3(trace)
    info_gain_bits = math.log2(3) * N * (1.0 - H)
    effective_cost = max(energy_wh * price_per_wh, 0.01)
    return info_gain_bits / effective_cost
