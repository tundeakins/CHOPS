import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

st.set_page_config(page_title="CHOPS", layout="wide")

st.title("CHOPS")
st.markdown("**C**HEOPS **H**elper for **O**bservation **P**hase **S**cheduling  —  visualize the observation window for a planetary transit.")

# ── Synced slider + number-input helper ──────────────────────────────────────
def synced_slider(label, min_val, max_val, default, step, key, fmt="%.2f", help=None,
                  log_scale=False):
    """Slider with an adjacent number-input box kept in sync via session_state.
    When log_scale=True the slider operates in log10 space; the number input and
    returned value are always in linear space."""
    s_key = f"_sl_{key}"
    n_key = f"_ni_{key}"
    if key not in st.session_state:
        st.session_state[key] = float(default)

    if log_scale:
        import math as _math
        log_min = _math.log10(min_val)
        log_max = _math.log10(max_val)
        log_step = (log_max - log_min) / 400  # ~400 steps across the range

        def _on_slider():
            st.session_state[key] = round(10 ** st.session_state[s_key], 6)
            st.session_state[n_key] = st.session_state[key]

        def _on_input():
            st.session_state[key] = float(np.clip(st.session_state[n_key], min_val, max_val))
            st.session_state[s_key] = _math.log10(st.session_state[key])

        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.slider(label, min_value=log_min, max_value=log_max,
                      value=_math.log10(float(st.session_state[key])),
                      step=log_step, key=s_key, on_change=_on_slider,
                      format="", help=help)
        with col2:
            st.number_input("val", min_value=float(min_val), max_value=float(max_val),
                            value=float(st.session_state[key]), step=float(step),
                            key=n_key, on_change=_on_input,
                            label_visibility="collapsed", format=fmt)
    else:
        def _on_slider():
            st.session_state[key] = float(st.session_state[s_key])
            st.session_state[n_key] = st.session_state[key]

        def _on_input():
            st.session_state[key] = float(np.clip(st.session_state[n_key], min_val, max_val))
            st.session_state[s_key] = st.session_state[key]

        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.slider(label, min_value=float(min_val), max_value=float(max_val),
                      value=float(st.session_state[key]), step=float(step),
                      key=s_key, on_change=_on_slider, help=help)
        with col2:
            st.number_input("val", min_value=float(min_val), max_value=float(max_val),
                            value=float(st.session_state[key]), step=float(step),
                            key=n_key, on_change=_on_input,
                            label_visibility="collapsed", format=fmt)
    return st.session_state[key]

# ── Sidebar sliders ──────────────────────────────────────────────────────────
st.sidebar.header("Transit Parameters")

P_days = synced_slider("Orbital Period P (days)", 0.5, 200.0, 1.5, 0.05, "P_days", fmt="%.3f",
                       log_scale=True)
P_hr   = P_days * 24.0

trans_dur_hr = synced_slider("Transit Duration (hr)", 0.1, 24.0, 2.5, 0.1, "trans_dur", fmt="%.1f")

pre_trans_baseline_dur_hr = synced_slider(
    "Pre-transit Baseline (hr)", 0.1, 6.0, 1.65, 0.05, "pre_base", fmt="%.2f"
)
post_trans_baseline_dur_hr = synced_slider(
    "Post-transit Baseline (hr)", 0.1, 6.0,
    st.session_state.get("post_base", st.session_state.get("pre_base", 1.65)),
    0.05, "post_base", fmt="%.2f"
)
obs_slack_hr = synced_slider(
    "Observation Slack Window (hr)", 0.1, 6.0, 1.0, 0.1, "obs_slack", fmt="%.1f",
    help="Extra time allowed before the latest observation start"
)

# T0 uncertainty — unit toggle
t0_unit = st.sidebar.radio("T0 Uncertainty units", ["hr", "min"], horizontal=True)
if t0_unit == "hr":
    T0_unc_raw = synced_slider("T0 Uncertainty (hr)", 0.0, 5.0, 0.0, 0.05, "t0_hr", fmt="%.2f")
    T0_unc_hr  = T0_unc_raw
else:
    T0_unc_raw = synced_slider("T0 Uncertainty (min)", 0.0, 300.0, 0.0, 1.0, "t0_min", fmt="%.0f")
    T0_unc_hr  = T0_unc_raw / 60.0

