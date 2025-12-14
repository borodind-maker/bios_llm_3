# 🧠 SmartBeesSwam 3CY LLM: BIOS-LLM v3.0-TS

![Release](https://img.shields.io/badge/Release-v3.0--TS-blue)
![Status](https://img.shields.io/badge/Status-NORMATIVE-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Specification](https://img.shields.io/badge/Type-Technical_Spec-orange)

> **Epigraph**: «Binary systems obey. Ternary systems adapt.»

## **📖 Overview**

The **SmartBees LLM System** provides on-device intelligence for autonomous drones, enabling offline decision-making, strategic analysis, and multimodal processing.

At its core lies **BIOS-LLM v3.0-TS**, a ternary-efficient layer that operates during the drone's "Dream State" (charging mode). Instead of binary success/failure, it utilizes **Balanced Ternary Logic** (-1, 0, +1) to maximize information density per watt of energy consumed during the learning process.

## 🔗 Quick Links
- 📄 **[Full Specification](bios_llm_spec_v3.0_TS.txt)** - Complete normative text
- 🏷️ **[Latest Release](https://github.com/borodind-maker/bios_llm_3/releases)** - Version history
- 🐛 **[Report Issues](https://github.com/borodind-maker/bios_llm_3/issues)** - Bug reports
- 💬 **[Discussions](https://github.com/borodind-maker/bios_llm_3/discussions)** - Community forum
- 📜 **[License](LICENSE)** - MIT License terms

### **🚀 Key Features**

1. **Offline Inference**: Runs entirely on-device (Android) using Google's MediaPipe technology. No internet required.
2. **Dual-Mode Operation**:
   * **Tactical Mode**: Real-time reflexes (navigating obstacles).
   * **Strategic Mode (Dreaming)**: Deep theoretical analysis using the BIOS-LLM v3.0 specification.
3. **Economic Optimality**: Automatic validation requiring efficiency $\eta \ge 1.0$ bit/USD.
4. **Context Awareness**: Manages a 2048-token window prioritizing sensors, threats, and mission updates.

---

## **📐 BIOS-LLM v3.0-TS: Normative Specification**

This section defines the "Ternary-Efficiency Layer" standard implemented in this repository.

### **1. Normative Definitions**

| Term | Value / Unit | Notes |
| :---- | :---- | :---- |
| **Information Gain** | $\log_2(3) \cdot N \cdot (1 - H)$ | bits (where $H$ is empirical entropy) |
| **Energy Cost** | $E_{total} \cdot P_{rate}$ | USD ($E$ in Wh, $P$ in $/Wh) |
| **Efficiency ($\eta$)** | $Gain / \max(Cost, 0.01)$ | **Target: $\eta \ge 1.0$ bit/USD** |
| **Ternary Symbol** | $\in \{-1, 0, +1\}$ | Z-score based encoding |

### **2. Ternary Encoding Schema**

Raw telemetry is mapped to ternary states using Z-scores:

* **-1 (Negative)**: $z < -1.0$ (Failure / Threat / Low)
* **0 (Neutral)**: $-1.0 \le z \le 1.0$ (Uncertainty / Normal / Unknown)
* **+1 (Positive)**: $z > 1.0$ (Success / Advantage / High)

**Override Rule**: If `uncertainty_metric > 0.7`, force state **0**.

### **3. Route Tags**

Map segments are tagged with a 3-tuple `[Risk, Stealth, Speed]`:

* `[-1, -1, -1]`: Safe Zone / Passive Stealth / Loiter
* `[+1, +1, +1]`: Danger Zone / Active Beacon / Max Thrust

### **🧮 Mathematical Justification**

Ternary logic provides an information density of $\log_2 3 \approx 1.585$ bits per symbol. This is the closest integer base to Euler's number $e$, offering optimal radix economy for storing "fuzzy" battlefield data where uncertainty (0) is as informative as a confirmed threat (-1).

---

## **🧠 Cognitive Architecture: The "Anti-System"**

Beyond mathematical efficiency, the LLM utilizes a rigorous cognitive framework to prevent strategic blindness.

1. **The "Anti-System"**: A background process that challenges generated conclusions. If the model formulates "X is important", the algorithm forces the generation of "Why X might be irrelevant".
2. **Self-Correction Pipeline**:
   `Thought -> [System Mapping] -> [Uncertainty Search] -> [Alternatives] -> [Friction Assessment] -> [Counter-Question]`
3. **Linguistic Censors**:
   * Forbidden: "must", "best", "victory" (prevents dogmatism).
   * Mandatory: Conditional mood ("could", "might").
4. **The Counter-Question**: Every response must end with an "Open Rupture" — a question challenging the conclusion just reached (e.g., *"But doesn't this analysis assume we know what the enemy doesn't?"*).

---

## **📁 Project Structure**

```text
bios_llm_3/
├── smartbees/
│   ├── app/
│   │   ├── llm/
│   │   │   ├── llm_engine.py        # Core MediaPipe wrapper
│   │   │   ├── context_manager.py   # Token window management
│   │   │   ├── mission_gen.py       # Strategy generation
│   │   │   ├── sensor_translator.py # Telemetry -> Text
│   │   │   └── bios_llm.json        # Normative Config & Thresholds
│   │   └── reflexes/
│   │       └── dynamic_reflex.py    # Implements Ternary Triggers
│   ├── utils/
│   │   └── math_helpers.py          # Z-score, Entropy, & Eta calculations
│   └── ai/
│       └── brain_controller.py      # Optimality Checkpoint logic
├── config/
│   └── reflex_schema_v3.json        # JSON Schema for validation
├── scripts/
│   └── check_eta.py                 # Validation tools
├── .github/workflows/
│   └── validate.yml                 # CI/CD pipeline
└── README.md                        # This specification
```

---

## **⚙️ Installation & Usage**

### **Installation**
```bash
# Clone the repository
git clone https://github.com/borodind-maker/bios_llm_3.git
cd bios_llm_3

# Install required dependencies (if any)
pip install -r requirements.txt
```

### **Quick Start**
1. Read the **[full specification](bios_llm_spec_v3.0_TS.txt)** to understand the normative requirements.
2. Use the provided scripts to validate ternary encoding:
   ```bash
   python scripts/check_eta.py
   ```
3. For implementation, refer to the reference code in the `smartbees/` directory.

### **Validate Efficiency ($\eta$)**
Check if a charging session was economically efficient:

```python
from smartbees.utils.math_helpers import calculate_eta_v3

# Example ternary trace: [-1 (Bad), 0 (Unknown), +1 (Good), +1 (Good)]
trace = [-1, 0, 1, 1]
energy_wh = 0.5  # Energy consumed in watt-hours
price_per_wh = 0.0002  # Price in USD per Wh

eta = calculate_eta_v3(trace, energy_wh, price_per_wh)
print(f"Efficiency: {eta:.2f} bit/USD")
```

---

## **📊 Reporting Template**

The system enforces the following session report format after every charging cycle:

```text
BIOS-LLM-v3.0-TS session end
ETA: 2.34 bit/USD
Reflexes added: 3 (–1×1, 0×1, +1×1)
Tags updated: 5 segments
Uncertainty zones: 7
Next flight ternary mask seed: [0,–1,0,1,0]
<end>
```

---

## **🤝 Contributing**

This is a normative technical specification. Contributions are welcome through:

1. **Issues**: For clarifications, corrections, or discussions.
2. **Discussions**: For theoretical debates and extensions.
3. **Pull Requests**: For well-justified amendments.

Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting changes.

---

## **📄 License & Copyright**

**MIT License** - See [LICENSE](LICENSE) for full terms.

**Copyright © 2025 [UngWin].** All rights reserved.

This specification is maintained by the **SmartBeesSwarm Intelligence Group**.

## **👥 Maintainers & Authors**

**SmartBeesSwarm 3CY & Monte Carlo Intelligence Group** (Uzhhorod, Ukraine)

* **Borodin Dmytro Volodimirov**
* **Borodin Volidymyr Dmytriev**
* 📧 Email: `biosbees@gmail.com`

## **📞 +380634117007**
- **Issues**: [GitHub Issues](https://github.com/borodind-maker/bios_llm_3/issues)
- **Discussions**: [GitHub Discussions](https://github.com/borodind-maker/bios_llm_3/discussions)
- **Author**: [Borodins/UngWinMonte]

---

*"Binary asks: fight or flight? Ternary answers: –1, 0, +1 – and takes the e-fficient height."*
