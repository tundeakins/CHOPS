# CHORE — CHEOPS Helper for Observation Request Entry

An interactive Streamlit app for planning planetary transit observations with the [CHEOPS](https://www.esa.int/Science_Exploration/Space_Science/Cheops) space telescope. Given a set of transit and orbital parameters, CHORE computes and visualises the valid observation window and outputs the values needed to fill in a PHT2 observation request.

---

## Features

- **Transit window visualisation** — phase-folded plot showing the pre/post-transit baselines, T0 uncertainty regions, ingress/egress contact points, and the observation start slack window
- **Dual transit curves** — white curve (latest start) and red curve (earliest start) drawn at the correct phases, with a small vertical offset for clarity
- **Visit duration** — computed in both hours and CHEOPS orbits (98.77 min period)
- **PHT2 parameter table** — ready-to-copy values: transit period, visit duration, earliest and latest start phases, and optional T2/T3 phase ranges
- **Formulae panel** — displays the exact equations and numeric substitution used to derive the start phases
- **T2/T3 phase ranges** — toggle on ingress/egress contacts with configurable duration (hours or minutes)
- **Custom phase highlights** — free-form text input to shade arbitrary phase ranges on the plot
- **JD ↔ UTC converter** — sidebar tool to convert between Julian Date and calendar date/time

---

## Installation

```bash
git clone https://github.com/tundeakins/CHORE.git
cd CHORE
pip install -r requirements.txt
```

**Requirements:** `streamlit`, `matplotlib`, `numpy` (Python 3.8+)

---

## Usage

```bash
streamlit run transit_scheduler.py
```

Then open the URL shown in the terminal (usually `http://localhost:8501`).

### Sidebar parameters

| Parameter | Description |
|---|---|
| Orbital Period P | Planet orbital period in days |
| Transit Duration | First to last contact (T1–T4) in hours |
| Pre-transit Baseline | Required out-of-transit baseline before ingress |
| Post-transit Baseline | Required out-of-transit baseline after egress |
| Observation Slack Window | Extra time allowed before the latest start (carved from the post-transit baseline) |
| T0 Uncertainty | 1-σ uncertainty on the predicted mid-transit time (hours or minutes) |
| Ingress/Egress Duration | Duration of T1→T2 or T3→T4 (assumed equal); shown when T2/T3 ranges are enabled |


## Output — PHT2 values

The table at the bottom of the page lists the values required for a CHEOPS PHT2 observation request:

- Transit Period [days]
- Visit Duration [CHEOPS orbits]
- Earliest Start Phase
- Latest Start Phase
- Phase Ranges for T2/T3 (when ingress/egress is enabled)