# Ingress/egress duration — unit toggle
ing_unit = st.sidebar.radio("Ingress/Egress Duration units", ["hr", "min"], horizontal=True)
if ing_unit == "hr":
    ingress_raw    = synced_slider("Ingress/Egress Duration (hr)", 0.05, 3.0, 0.5, 0.05, "ing_hr", fmt="%.2f")
    ingress_dur_hr = ingress_raw
else:
    ingress_raw    = synced_slider("Ingress/Egress Duration (min)", 1.0, 180.0, 30.0, 1.0, "ing_min", fmt="%.0f")
    ingress_dur_hr = ingress_raw / 60.0

# Fixed transit depth
trans_depth_ppm = 5000

# ── Derived phases ────────────────────────────────────────────────────────────
half_dur_phase   = 0.5 * trans_dur_hr / P_hr
ingress_frac     = min(ingress_dur_hr / trans_dur_hr * 2, 0.49)  # clamp so ingress < half-duration
t0_unc_phase     = T0_unc_hr / P_hr
baseline_phase      = pre_trans_baseline_dur_hr / P_hr
post_baseline_phase = post_trans_baseline_dur_hr / P_hr
slack_phase      = obs_slack_hr / P_hr

transit_center   = 1.0                 # transit centred at phase 1.0

# Observation start window
latest_phase_start   = 1.0 - (baseline_phase + half_dur_phase + t0_unc_phase)
earliest_phase_start = 1.0 - (slack_phase + baseline_phase + half_dur_phase + t0_unc_phase)

# Transit boundary phases (nominal ± T0 uncertainty)
# T1: start of ingress,  T2: end of ingress,  T3: start of egress,  T4: end of egress
ingress_frac_phase = ingress_frac * half_dur_phase   # ingress width in phase

ingress_earliest = transit_center - half_dur_phase - t0_unc_phase   # T1 earliest
ingress_latest   = transit_center - half_dur_phase + t0_unc_phase   # T1 latest
t2_earliest      = transit_center - half_dur_phase + ingress_frac_phase - t0_unc_phase  # T2 earliest
t2_latest        = transit_center - half_dur_phase + ingress_frac_phase + t0_unc_phase  # T2 latest
t3_earliest      = transit_center + half_dur_phase - ingress_frac_phase - t0_unc_phase  # T3 earliest
t3_latest        = transit_center + half_dur_phase - ingress_frac_phase + t0_unc_phase  # T3 latest
egress_earliest  = transit_center + half_dur_phase - t0_unc_phase   # T4 earliest
egress_latest    = transit_center + half_dur_phase + t0_unc_phase   # T4 latest

# ── Metric cards ──────────────────────────────────────────────────────────────
obs_dur_hr = pre_trans_baseline_dur_hr + 2 * T0_unc_hr + trans_dur_hr + post_trans_baseline_dur_hr

c1, c2, c3, c4 = st.columns(4)
c1.metric("Earliest Phase Start",        f"{earliest_phase_start:.5f}")
c2.metric("Latest Phase Start",          f"{latest_phase_start:.5f}")
c3.metric("Start Window Width",          f"{slack_phase:.5f}  ({obs_slack_hr:.1f} hr)")
c4.metric("Total Obs. Duration (ex. slack)", f"{obs_dur_hr:.2f} hr")

# ── Transit model (trapezoid) ─────────────────────────────────────────────────
def trapezoid_transit(phase_arr, center, half_dur, ingress_frac, depth):
    """Return normalised flux array for a trapezoidal transit."""
    flux = np.ones_like(phase_arr)
    iw   = ingress_frac * half_dur
    t1, t2 = center - half_dur, center - half_dur + iw
    t3, t4 = center + half_dur - iw, center + half_dur

    ingress_mask = (phase_arr >= t1) & (phase_arr < t2)
    flat_mask    = (phase_arr >= t2) & (phase_arr <= t3)
    egress_mask  = (phase_arr > t3) & (phase_arr <= t4)

    if t2 > t1:
        flux[ingress_mask] = 1 - depth * (phase_arr[ingress_mask] - t1) / (t2 - t1)
    flux[flat_mask] = 1 - depth
    if t4 > t3:
        flux[egress_mask] = 1 - depth * (t4 - phase_arr[egress_mask]) / (t4 - t3)
    return flux

