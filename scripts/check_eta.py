#!/usr/bin/env python3
import sys
import os
import argparse
import json
from typing import List

# Add root path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from smartbees.utils.math_helpers import calculate_eta_v3, empirical_entropy_base3
except ImportError:
    print("Error: Could not import 'smartbees.utils.math_helpers'.")
    sys.exit(1)

def parse_trace(trace_str: str) -> List[int]:
    try:
        clean_str = trace_str.replace('[', '').replace(']', '').replace(' ', '')
        return [int(x) for x in clean_str.split(',') if x]
    except ValueError:
        print(f"Error: Invalid trace format.")
        sys.exit(1)

def generate_report(eta: float, trace: List[int], energy: float, price: float):
    counts = {i: trace.count(i) for i in [-1, 0, 1]}
    total_segments = len(trace)
    seed_str = str(trace[-5:] if len(trace) >= 5 else trace).replace(" ", "")
    
    report = f'''
## BIOS-LLM-v3.0-TS session end

## ETA: {eta:.4f} bit/USD Status: {"OPTIMAL" if eta >= 1.0 else "SUBOPTIMAL (< 1.0)"} Reflexes added: {total_segments} (-1x{counts[-1]}, 0x{counts[0]}, +1x{counts[1]}) Tags updated: {total_segments} segments Uncertainty zones: {counts[0]} Next flight ternary mask seed: {seed_str} <end>

Input: {energy} Wh @ ${price}/Wh
'''
    print(report)

def main():
    parser = argparse.ArgumentParser(description="Check Economic Optimality (η)")
    parser.add_argument('--trace', type=str, required=True, help='Trace: "-1,0,1"')
    parser.add_argument('--energy', type=float, default=0.5, help='Energy Wh')
    parser.add_argument('--price', type=float, default=0.0002, help='Price $/Wh')
    args = parser.parse_args()

    trace = parse_trace(args.trace)
    eta = calculate_eta_v3(trace, args.energy, args.price)
    generate_report(eta, trace, args.energy, args.price)

    if eta < 1.0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
