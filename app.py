import streamlit as st
import json
import time
import random
from groq import Groq
from surgical_config import SURGICAL_PHASES, VITALS_NORMAL, AI_SYSTEM_PROMPT, SURGERY_TYPE
from surgical_engine import init_robot_state, init_vitals, update_vitals, update_robot, get_vitals_status
from surgical_visuals import render_robot_arm, render_knee_map

st.set_page_config(
    page_title="ARIA — Surgical Robot Assistant",
    page_icon="🏥",
    layout="wide",
)

# ── Dark Clinical CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
  html, body, [class*="css"] {
    background-color: #050a14 !important;
    color: #c9d8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
  }
  .stApp { background-color: #050a14 !important; }
  .block-container { padding-top: 1rem !important; }
  h1, h2, h3 { color: #00d4ff !important; letter-spacing: 1px; }
  [data-testid="stSidebar"] { background-color: #030810 !important; border-right: 1px solid #1e3a5f !important; }
  .stButton > button {
    background: #0a1526 !important; color: #00d4ff !important;
    border: 1px solid #00d4ff44 !important; border-radius: 4px !important;
    font-family: monospace !important; font-size: 12px !important;
  }
  .stButton > button:hover { background: #00d4ff22 !important; border-color: #00d4ff !important; }
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00d4ff22, #00ff8822) !important;
    border: 1px solid #00d4ff !important; color: #00d4ff !important; font-weight: bold !important;
  }
  [data-testid="stMetric"] { background: #0a1526 !important; border: 1px solid #1e3a5f !important; border-radius: 6px !important; padding: 8px !important; }
  [data-testid="stMetricValue"] { color: #00d4ff !important; font-size: 1.2rem !important; }
  [data-testid="stMetricLabel"] { color: #5a7a9a !important; font-size: 0.65rem !important; }
  .vital-card { background: #0a1526; border: 1px solid #1e3a5f; border-radius: 8px; padding: 10px; margin: 4px 0; }
  .vital-value { font-size: 20px; font-weight: bold; font-family: monospace; }
  .vital-label { font-size: 10px; color: #5a7a9a; font-family: monospace; }
  .alert-card { background: #1f0a0a; border: 1px solid #ff4444; border-radius: 6px; padding: 8px 12px; margin: 4px 0; font-size: 12px; color: #ff8888; font-family: monospace; }
  .ai-card { background: #0a1f14; border: 1px solid #00ff8844; border-radius: 8px; padding: 12px; margin: 6px 0; font-size: 12px; color: #a0e8c0; font-family: monospace; line-height: 1.6; }
  .phase-card { background: #0a1526; border-left: 3px solid #00d4ff; border-radius: 4px; padding: 8px 12px; margin: 3px 0; font-size: 11px; font-family: monospace; }
  .phase-card.active { background: #0a1f2e; border-color: #00ff88; color: #00ff88; }
  .phase-card.done { border-color: #3a5a3a; color: #5a7a5a; }
  hr { border-color: #1e3a5f !important; }
  .stTextInput input { background: #0a1526 !important; border: 1px solid #1e3a5f !important; color: #c9d8f0 !important; font-family: monospace !important; }
  .stSelectbox label, .stSlider label, .stCheckbox label { color: #5a7a9a !important; font-size: 11px !important; }
  .stProgress > div > div { background: #00d4ff !important; }
  [data-testid="stExpander"] { border: 1px solid #1e3a5f !important; background: #0a1526 !important; }
  .streamlit-expanderHeader { color: #00d4ff !important; font-family: monospace !important; }
</style>
""", unsafe_allow_html=True)

# ── Secrets ───────────────────────────────────────────────────────────────────
default_key = st.secrets.get("GROQ_API_KEY", "")

# ── Session state ─────────────────────────────────────────────────────────────
if "robot_state" not in st.session_state:
    st.session_state.robot_state = init_robot_state()
if "vitals" not in st.session_state:
    st.session_state.vitals = init_vitals()
if "running" not in st.session_state:
    st.session_state.running = False
if "ai_guidance" not in st.session_state:
    st.session_state.ai_guidance = "ARIA online. Awaiting surgical team readiness."
if "procedure_log" not in st.session_state:
    st.session_state.procedure_log = []
if "phase_idx" not in st.session_state:
    st.session_state.phase_idx = 0
if "step" not in st.session_state:
    st.session_state.step = 0

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ SYSTEM CONFIG")
    api_key = st.text_input("GROQ API KEY", value=default_key, type="password", placeholder="gsk_...")
    model = st.selectbox("AI MODEL", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
    sim_speed = st.slider("SIM SPEED (s/step)", 0.05, 0.5, 0.15)
    st.divider()

    st.markdown("### 🏥 PATIENT INFO")
    st.markdown('<span style="color:#5a7a9a;font-size:11px">Patient ID: PT-2024-0847</span>', unsafe_allow_html=True)
    st.markdown('<span style="color:#5a7a9a;font-size:11px">Procedure: Total Knee Replacement</span>', unsafe_allow_html=True)
    st.markdown('<span style="color:#5a7a9a;font-size:11px">Laterality: Right Knee</span>', unsafe_allow_html=True)
    st.markdown('<span style="color:#5a7a9a;font-size:11px">Surgeon: Dr. A. Rahman</span>', unsafe_allow_html=True)
    st.markdown('<span style="color:#5a7a9a;font-size:11px">Anesthesia: General</span>', unsafe_allow_html=True)
    st.divider()

    st.markdown("### 📋 SURGICAL PHASES")
    current_phase = st.session_state.phase_idx
    for i, phase in enumerate(SURGICAL_PHASES):
        if i < current_phase:
            css = "done"
            icon = "✅"
        elif i == current_phase:
            css = "active"
            icon = "▶"
        else:
            css = ""
            icon = "○"
        st.markdown(
            f'<div class="phase-card {css}">{icon} {phase["icon"]} {phase["name"]}'
            f'<span style="float:right;color:#334e6e">{phase["risk"].upper()}</span></div>',
            unsafe_allow_html=True
        )
    st.divider()

    st.markdown("### 🔧 ROBOT CONTROLS")
    estop = st.button("🛑 EMERGENCY STOP", use_container_width=True)
    if estop:
        st.session_state.robot_state["emergency_stop"] = True
        st.session_state.running = False

    reset = st.button("🔄 RESET PROCEDURE", use_container_width=True)
    if reset:
        st.session_state.robot_state = init_robot_state()
        st.session_state.vitals = init_vitals()
        st.session_state.phase_idx = 0
        st.session_state.step = 0
        st.session_state.procedure_log = []
        st.session_state.ai_guidance = "ARIA online. System reset complete."
        st.session_state.running = False
        st.rerun()


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🏥 ARIA — AUTONOMOUS ROBOTIC INTELLIGENCE ASSISTANT")
st.caption(f"Orthopedic Surgery Module · {SURGERY_TYPE} · Real-Time AI Guidance · Powered by Groq + Llama 3")
st.divider()


# ── AI Guidance function ──────────────────────────────────────────────────────
def get_ai_guidance(api_key, robot_state, vitals, phase_idx):
    if not api_key:
        return "⚠️ API key required for AI guidance."
    try:
        client = Groq(api_key=api_key)
        phase = SURGICAL_PHASES[phase_idx]
        alerts = get_vitals_status(vitals) + robot_state.get("alerts", [])
        prompt = AI_SYSTEM_PROMPT.format(
            phase=f'{phase["icon"]} {phase["name"]} (Risk: {phase["risk"]})',
            robot_status=f'Tool: {robot_state["tool"]}, Force: {robot_state["force_applied"]}N, Precision: {robot_state["precision_score"]}%, Collision Risk: {robot_state["collision_risk"]:.0%}',
            vitals=f'HR: {vitals["heart_rate"]}bpm, BP: {vitals["bp_sys"]}/{vitals["bp_dia"]}, SpO2: {vitals["spo2"]}%, Temp: {vitals["temperature"]}°C',
            alerts="; ".join(alerts) if alerts else "None",
        )
        resp = client.chat.completions.create(
            model=model,
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"ARIA guidance unavailable: {str(e)[:60]}"


# ── Vitals renderer ───────────────────────────────────────────────────────────
def render_vitals(vitals):
    def color(val, low, high):
        return "#00ff88" if low <= val <= high else "#ffd700" if (val < low * 0.9 or val > high * 1.1) else "#ff4444"

    hr_c  = color(vitals["heart_rate"],  60, 90)
    bp_c  = color(vitals["bp_sys"],      110, 130)
    sp_c  = color(vitals["spo2"],        96, 100)
    tmp_c = color(vitals["temperature"], 36.0, 37.2)
    rr_c  = color(vitals["resp_rate"],   12, 18)

    cols = st.columns(5)
    with cols[0]:
        st.markdown(f'<div class="vital-card"><div class="vital-label">❤️ HEART RATE</div><div class="vital-value" style="color:{hr_c}">{vitals["heart_rate"]}</div><div class="vital-label">bpm</div></div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f'<div class="vital-card"><div class="vital-label">🩺 BLOOD PRESSURE</div><div class="vital-value" style="color:{bp_c}">{vitals["bp_sys"]}/{vitals["bp_dia"]}</div><div class="vital-label">mmHg</div></div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f'<div class="vital-card"><div class="vital-label">🫁 SpO₂</div><div class="vital-value" style="color:{sp_c}">{vitals["spo2"]}%</div><div class="vital-label">oxygen sat</div></div>', unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f'<div class="vital-card"><div class="vital-label">🌡️ TEMPERATURE</div><div class="vital-value" style="color:{tmp_c}">{vitals["temperature"]}°C</div><div class="vital-label">core temp</div></div>', unsafe_allow_html=True)
    with cols[4]:
        st.markdown(f'<div class="vital-card"><div class="vital-label">💨 RESP RATE</div><div class="vital-value" style="color:{rr_c}">{vitals["resp_rate"]}</div><div class="vital-label">breaths/min</div></div>', unsafe_allow_html=True)


# ── Main layout ───────────────────────────────────────────────────────────────
# Vitals row
st.markdown("### 📊 PATIENT VITALS — LIVE MONITORING")
vitals_ph = st.empty()
with vitals_ph.container():
    render_vitals(st.session_state.vitals)

# Alerts
alerts_ph = st.empty()

# AI Guidance
st.markdown("### 🧠 ARIA — AI SURGICAL GUIDANCE")
ai_ph = st.empty()
ai_ph.markdown(f'<div class="ai-card">💬 {st.session_state.ai_guidance}</div>', unsafe_allow_html=True)

st.divider()

# Main visuals
st.markdown("### 🦾 SURGICAL COCKPIT")
arm_col, knee_col = st.columns([1, 1])
arm_ph  = arm_col.empty()
knee_ph = knee_col.empty()

# Initial render
arm_ph.markdown(render_robot_arm(st.session_state.robot_state), unsafe_allow_html=True)
knee_ph.markdown(render_knee_map(st.session_state.robot_state), unsafe_allow_html=True)

st.divider()

# Controls + log
ctrl_col, log_col = st.columns([1, 2])
with ctrl_col:
    st.markdown("### ▶ PROCEDURE CONTROL")
    if not api_key:
        st.warning("⚠️ Add Groq API key in sidebar")

    start_btn = st.button("▶ BEGIN PROCEDURE", type="primary", use_container_width=True,
                          disabled=st.session_state.running or not api_key)
    step_btn  = st.button("⏭ STEP FORWARD", use_container_width=True,
                          disabled=st.session_state.running)

    st.divider()
    st.markdown("### 📈 METRICS")
    rs = st.session_state.robot_state
    m1, m2 = st.columns(2)
    m1.metric("Precision", f"{rs['precision_score']:.1f}%")
    m2.metric("Force", f"{rs['force_applied']}N")
    m3, m4 = st.columns(2)
    m3.metric("Tremor (raw)", f"{rs['tremor_raw']} mm")
    m4.metric("Tremor (filtered)", f"{rs['tremor_filtered']} mm")

with log_col:
    st.markdown("### 📋 PROCEDURE LOG")
    log_ph = st.empty()
    log_html = ""
    for entry in st.session_state.procedure_log[-8:]:
        log_html += f'<div class="phase-card">[{entry["step"]:03d}] {entry["phase"]} — {entry["event"]}</div>'
    if not log_html:
        log_html = '<div class="phase-card" style="color:#334e6e">Awaiting procedure start…</div>'
    log_ph.markdown(log_html, unsafe_allow_html=True)

prog_ph = st.progress(0, text="Ready to begin procedure")


# ── Simulation loop ───────────────────────────────────────────────────────────
def run_step(api_key, get_ai=False):
    rs    = st.session_state.robot_state
    vitals = st.session_state.vitals
    phase_idx = st.session_state.phase_idx
    step = st.session_state.step

    if phase_idx >= len(SURGICAL_PHASES):
        return False

    phase = SURGICAL_PHASES[phase_idx]
    rs["phase_idx"] = phase_idx

    # Update simulation
    rs = update_robot(rs, phase_idx, step)
    vitals = update_vitals(vitals, phase_idx, rs["emergency_stop"])

    # Log entry
    event = f'{phase["icon"]} {phase["name"]} | Tool: {rs["tool"]} | Force: {rs["force_applied"]}N | Precision: {rs["precision_score"]:.1f}%'
    st.session_state.procedure_log.append({"step": step, "phase": phase["name"], "event": event})

    # Advance phase
    steps_in_phase = phase["duration"]
    phase_step = step % max(1, sum(p["duration"] for p in SURGICAL_PHASES[:phase_idx+1]))
    if (step + 1) % steps_in_phase == 0 and phase_idx < len(SURGICAL_PHASES) - 1:
        st.session_state.phase_idx += 1

    st.session_state.robot_state = rs
    st.session_state.vitals = vitals
    st.session_state.step += 1

    # Get AI guidance every N steps
    if get_ai and step % 5 == 0:
        st.session_state.ai_guidance = get_ai_guidance(api_key, rs, vitals, phase_idx)

    return True


def refresh_ui():
    rs     = st.session_state.robot_state
    vitals = st.session_state.vitals

    with vitals_ph.container():
        render_vitals(vitals)

    # Alerts
    all_alerts = get_vitals_status(vitals) + rs.get("alerts", [])
    if all_alerts:
        alert_html = "".join([f'<div class="alert-card">{a}</div>' for a in all_alerts])
        alerts_ph.markdown(alert_html, unsafe_allow_html=True)
    else:
        alerts_ph.empty()

    ai_ph.markdown(f'<div class="ai-card">💬 {st.session_state.ai_guidance}</div>', unsafe_allow_html=True)
    arm_ph.markdown(render_robot_arm(rs), unsafe_allow_html=True)
    knee_ph.markdown(render_knee_map(rs), unsafe_allow_html=True)

    # Log
    log_html = ""
    for entry in st.session_state.procedure_log[-8:]:
        log_html += f'<div class="phase-card">[{entry["step"]:03d}] {entry["phase"]} — {entry["event"]}</div>'
    log_ph.markdown(log_html, unsafe_allow_html=True)

    # Metrics
    m1.metric("Precision", f"{rs['precision_score']:.1f}%")
    m2.metric("Force", f"{rs['force_applied']}N")
    m3.metric("Tremor (raw)", f"{rs['tremor_raw']} mm")
    m4.metric("Tremor (filtered)", f"{rs['tremor_filtered']} mm")

    # Progress
    total_steps = sum(p["duration"] for p in SURGICAL_PHASES)
    pct = min(1.0, st.session_state.step / total_steps)
    phase = SURGICAL_PHASES[min(st.session_state.phase_idx, len(SURGICAL_PHASES)-1)]
    prog_ph.progress(pct, text=f'Phase {st.session_state.phase_idx+1}/{len(SURGICAL_PHASES)}: {phase["icon"]} {phase["name"]}')


# ── Triggers ──────────────────────────────────────────────────────────────────
if step_btn:
    run_step(api_key, get_ai=True)
    refresh_ui()

if start_btn and api_key:
    st.session_state.running = True
    total_steps = sum(p["duration"] for p in SURGICAL_PHASES)

    for i in range(total_steps):
        if st.session_state.robot_state.get("emergency_stop"):
            st.session_state.running = False
            break
        if st.session_state.phase_idx >= len(SURGICAL_PHASES):
            break
        get_ai = (i % 6 == 0)
        run_step(api_key, get_ai=get_ai)
        refresh_ui()
        time.sleep(sim_speed)

    st.session_state.running = False

    # Final summary
    if not st.session_state.robot_state.get("emergency_stop"):
        st.balloons()
        st.success("✅ PROCEDURE COMPLETE — Total Knee Replacement successful")
        fc1, fc2, fc3, fc4 = st.columns(4)
        fc1.metric("Total Steps",     st.session_state.step)
        fc2.metric("Final Precision", f"{st.session_state.robot_state['precision_score']:.1f}%")
        fc3.metric("Phases Completed", f"{min(st.session_state.phase_idx, len(SURGICAL_PHASES))}/{len(SURGICAL_PHASES)}")
        fc4.metric("Log Entries",     len(st.session_state.procedure_log))

        with st.expander("📋 Full Procedure Log"):
            for entry in st.session_state.procedure_log:
                st.markdown(f'`[{entry["step"]:03d}]` **{entry["phase"]}** — {entry["event"]}')