depth   = trans_depth_ppm / 1e6
x_min   = earliest_phase_start
post_baseline_end = egress_latest + post_baseline_phase
x_max   = post_baseline_end
phase   = np.linspace(x_min, x_max, 3000)

flux_nominal = trapezoid_transit(phase, transit_center, half_dur_phase, ingress_frac, depth)
flux_early   = trapezoid_transit(phase, transit_center - t0_unc_phase, half_dur_phase, ingress_frac, depth)
flux_late    = trapezoid_transit(phase, transit_center + t0_unc_phase, half_dur_phase, ingress_frac, depth)

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor("#0e1117")
ax.set_facecolor("#0e1117")

# colour palette
C_WIN      = "#44dd66"
C_BASE     = "#4488ff"
C_T0       = "#ff9900"
C_TRANSIT  = "#aaaaaa"
C_TICK     = "#cccccc"

# y limits: tight — banner is drawn in axes-fraction space, not data space
y_bot = 1 - 1.6 * depth
y_top = 1.008
# Banner occupies the top 8 % of the axes (axes-fraction coords)
BAN_LO_F, BAN_HI_F = 0.92, 1.00

# ── Region fills (full height) ───────────────────────────────────────────────
ax.axvspan(earliest_phase_start, latest_phase_start, alpha=0.22, color=C_WIN,   zorder=1)
ax.axvline(earliest_phase_start, color=C_WIN, ls="--", lw=1.5, alpha=0.9)
ax.axvline(latest_phase_start,   color=C_WIN, ls="--", lw=1.5, alpha=0.9)
ax.axvspan(latest_phase_start,   ingress_earliest,    alpha=0.18, color=C_BASE, zorder=1)
ax.axvspan(ingress_earliest,     ingress_latest,      alpha=0.35, color=C_T0,   zorder=2)
ax.axvspan(egress_earliest,      egress_latest,       alpha=0.35, color=C_T0,   zorder=2)
ax.axvspan(egress_latest,        post_baseline_end,   alpha=0.18, color=C_BASE, zorder=1)
ax.fill_between(phase, flux_early, flux_late, alpha=0.28, color=C_T0, zorder=3)

# ── Mid-transit vertical line ─────────────────────────────────────────────────
ax.axvline(transit_center, color="#ffffff", ls=":", lw=1.2, alpha=0.5, zorder=4)

# ── Light curve ───────────────────────────────────────────────────────────────
ax.plot(phase, flux_nominal, color="white", lw=2.5, zorder=5)

# ── Duration banner at top (axes-fraction y via blended transform) ─────────────
from matplotlib.transforms import blended_transform_factory
_btrans = blended_transform_factory(ax.transData, ax.transAxes)

def banner_segment(x0, x1, color, label):
    """Draw a thin coloured rectangle at the very top of the axes."""
    if x1 <= x0:
        return
    rect = mpatches.Rectangle(
        (x0, BAN_LO_F), x1 - x0, BAN_HI_F - BAN_LO_F,
        transform=_btrans, color=color, alpha=0.78, zorder=6, clip_on=True
    )
    ax.add_patch(rect)
    for xv in (x0, x1):
        ax.plot([xv, xv], [BAN_LO_F, BAN_HI_F], color="#0e1117", lw=0.8,
                transform=_btrans, zorder=7, clip_on=True)
    cx = (x0 + x1) / 2
    hrs = (x1 - x0) * P_hr
    min_width = (x_max - x_min) * 0.045
    if (x1 - x0) > min_width:
        ax.text(cx, (BAN_LO_F + BAN_HI_F) / 2, f"{label}  {hrs:.2f} hr",
                transform=_btrans, ha="center", va="center",
                fontsize=6.5, color="white", fontweight="bold", zorder=8)

banner_segment(earliest_phase_start, latest_phase_start, C_WIN,     "Slack\n")
banner_segment(latest_phase_start,   ingress_earliest,   C_BASE,    "Pre-transit\nbaseline\n")
banner_segment(ingress_earliest,     ingress_latest,     C_T0,      "T0 unc\n")
banner_segment(ingress_latest,       egress_earliest,    C_TRANSIT, "Transit\n")
banner_segment(egress_earliest,      egress_latest,      C_T0,      "T0 unc\n")
banner_segment(egress_latest,        post_baseline_end,  C_BASE,    "Post-transit\nbaseline\n")

