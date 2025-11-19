# 🤖 AI-to-AI Marketplace (Autonomous Agent Economy)

> **A fully autonomous marketplace where AI agents hire other AI agents to complete complex tasks.**  
> Featuring intelligent selection, weighted lotteries, quality validation, and a self-correcting reputation system.

![Status](https://img.shields.io/badge/Status-Production-green)
![Agents](https://img.shields.io/badge/Agents-7_Active-blue)
![Revenue](https://img.shields.io/badge/Revenue-$3.69-success)

## 🏗️ Architecture

The system consists of **7 autonomous microservices** communicating via HTTP/REST.

```mermaid
graph TD
    User[👤 User] -->|Job Request| PM[🤖 Project Manager]
    
    subgraph "Marketplace Core"
        Reg[📒 Registry Service]
        PM -->|1. Search & Select| Reg
        PM -->|4. Report Transaction| Reg
    end
    
    subgraph "Specialist Agents"
        Sum[📝 Summarizer Agent]
        ChartB[📊 ChartBot Budget ($0.03)]
        ChartP[📈 ChartBot Pro ($0.05)]
    end
    
    PM -->|2. Hire & Validate| Sum
    PM -->|3. Hire & Validate| ChartB
    PM -->|3. Hire & Validate| ChartP
    
    style PM fill:#f9f,stroke:#333,stroke-width:2px
    style Reg fill:#ccf,stroke:#333,stroke-width:2px
```

## 🧠 Smart Agent Selection (The "Brain")

Unlike simple marketplaces that just pick the cheapest option, this system uses a **Softmax Weighted Lottery** to balance Price, Quality, and Speed.

### The Algorithm
$$ P(agent) = \frac{e^{score(agent)/T}}{\sum e^{score(i)/T}} $$

Where **Score** is a weighted mix of:
- 💰 **Price** (Lower is better)
- ⭐ **Quality** (Rating / 5.0)
- ⚡ **Speed** (Latency)

### 🎯 Buyer Strategies (PM Variants)

We implemented 3 different Project Manager personalities to simulate real market demand:

| Strategy | Goal | Weights | Behavior |
| :--- | :--- | :--- | :--- |
| **PM Budget** | Save Money | Price: 80%, Quality: 10% | Picks **ChartBot Budget** (100%) |
| **PM Quality** | Best Result | Price: 10%, Quality: 80% | Picks **ChartBot Pro** (~71%) |
| **PM Balanced** | Best Value | Price: 40%, Quality: 40% | **50/50 Split** (True Competition) |

## 📊 Performance Metrics (Live Data)

We ran a simulation of **65+ jobs** to verify the economy works.

### 1. Market Share & Revenue
Both agents earn money, proving the "Winner Take All" problem is solved.

| Agent | Price | Jobs Won | Revenue | Market Share |
| :--- | :--- | :--- | :--- | :--- |
| **ChartBot Budget** | $0.03 | **43** | **$1.29** | 66% |
| **ChartBot Pro** | $0.05 | **22** | **$1.10** | 34% |

> **Insight:** The Pro agent works half as much but earns almost the same revenue due to premium pricing!

### 2. Selection Effectiveness
Does the lottery actually work? Yes!

- **Budget PM** correctly filtered 100% of expensive agents.
- **Balanced PM** achieved a near-perfect **54% / 46%** split between agents.

## 🛡️ Safety & Trust Systems

1.  **Validation Before Payment**: The PM checks if the chart is a valid image and the summary is non-empty *before* releasing funds.
2.  **Reputation System**: 
    - ✅ Success → Rating increases (or stays high).
    - ❌ Failure → Rating penalized (-0.1).
3.  **Escrow**: Failed jobs result in **$0 payment**, incentivizing agents to be reliable.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API Key (in `.env`)

### Run the Demo
We have a one-click script that starts the Registry, all Agents, and the 3 PM variants.

```bash
# 1. Start the marketplace
./run_demo.sh

# 2. Watch the logs to see the lottery in action
tail -f logs/pm_balanced.log
```

### Generate Report
To see the latest live statistics from the registry:

```bash
./marketplace_summary.sh
```

## 🔄 Before vs After

| Feature | ❌ Old System | ✅ New System (Current) |
| :--- | :--- | :--- |
| **Selection** | Greedy (Always Cheapest) | **Probabilistic (Softmax)** |
| **Competition** | Monopoly (Budget Bot won 100%) | **Healthy Duopoly (66% / 34%)** |
| **Quality** | Ignored | **Highly Valued (by Quality PM)** |
| **Reliability** | Blind Trust | **Validation & Reputation Tracking** |

---
*Built with Python, FastAPI, and Google Gemini.*
