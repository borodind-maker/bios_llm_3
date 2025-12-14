````markdown
# 🧠 SmartBeesSwarm 3CY: BIOS-LLM v3.0-TS

![Release](https://img.shields.io/badge/Release-v3.0--TS-blue)
![Status](https://img.shields.io/badge/Status-NORMATIVE-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Specification](https://img.shields.io/badge/Type-Technical_Spec-orange)

> **Epigraph**: «Binary systems obey. Ternary systems adapt.»

## **📖 Overview**

The **SmartBees LLM System** provides on-device intelligence for autonomous drones, enabling offline decision-making, strategic analysis, and multimodal processing.

At its core lies **BIOS-LLM v3.0-TS**, a ternary-efficient layer that operates during the drone's "Dream State" (charging mode). Instead of binary success/failure, it utilizes **Balanced Ternary Logic** (`-1, 0, +1`) to maximize information density per watt of energy consumed during the learning process.

## 🔗 Quick Links
- 📄 **[Full Specification](bios_llm_spec_v3.0_TS.txt)** - Complete normative text
- ⚛️ **[Quantum Roadmap](QUANTUM_ARCH.md)** - Qutrit implementation & future hybrid architecture
- 🏷️ **[Latest Release](https://github.com/borodind-maker/bios_llm_3/releases)** - Version history
- 🐛 **[Report Issues](https://github.com/borodind-maker/bios_llm_3/issues)** - Bug reports
- 💬 **[Discussions](https://github.com/borodind-maker/bios_llm_3/discussions)** - Community forum

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

## **🏗️ Architecture: The "Brain–Body Split"**

To resolve the conflict between **Safety** (Flight) and **Adaptation** (Learning), the system implements a strict physical separation of concerns, modeled after Daniel Kahneman's "System 1 / System 2" theory.

```mermaid
graph LR
    subgraph S2 [System 2: The Brain]
        direction TB
        LLM[BIOS-LLM Ternary Core]
        Hist[Flight History]
        Sim[Quantum Annealing]
        style LLM fill:#4b0082,stroke:#fff,color:#fff
    end

    subgraph Bridge [The Bridge]
        Comp[Reflex Compiler]
        Valid[Safety Validator]
        style Comp fill:#f9f,stroke:#333
    end

    subgraph S1 [System 1: The Body]
        Reflex[Tactical Reflexes]
        Motor[Motor Control]
        Sensors[Sensors 60Hz]
        style Reflex fill:#228b22,stroke:#fff,color:#fff
    end

    LLM -->|JSON Strategy| Comp
    Comp -->|Deterministic Code| Reflex
    Sensors --> Reflex
    Reflex --> Motor
    Sensors -.->|Logs (Charging)| Hist
````

### **4.1. System 1: The Reflexive Body**

  * **Role**: Survival, Deterministic Execution.
  * **Mode**: **Real-time (Flight)**. Cycle time \< 16ms (60Hz).
  * **Logic**: Low-level optimized code (Python/C++). Direct motor access.
  * **Safety**: **Neural Networks are physically absent** in the control loop. The drone flies on "muscle memory".

### **4.2. System 2: The Analytic Brain**

  * **Role**: Analysis, Strategy Generation, Evolution.
  * **Mode**: **Offline (Charging/Dreaming only)**.
  * **Logic**: Large Language Models (LLM), Reinforcement Learning, Ternary Optimization.
  * **Constraint**: Has **Zero** direct access to flight controls. It cannot crash the drone because it cannot fly it.

### **4.3. The Bridge (Reflex Manager)**

  * **Component**: `reflex_definition_manager.py`
  * **Function**: Acts as a compiler. It translates abstract strategies generated by System 2 (e.g., *"Avoid open areas when windy"*) into safe, validated `if/else` reflex code for System 1.
  * **Result**: Bridges the "Learning Gap" without risking flight safety.

-----

## **🧠 Cognitive Architecture: The "Anti-System"**

Beyond mathematical efficiency and physical safety, the LLM utilizes a rigorous cognitive framework to prevent strategic blindness. This is implemented via the **BIOS Persona** defined in `bios_llm.json`.

### **1. Core Principles**

1.  **The "Anti-System" Protocol**: A background process that challenges generated conclusions. If the model formulates "X is important", the algorithm immediately forces the generation of a counter-argument "Why X might be irrelevant".
2.  **Self-Correction Pipeline**:
    `Thought -> [System Mapping] -> [Uncertainty Search] -> [5+ Alternatives] -> [Counter-Arguments] -> [Friction Assessment] -> [Counter-Question]`
3.  **Linguistic Censors**:
      - Words like **"must"**, **"best"**, **"victory"** are forbidden to prevent dogmatism.
      - Conditional mood ("could", "might") is mandatory.
4.  **Memory as Self-Critique**: The system tags stored "distinctions" with the theory they refute. Weekly memory reviews systematically purge obsolete beliefs (Hypothesis -\> Falsification -\> Update).
5.  **The Counter-Question**: Every response must end with an "Open Rupture" - a question that challenges the conclusion just reached (e.g., *"But doesn't this analysis assume we know what the enemy doesn't?"*).

### **2. Pragmatic Value**

1.  **Prevents Strategic Blindness**: The system cannot hold a single rigid viewpoint. It is forced to see the battlefield from multiple angles simultaneously.
2.  **Models Real Uncertainty**: Simulates the "fog of war" where no "correct" picture exists, only probabilities.
3.  **Cognitive Training**: It doesn't give answers, but trains the operator's (or the Swarm's) cognitive flexibility.

### **3. Philosophical Essence**

It is a meta-system for managing cognitive biases. It creates an **anti-system of thinking** that stands alongside the generation process, acting like a neurosurgeon who cuts and simultaneously analyzes how the cut distorts perception.

> *"The goal is not to find the truth, but to avoid the error of certainty."*

-----

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
├── QUANTUM_ARCH.md                  # Future roadmap
└── README.md                        # This specification
```

-----

## **⚙️ Usage Example**

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

### **Define a Ternary Reflex**

Use the JSON DSL to define temporal triggers based on ternary patterns:

```json
"ternary_trigger": {
  "pattern": [-1, 0, -1],  // Detects sequence: "Threat -> Unknown -> Threat"
  "window_sec": 5,         // Sliding window size
  "tolerance": 0,          // Exact match required
  "sampling_hz": 20        // Check frequency
}
```

-----

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

-----

## **🤝 Contributing**

This is a normative technical specification. Contributions are welcome through **Issues** and **Pull Requests**. Please read our [Contributing Guidelines](https://www.google.com/search?q=CONTRIBUTING.md) before submitting changes.

-----

## **📄 License & Copyright**

**MIT License** - See [LICENSE](https://www.google.com/search?q=LICENSE) for full terms.

**Copyright © 2025 SmartBeesSwarm 3CY Monte Carlo Intelligence Group & Borodin.** All Rights Reserved.

This specification is maintained by the **SmartBeesSwarm Intelligence Group**.

## **👥 Maintainers & Authors**

**SmartBeesSwarm 3CY & Monte Carlo Intelligence Group** (Uzhhorod, Ukraine)

  * **Borodin Dmytro Volodimirov**
  * **Borodin Volidymyr Dmytriev**
  * 📧 Email: `biosbees@gmail.com`

-----

*"Binary asks: fight or flight? Ternary answers: –1, 0, +1 – and takes the e-fficient height."*

```
```