# ── Contact point annotations ─────────────────────────────────────────────────
# T1/T4 labelled at bottom; T2/T3 labelled slightly higher to avoid overlap
# Each entry: (phase, label, y_offset_fraction_above_bot, color)
def _contact_label(ph, label, y_frac, color):
    ax.axvline(ph, color=color, ls=":", lw=1.0, alpha=0.7, zorder=4)
    y_data = y_bot + (y_top - y_bot) * y_frac
    ax.text(ph, y_data, f"{label}\n{ph:.5f}", ha="center", va="bottom",
            fontsize=7, color=color, zorder=8,
            bbox=dict(boxstyle="round,pad=0.15", fc="#0e1117", ec="none", alpha=0.7))

C_T2T3 = "#ff55cc"   # distinct colour for T2/T3

if T0_unc_hr == 0:
    _contact_label(ingress_earliest, "T1",  0.01, C_T0)
    _contact_label(t2_earliest,      "T2",  0.16, C_T2T3)
    _contact_label(t3_earliest,      "T3",  0.16, C_T2T3)
    _contact_label(egress_latest,    "T4",  0.01, C_T0)
else:
    _contact_label(ingress_earliest, "T1-early", 0.01, C_T0)
    _contact_label(ingress_latest,   "T1-late",  0.01, C_T0)
    _contact_label(t2_earliest,      "T2-early", 0.18, C_T2T3)
    _contact_label(t2_latest,        "T2-late",  0.18, C_T2T3)
    _contact_label(t3_earliest,      "T3-early", 0.18, C_T2T3)
    _contact_label(t3_latest,        "T3-late",  0.18, C_T2T3)
    _contact_label(egress_earliest,  "T4-early", 0.01, C_T0)
    _contact_label(egress_latest,    "T4-late",  0.01, C_T0)

# ── Obs-start annotations ─────────────────────────────────────────────────────
for ph, lbl in [(earliest_phase_start, "Earliest\nstart"), (latest_phase_start, "Latest\nstart")]:
    ax.text(ph, BAN_LO_F - 0.01, f"{lbl}\n{ph:.5f}", ha="center", va="top",
            transform=_btrans, fontsize=10, color=C_WIN, zorder=8,
            bbox=dict(boxstyle="round,pad=0.15", fc="#0e1117", ec="none", alpha=0.7))

# ── Axes style ────────────────────────────────────────────────────────────────
t0_label  = f"{T0_unc_raw:.0f} min" if t0_unit == "min" else f"{T0_unc_raw:.2f} hr"
ing_label = f"{ingress_raw:.0f} min" if ing_unit == "min" else f"{ingress_raw:.2f} hr"

legend_handles = [
    mpatches.Patch(color=C_WIN,     alpha=0.5, label=f"Obs. start window ({obs_slack_hr:.1f} hr slack)"),
    mpatches.Patch(color=C_BASE,    alpha=0.4, label=f"Pre/post-transit baseline ({pre_trans_baseline_dur_hr:.1f} / {post_trans_baseline_dur_hr:.1f} hr)"),
    mpatches.Patch(color=C_T0,      alpha=0.5, label=f"T0 uncertainty / T1 & T4 contacts (±{t0_label})"),
    mpatches.Patch(color=C_T2T3,    alpha=0.6, label=f"T2 (end ingress) & T3 (start egress)  |  ingress {ing_label}"),
    mpatches.Patch(color=C_TRANSIT, alpha=0.6, label=f"Transit ({trans_dur_hr:.1f} hr)"),
    plt.Line2D([0], [0], color="white", lw=2.5, label="Transit (nominal T0)"),
]
# ax.legend(handles=legend_handles, loc="lower left",
#           facecolor="#1e2130", labelcolor=C_TICK, fontsize=9, framealpha=0.85)
ax.set_title("CHOPS — Planetary Transit Observation Window", color="white", fontsize=13, pad=10)

ax.set_xlabel("Orbital Phase", color=C_TICK, fontsize=11)
ax.set_ylabel("Relative Flux", color=C_TICK, fontsize=11)
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_bot, y_top)

