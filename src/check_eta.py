#!/usr/bin/env python3
"""
Проста перевірка η >= 1.0 для BIOS-LLM v3.0-TS
"""
import json
import sys

SPEC_FILE = "config/bios-llm-spec-v3.0-ts.json"

def main():
    try:
        with open(SPEC_FILE, encoding="utf-8") as f:
            data = json.load(f)

        # Припустимо, що в специфікації є поля information_gain і energy_cost
        ig  = data.get("information_gain", 0)
        cost= data.get("energy_cost", 1e-9)
        eta = ig / max(cost, 0.01)

        print(f"η = {eta:.2f} bit/USD")
        if eta < 1.0:
            print("❌ η < 1.0 – нижче трійкового оптимуму")
            sys.exit(1)
        print("✅ η ≥ 1.0 – прийнятно")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
