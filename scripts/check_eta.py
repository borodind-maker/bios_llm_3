#!/usr/bin/env python3
"""
BIOS-LLM v3.0-TS Efficiency Validator
-------------------------------------
Calculates η (Eta) metric based on ternary traces and energy cost.
Implements Normative Definition 1 & 5 from the Specification.

Usage:
    python scripts/check_eta.py --trace "-1,0,1,1,0" --energy 0.5 --price 0.0002
"""

import sys
import os
import argparse
import json
from typing import List

# Додаємо кореневу папку в шлях, щоб імпортувати модуль smartbees
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from smartbees.utils.math_helpers import calculate_eta_v3, empirical_entropy_base3
except ImportError:
    print("❌ Error: Could not import 'smartbees.utils.math_helpers'.")
    print("Make sure you are running this script from the project root or 'scripts' folder.")
    sys.exit(1)

def parse_trace(trace_str: str) -> List[int]:
    """Parses a comma-separated string into a list of integers."""
    try:
        # Remove brackets if user pasted a list like "[-1, 0, 1]"
        clean_str = trace_str.replace('[', '').replace(']', '').replace(' ', '')
        return [int(x) for x in clean_str.split(',') if x]
    except ValueError:
        print(f"❌ Error: Invalid trace format. Use comma-separated integers: -1,0,1")
        sys.exit(1)

def generate_report(eta: float, trace: List[int], energy: float, price: float):
    """
    Generates the Mandatory Reporting Template (Spec v3.0 Section 6).
    """
    counts = {i: trace.count(i) for i in [-1, 0, 1]}
    total_segments = len(trace)
    
    # Generate seed for next flight (last 5 symbols or padded)
    seed_window = trace[-5:] if len(trace) >= 5 else trace
    seed_str = str(seed_window).replace(" ", "")

    report = f"""
BIOS-LLM-v3.0-TS session end
--------------------------------------------------
ETA: {eta:.4f} bit/USD
Status: {"✅ OPTIMAL" if eta >= 1.0 else "⚠️ SUBOPTIMAL (< 1.0)"}
Reflexes added: {total_segments} (–1×{counts[-1]}, 0×{counts[0]}, +1×{counts[1]})
Tags updated: {total_segments} segments
Uncertainty zones: {counts[0]}
Next flight ternary mask seed: {seed_str}
<end>
--------------------------------------------------
Input: {energy} Wh @ ${price}/Wh
"""
    print(report)

def main():
    parser = argparse.ArgumentParser(description="Check Economic Optimality (η) for BIOS-LLM traces.")
    
    parser.add_argument('--trace', type=str, required=True,
                        help='Ternary trace string (e.g., "-1,0,1,1,0")')
    parser.add_argument('--energy', type=float, default=0.5,
                        help='Energy consumed in Wh (default: 0.5)')
    parser.add_argument('--price', type=float, default=0.0002,
                        help='Price per Wh in USD (default: 0.0002)')
    parser.add_argument('--json', action='store_true',
                        help='Output in JSON format (for CI/CD pipelines)')

    args = parser.parse_args()

    # 1. Parse Input
    trace = parse_trace(args.trace)
    
    # 2. Calculate Eta
    eta = calculate_eta_v3(trace, args.energy, args.price)
    
    # 3. Output
    if args.json:
        result = {
            "eta": eta,
            "is_optimal": eta >= 1.0,
            "trace_length": len(trace),
            "entropy": empirical_entropy_base3(trace)
        }
        print(json.dumps(result))
    else:
        generate_report(eta, trace, args.energy, args.price)

    # 4. Exit Code (for CI pipelines)
    if eta < 1.0:
        sys.exit(1) # Fail build if suboptimal
    sys.exit(0)

if __name__ == "__main__":
    main()