# Generate ticks anchored at transit centre (1.0) so it always appears
import math
_tick_step = (x_max - x_min) / 10
_magnitude = 10 ** math.floor(math.log10(_tick_step))
_tick_step  = round(_tick_step / _magnitude) * _magnitude or _magnitude
_start = math.ceil((x_min - transit_center) / _tick_step) * _tick_step + transit_center
phase_tick_vals = np.round(np.arange(_start, x_max + _tick_step * 0.01, _tick_step), 8)

ax.set_xticks(phase_tick_vals)
tick_labels = [f"{p:.4f}" for p in phase_tick_vals]
ax.set_xticklabels(tick_labels, color=C_TICK, fontsize=8, rotation=30, ha="right")

# Bold + highlight the transit-centre label
for lbl, val in zip(ax.get_xticklabels(), phase_tick_vals):
    if abs(val - transit_center) < _tick_step * 0.01:
        lbl.set_color("#ffffff")
        lbl.set_fontweight("bold")
ax.tick_params(colors=C_TICK, labelleft=False, left=False)
ax.grid(True, alpha=0.18, color="#444444")
for sp in ax.spines.values():
    sp.set_edgecolor("#444444")

st.pyplot(fig)

# ── Formula display ───────────────────────────────────────────────────────────
st.divider()
st.subheader("Formulae")

fc1, fc2 = st.columns(2)
with fc1:
    st.markdown("**Latest Phase Start**")
    st.latex(
        r"\phi_{\rm latest} = 1 - "
        r"\frac{t_{\rm baseline} + 0.5\,t_{\rm transit} + \sigma_{T_0}}{P}"
    )
    st.code(
        f"= 1 − ({pre_trans_baseline_dur_hr:.2f} + 0.5×{trans_dur_hr:.2f} + {T0_unc_hr:.3f}) / {P_hr:.2f} hr  [P = {P_days:.2f} d]\n"
        f"= {latest_phase_start:.6f}"
    )

with fc2:
    st.markdown(f"**Earliest Phase Start**  *({obs_slack_hr:.1f} hr slack)*")
    st.latex(
        r"\phi_{\rm earliest} = 1 - "
        r"\frac{t_{\rm slack} + t_{\rm baseline} + 0.5\,t_{\rm transit} + \sigma_{T_0}}{P}"
    )
    st.code(
        f"= 1 − ({obs_slack_hr:.2f} + {pre_trans_baseline_dur_hr:.2f} + 0.5×{trans_dur_hr:.2f} + {T0_unc_hr:.3f}) / {P_hr:.2f} hr  [P = {P_days:.2f} d]\n"
        f"= {earliest_phase_start:.6f}"
    )

# ── Parameter summary table ───────────────────────────────────────────────────
st.divider()
st.subheader("Parameter Summary")
st.table({
    "Parameter": [
        "Orbital Period P",
        "Transit Duration",
        "Ingress/Egress Duration",
        "Pre-transit Baseline",
        "Post-transit Baseline",
        "T0 Uncertainty",
        "Transit Depth",
        "Total Obs. Duration (excl. slack)",
        "Latest Phase Start",
        "Earliest Phase Start",
        "Start Window Width",
    ],
    "Value": [
        f"{P_days:.2f} days  ({P_hr:.2f} hr)",
        f"{trans_dur_hr:.2f} hr  ({half_dur_phase*2:.5f} in phase)",
        f"{ing_label}  ({ingress_dur_hr:.3f} hr)",
        f"{pre_trans_baseline_dur_hr:.2f} hr  ({baseline_phase:.5f} in phase)",
        f"{post_trans_baseline_dur_hr:.2f} hr  ({post_baseline_phase:.5f} in phase)",
        f"±{t0_label}  (±{T0_unc_hr:.3f} hr  /  ±{t0_unc_phase:.5f} in phase)",
        f"{trans_depth_ppm} ppm  (fixed)",
        f"{obs_dur_hr:.2f} hr",
        f"{latest_phase_start:.6f}",
        f"{earliest_phase_start:.6f}",
        f"{slack_phase:.6f}  ({obs_slack_hr:.2f} hr)",
    ],
})
