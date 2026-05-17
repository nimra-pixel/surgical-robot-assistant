import streamlit as st
import json
import time
import random
import datetime
from groq import Groq
from surgical_config import (
    SURGICAL_PHASES, VITALS_NORMAL, AI_SYSTEM_PROMPT, SURGERY_TYPE,
    IMPLANT_OPTIONS, IMPLANT_SIZES, ASA_CLASSES, COMORBIDITIES
)
from surgical_engine import init_robot_state, init_vitals, update_vitals, update_robot, get_vitals_status
from surgical_visuals import render_robot_arm, render_knee_map
from surgical_report import generate_report

st.set_page_config(page_title="ARIA — Surgical Robot Assistant", page_icon="🏥", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
  html, body, [class*="css"] { background-color:#050a14!important; color:#c9d8f0!important; font-family:'JetBrains Mono',monospace!important; }
  .stApp { background-color:#050a14!important; }
  .block-container { padding-top:1rem!important; }
  h1,h2,h3 { color:#00d4ff!important; letter-spacing:1px; }
  [data-testid="stSidebar"] { background-color:#030810!important; border-right:1px solid #1e3a5f!important; }
  .stButton>button { background:#0a1526!important; color:#00d4ff!important; border:1px solid #00d4ff44!important; border-radius:4px!important; font-family:monospace!important; font-size:12px!important; }
  .stButton>button:hover { background:#00d4ff22!important; border-color:#00d4ff!important; }
  .stButton>button[kind="primary"] { background:linear-gradient(135deg,#00d4ff22,#00ff8822)!important; border:1px solid #00d4ff!important; color:#00d4ff!important; font-weight:bold!important; }
  [data-testid="stMetric"] { background:#0a1526!important; border:1px solid #1e3a5f!important; border-radius:6px!important; padding:8px!important; }
  [data-testid="stMetricValue"] { color:#00d4ff!important; font-size:1.2rem!important; }
  [data-testid="stMetricLabel"] { color:#5a7a9a!important; font-size:0.65rem!important; }
  .vital-card { background:#0a1526; border:1px solid #1e3a5f; border-radius:8px; padding:10px; margin:4px 0; }
  .vital-value { font-size:20px; font-weight:bold; font-family:monospace; }
  .vital-label { font-size:10px; color:#5a7a9a; font-family:monospace; }
  .alert-card { background:#1f0a0a; border:1px solid #ff4444; border-radius:6px; padding:8px 12px; margin:4px 0; font-size:12px; color:#ff8888; font-family:monospace; }
  .ai-card { background:#0a1f14; border:1px solid #00ff8844; border-radius:8px; padding:12px; margin:6px 0; font-size:12px; color:#a0e8c0; font-family:monospace; line-height:1.6; }
  .phase-card { background:#0a1526; border-left:3px solid #00d4ff; border-radius:4px; padding:8px 12px; margin:3px 0; font-size:11px; font-family:monospace; }
  .phase-card.active { background:#0a1f2e; border-color:#00ff88; color:#00ff88; }
  .phase-card.done { border-color:#3a5a3a; color:#5a7a5a; }
  .intake-section { background:#0a1526; border:1px solid #1e3a5f; border-radius:10px; padding:16px; margin:8px 0; }
  hr { border-color:#1e3a5f!important; }
  .stTextInput input,.stNumberInput input,.stTextArea textarea { background:#0a1526!important; border:1px solid #1e3a5f!important; color:#c9d8f0!important; font-family:monospace!important; }
  .stSelectbox label,.stSlider label,.stCheckbox label,.stMultiSelect label,.stRadio label { color:#5a7a9a!important; font-size:11px!important; }
  .stSelectbox>div>div { background:#0a1526!important; border:1px solid #1e3a5f!important; color:#c9d8f0!important; }
  .stMultiSelect>div>div { background:#0a1526!important; border:1px solid #1e3a5f!important; }
  .stProgress>div>div { background:#00d4ff!important; }
  [data-testid="stExpander"] { border:1px solid #1e3a5f!important; background:#0a1526!important; }
  .streamlit-expanderHeader { color:#00d4ff!important; font-family:monospace!important; }
  .stTabs [data-baseweb="tab"] { color:#5a7a9a!important; font-family:monospace!important; font-size:12px!important; }
  .stTabs [aria-selected="true"] { color:#00d4ff!important; border-bottom:2px solid #00d4ff!important; }
</style>
""", unsafe_allow_html=True)

# ── Secrets ───────────────────────────────────────────────────────────────────
default_key = st.secrets.get("GROQ_API_KEY", "")

# ── Session state ─────────────────────────────────────────────────────────────
def reset_session():
    st.session_state.robot_state   = init_robot_state()
    st.session_state.vitals        = init_vitals()
    st.session_state.running       = False
    st.session_state.ai_guidance   = "ARIA online. Complete patient intake to begin."
    st.session_state.procedure_log = []
    st.session_state.phase_idx     = 0
    st.session_state.step          = 0
    st.session_state.vitals_history= []
    st.session_state.surgeon_notes = {p["name"]: "" for p in SURGICAL_PHASES}
    st.session_state.complications = []
    st.session_state.procedure_started = False
    st.session_state.patient       = {}

for key in ["robot_state","vitals","running","ai_guidance","procedure_log",
            "phase_idx","step","vitals_history","surgeon_notes","complications",
            "procedure_started","patient"]:
    if key not in st.session_state:
        reset_session()
        break

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ SYSTEM CONFIG")
    api_key   = st.text_input("GROQ API KEY", value=default_key, type="password", placeholder="gsk_...")
    model     = st.selectbox("AI MODEL", ["llama-3.3-70b-versatile","llama-3.1-8b-instant"])
    sim_speed = st.slider("SIM SPEED (s/step)", 0.05, 0.5, 0.15)
    st.divider()

    st.markdown("### 📋 SURGICAL PHASES")
    current_phase = st.session_state.phase_idx
    for i, phase in enumerate(SURGICAL_PHASES):
        css  = "done" if i < current_phase else ("active" if i == current_phase else "")
        icon = "✅" if i < current_phase else ("▶" if i == current_phase else "○")
        st.markdown(
            f'<div class="phase-card {css}">{icon} {phase["icon"]} {phase["name"]}'
            f'<span style="float:right;color:#334e6e">{phase["risk"].upper()}</span></div>',
            unsafe_allow_html=True
        )
    st.divider()

    st.markdown("### 🔧 ROBOT CONTROLS")
    if st.button("🛑 EMERGENCY STOP", use_container_width=True):
        st.session_state.robot_state["emergency_stop"] = True
        st.session_state.running = False
        st.session_state.complications.append("Emergency stop activated")

    if st.button("🔄 RESET ALL", use_container_width=True):
        reset_session()
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🏥 ARIA — AUTONOMOUS ROBOTIC INTELLIGENCE ASSISTANT")
st.caption(f"Orthopedic Surgery Module · {SURGERY_TYPE} · Clinical Decision Support · Groq + Llama 3")
st.divider()

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 PATIENT INTAKE", "🦾 SURGICAL COCKPIT", "📊 REPORT"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Patient Intake
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### 👤 PATIENT INFORMATION")
    st.markdown('<div class="intake-section">', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        pt_id     = st.text_input("Patient ID",  value=st.session_state.patient.get("id","PT-2024-0001"), key="pt_id")
        pt_name   = st.text_input("Patient Name", value=st.session_state.patient.get("name",""), placeholder="Full name", key="pt_name")
        pt_age    = st.number_input("Age (years)", 18, 100, int(st.session_state.patient.get("age", 65)), key="pt_age")
    with c2:
        pt_weight = st.number_input("Weight (kg)", 40, 200, int(st.session_state.patient.get("weight", 75)), key="pt_weight")
        pt_height = st.number_input("Height (cm)", 140, 210, int(st.session_state.patient.get("height", 170)), key="pt_height")
        bmi       = round(pt_weight / ((pt_height/100)**2), 1)
        st.markdown(f'<div style="margin-top:8px"><span style="color:#5a7a9a;font-size:11px">CALCULATED BMI</span><br><span style="color:{"#ff4444" if bmi>30 else "#00d4ff"};font-size:20px;font-weight:bold">{bmi}</span></div>', unsafe_allow_html=True)
    with c3:
        pt_asa    = st.selectbox("ASA Physical Status", list(ASA_CLASSES.keys()), key="pt_asa")
        pt_anest  = st.selectbox("Anesthesia Type", ["General","Spinal","Epidural","Combined Spinal-Epidural"], key="pt_anest")
        pt_surgeon= st.text_input("Surgeon Name", value=st.session_state.patient.get("surgeon","Dr. "), key="pt_surgeon")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 🩺 COMORBIDITIES")
    st.markdown('<div class="intake-section">', unsafe_allow_html=True)
    selected_comorbidities = st.multiselect("Select all that apply", COMORBIDITIES,
        default=st.session_state.patient.get("comorbidities", []), key="pt_comorbidities")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 🔩 IMPLANT SELECTION")
    st.markdown('<div class="intake-section">', unsafe_allow_html=True)
    ic1, ic2 = st.columns(2)
    with ic1:
        implant      = st.selectbox("Implant System", IMPLANT_OPTIONS, key="pt_implant")
        implant_size = st.selectbox("Implant Size", IMPLANT_SIZES, index=1, key="pt_implant_size")
    with ic2:
        laterality   = st.radio("Laterality", ["Right Knee","Left Knee"], key="pt_laterality")
        fixation     = st.radio("Fixation Method", ["Cemented","Cementless","Hybrid"], key="pt_fixation")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### ⚙️ ROBOT SETTINGS")
    st.markdown('<div class="intake-section">', unsafe_allow_html=True)
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
        force_limit   = st.slider("Max Force Limit (N)", 10, 80, int(st.session_state.patient.get("force_limit",50)), key="force_limit")
    with rc2:
        speed_limit   = st.slider("Max Speed Limit (RPM)", 500, 5000, int(st.session_state.patient.get("speed_limit",3500)), key="speed_limit")
    with rc3:
        tremor_filter = st.checkbox("Tremor Compensation Active", value=True, key="tremor_filter")
        haptic        = st.checkbox("Haptic Force Feedback", value=True, key="haptic")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### 📝 PRE-OP NOTES")
    preop_notes = st.text_area("Surgeon pre-operative notes", height=80,
        placeholder="Any pre-operative observations, concerns, or special instructions…",
        value=st.session_state.patient.get("preop_notes",""), key="preop_notes")

    st.divider()
    if st.button("✅ CONFIRM PATIENT & PROCEED TO SURGERY", type="primary", use_container_width=True):
        st.session_state.patient = {
            "id": pt_id, "name": pt_name, "age": pt_age,
            "weight": pt_weight, "height": pt_height, "bmi": bmi,
            "asa": pt_asa, "anesthesia": pt_anest, "surgeon": pt_surgeon,
            "comorbidities": selected_comorbidities,
            "implant": implant, "implant_size": implant_size,
            "laterality": laterality, "fixation": fixation,
            "force_limit": force_limit, "speed_limit": speed_limit,
            "tremor_filter": tremor_filter, "haptic": haptic,
            "preop_notes": preop_notes,
        }
        st.session_state.procedure_started = True
        # Adjust vitals baseline for comorbidities
        v = st.session_state.vitals
        if "Hypertension" in selected_comorbidities:
            v["bp_sys"] = random.randint(135, 150)
            v["bp_dia"] = random.randint(85, 95)
        if "Diabetes Mellitus" in selected_comorbidities:
            v["heart_rate"] = random.randint(78, 92)
        st.session_state.vitals = v
        st.success("✅ Patient intake complete. Switch to SURGICAL COCKPIT tab to begin.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Surgical Cockpit
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.procedure_started:
        st.warning("⚠️ Complete patient intake in the PATIENT INTAKE tab first.")
    else:
        patient = st.session_state.patient

        # ── Vitals row ────────────────────────────────────────────────────────
        st.markdown("### 📊 LIVE PATIENT VITALS")

        # Manual vital overrides
        with st.expander("🩺 Manual Vital Override (enter real readings)"):
            ov1, ov2, ov3, ov4, ov5 = st.columns(5)
            with ov1:
                override_hr  = st.number_input("Heart Rate (bpm)", 30, 180, st.session_state.vitals["heart_rate"], key="ov_hr")
            with ov2:
                override_sys = st.number_input("BP Systolic",       60, 220, st.session_state.vitals["bp_sys"], key="ov_sys")
                override_dia = st.number_input("BP Diastolic",       40, 130, st.session_state.vitals["bp_dia"], key="ov_dia")
            with ov3:
                override_spo2= st.number_input("SpO₂ (%)",          70, 100, st.session_state.vitals["spo2"], key="ov_spo2")
            with ov4:
                override_temp= st.number_input("Temp (°C)",         34.0, 41.0, float(st.session_state.vitals["temperature"]), step=0.1, key="ov_temp")
            with ov5:
                override_rr  = st.number_input("Resp Rate",           6,  40, st.session_state.vitals["resp_rate"], key="ov_rr")

            if st.button("📥 APPLY READINGS", use_container_width=True):
                st.session_state.vitals.update({
                    "heart_rate": override_hr, "bp_sys": override_sys,
                    "bp_dia": override_dia,    "spo2": override_spo2,
                    "temperature": override_temp, "resp_rate": override_rr,
                })
                st.success("Vitals updated.")

        vitals_ph = st.empty()

        def render_vitals_ui(vitals):
            def vc(val, lo, hi):
                return "#00ff88" if lo<=val<=hi else ("#ffd700" if (val<lo*0.95 or val>hi*1.05) else "#ff4444")
            v = vitals
            cols = st.columns(5)
            with cols[0]:
                st.markdown(f'<div class="vital-card"><div class="vital-label">❤️ HEART RATE</div><div class="vital-value" style="color:{vc(v["heart_rate"],60,90)}">{v["heart_rate"]}</div><div class="vital-label">bpm</div></div>', unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f'<div class="vital-card"><div class="vital-label">🩺 BLOOD PRESSURE</div><div class="vital-value" style="color:{vc(v["bp_sys"],110,130)}">{v["bp_sys"]}/{v["bp_dia"]}</div><div class="vital-label">mmHg</div></div>', unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f'<div class="vital-card"><div class="vital-label">🫁 SpO₂</div><div class="vital-value" style="color:{vc(v["spo2"],96,100)}">{v["spo2"]}%</div><div class="vital-label">oxygen sat</div></div>', unsafe_allow_html=True)
            with cols[3]:
                st.markdown(f'<div class="vital-card"><div class="vital-label">🌡️ TEMPERATURE</div><div class="vital-value" style="color:{vc(v["temperature"],36.0,37.2)}">{v["temperature"]}°C</div><div class="vital-label">core temp</div></div>', unsafe_allow_html=True)
            with cols[4]:
                st.markdown(f'<div class="vital-card"><div class="vital-label">💨 RESP RATE</div><div class="vital-value" style="color:{vc(v["resp_rate"],12,18)}">{v["resp_rate"]}</div><div class="vital-label">breaths/min</div></div>', unsafe_allow_html=True)

        with vitals_ph.container():
            render_vitals_ui(st.session_state.vitals)

        alerts_ph = st.empty()

        # ── AI Guidance ───────────────────────────────────────────────────────
        st.markdown("### 🧠 ARIA — AI SURGICAL GUIDANCE")
        ai_ph = st.empty()
        ai_ph.markdown(f'<div class="ai-card">💬 {st.session_state.ai_guidance}</div>', unsafe_allow_html=True)

        st.divider()

        # ── Main visuals ──────────────────────────────────────────────────────
        st.markdown("### 🦾 SURGICAL COCKPIT")
        arm_col, knee_col = st.columns([1, 1])
        arm_ph  = arm_col.empty()
        knee_ph = knee_col.empty()

        arm_ph.markdown(render_robot_arm(st.session_state.robot_state),  unsafe_allow_html=True)
        knee_ph.markdown(render_knee_map(st.session_state.robot_state), unsafe_allow_html=True)

        st.divider()

        # ── Controls + Log ────────────────────────────────────────────────────
        ctrl_col, log_col = st.columns([1, 2])
        with ctrl_col:
            st.markdown("### ▶ PROCEDURE CONTROL")
            if not api_key:
                st.warning("⚠️ Add Groq API key in sidebar")

            start_btn = st.button("▶ BEGIN PROCEDURE", type="primary", use_container_width=True,
                                  disabled=st.session_state.running or not api_key)
            step_btn  = st.button("⏭ STEP FORWARD",  use_container_width=True,
                                  disabled=st.session_state.running)

            st.divider()
            st.markdown("### 📝 INTRAOP NOTE")
            current_phase_name = SURGICAL_PHASES[min(st.session_state.phase_idx, len(SURGICAL_PHASES)-1)]["name"]
            note_input = st.text_area("Note for current phase", height=70,
                placeholder="Observations, findings, deviations…", key="note_input")
            if st.button("💾 SAVE NOTE", use_container_width=True):
                st.session_state.surgeon_notes[current_phase_name] = note_input
                st.success("Note saved.")

            st.divider()
            st.markdown("### ⚠️ COMPLICATIONS")
            comp_input = st.text_input("Flag a complication", placeholder="e.g. minor bleeding", key="comp_input")
            if st.button("🚩 FLAG", use_container_width=True):
                if comp_input:
                    st.session_state.complications.append(f"[Phase: {current_phase_name}] {comp_input}")
                    st.success("Flagged.")

            st.divider()
            st.markdown("### 📈 ROBOT METRICS")
            rs = st.session_state.robot_state
            m1, m2 = st.columns(2)
            m1.metric("Precision",       f"{rs['precision_score']:.1f}%")
            m2.metric("Force",           f"{rs['force_applied']}N")
            m3, m4 = st.columns(2)
            m3.metric("Tremor (raw)",    f"{rs['tremor_raw']} mm")
            m4.metric("Tremor (filt)",   f"{rs['tremor_filtered']} mm")

        with log_col:
            st.markdown("### 📋 PROCEDURE LOG")
            log_ph = st.empty()

            def render_log():
                log_html = ""
                for entry in st.session_state.procedure_log[-10:]:
                    log_html += f'<div class="phase-card">[{entry["step"]:03d}] <b>{entry["phase"]}</b> — {entry["event"]}</div>'
                if not log_html:
                    log_html = '<div class="phase-card" style="color:#334e6e">Awaiting procedure start…</div>'
                log_ph.markdown(log_html, unsafe_allow_html=True)

            render_log()

        prog_ph = st.progress(0, text="Ready to begin procedure")

        # ── AI Guidance helper ────────────────────────────────────────────────
        def get_ai_guidance(api_key, robot_state, vitals, phase_idx, patient):
            if not api_key:
                return "⚠️ API key required."
            try:
                client = Groq(api_key=api_key)
                phase  = SURGICAL_PHASES[phase_idx]
                alerts = get_vitals_status(vitals) + robot_state.get("alerts", [])
                comorbid = ", ".join(patient.get("comorbidities", [])) or "None"
                prompt = AI_SYSTEM_PROMPT.format(
                    patient_profile=f'Age:{patient.get("age")} BMI:{patient.get("bmi")} ASA:{patient.get("asa","I")[:5]} Comorbidities:{comorbid}',
                    phase=f'{phase["icon"]} {phase["name"]} (Risk:{phase["risk"]})',
                    robot_status=f'Tool:{robot_state["tool"]} Force:{robot_state["force_applied"]}N Precision:{robot_state["precision_score"]:.1f}% CollisionRisk:{robot_state["collision_risk"]:.0%}',
                    vitals=f'HR:{vitals["heart_rate"]}bpm BP:{vitals["bp_sys"]}/{vitals["bp_dia"]} SpO2:{vitals["spo2"]}% Temp:{vitals["temperature"]}°C',
                    alerts="; ".join(alerts) if alerts else "None",
                    force_limit=patient.get("force_limit", 50),
                    speed_limit=patient.get("speed_limit", 3500),
                )
                resp = client.chat.completions.create(
                    model=model, max_tokens=120,
                    messages=[{"role":"user","content":prompt}],
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                return f"ARIA guidance unavailable: {str(e)[:60]}"

        # ── Step function ─────────────────────────────────────────────────────
        def run_step(api_key, get_ai=False):
            rs         = st.session_state.robot_state
            vitals     = st.session_state.vitals
            phase_idx  = st.session_state.phase_idx
            step       = st.session_state.step
            patient    = st.session_state.patient

            if phase_idx >= len(SURGICAL_PHASES):
                return False

            phase = SURGICAL_PHASES[phase_idx]
            rs["phase_idx"] = phase_idx
            rs = update_robot(rs, phase_idx, step)
            vitals = update_vitals(vitals, phase_idx, rs["emergency_stop"])

            # Force/speed limit check
            if rs["force_applied"] > patient.get("force_limit", 50):
                rs["alerts"].append(f"🚨 Force {rs['force_applied']}N exceeds limit {patient['force_limit']}N!")
                if patient.get("force_limit", 50) not in [c for c in st.session_state.complications]:
                    st.session_state.complications.append(f"[{phase['name']}] Force exceeded limit")

            event = f'{phase["icon"]} {phase["name"]} | Tool:{rs["tool"]} | Force:{rs["force_applied"]}N | Precision:{rs["precision_score"]:.1f}%'
            st.session_state.procedure_log.append({"step":step,"phase":phase["name"],"event":event})
            st.session_state.vitals_history.append(dict(vitals))

            steps_in_phase = phase["duration"]
            if (step+1) % steps_in_phase == 0 and phase_idx < len(SURGICAL_PHASES)-1:
                st.session_state.phase_idx += 1

            st.session_state.robot_state = rs
            st.session_state.vitals      = vitals
            st.session_state.step       += 1

            if get_ai and step % 5 == 0:
                st.session_state.ai_guidance = get_ai_guidance(api_key, rs, vitals, phase_idx, patient)
            return True

        def refresh_ui():
            rs     = st.session_state.robot_state
            vitals = st.session_state.vitals
            with vitals_ph.container():
                render_vitals_ui(vitals)
            all_alerts = get_vitals_status(vitals) + rs.get("alerts", [])
            if all_alerts:
                alerts_ph.markdown("".join([f'<div class="alert-card">{a}</div>' for a in all_alerts]), unsafe_allow_html=True)
            else:
                alerts_ph.empty()
            ai_ph.markdown(f'<div class="ai-card">💬 {st.session_state.ai_guidance}</div>', unsafe_allow_html=True)
            arm_ph.markdown(render_robot_arm(rs),  unsafe_allow_html=True)
            knee_ph.markdown(render_knee_map(rs), unsafe_allow_html=True)
            render_log()
            total_steps = sum(p["duration"] for p in SURGICAL_PHASES)
            pct   = min(1.0, st.session_state.step / total_steps)
            phase = SURGICAL_PHASES[min(st.session_state.phase_idx, len(SURGICAL_PHASES)-1)]
            prog_ph.progress(pct, text=f'Phase {st.session_state.phase_idx+1}/{len(SURGICAL_PHASES)}: {phase["icon"]} {phase["name"]}')
            m1.metric("Precision",    f"{rs['precision_score']:.1f}%")
            m2.metric("Force",        f"{rs['force_applied']}N")
            m3.metric("Tremor (raw)", f"{rs['tremor_raw']} mm")
            m4.metric("Tremor (filt)",f"{rs['tremor_filtered']} mm")

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
                run_step(api_key, get_ai=(i%6==0))
                refresh_ui()
                time.sleep(sim_speed)
            st.session_state.running = False
            if not st.session_state.robot_state.get("emergency_stop"):
                st.balloons()
                st.success("✅ PROCEDURE COMPLETE — Total Knee Replacement successful")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Report
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📊 PROCEDURE REPORT")
    if not st.session_state.patient:
        st.info("Complete patient intake and run the procedure to generate a report.")
    else:
        patient = st.session_state.patient

        # Patient summary
        st.markdown("#### 👤 Patient Summary")
        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.metric("Patient",   patient.get("name","N/A"))
        rc2.metric("Age / BMI", f'{patient.get("age","N/A")} / {patient.get("bmi","N/A")}')
        rc3.metric("ASA Class", patient.get("asa","N/A")[:6])
        rc4.metric("Implant",   patient.get("implant","N/A")[:20])

        st.divider()

        # Comorbidities
        if patient.get("comorbidities"):
            st.markdown("#### 🩺 Comorbidities")
            st.markdown(", ".join([f"`{c}`" for c in patient["comorbidities"]]))

        # Complications
        st.markdown("#### ⚠️ Intraoperative Complications")
        if st.session_state.complications:
            for c in st.session_state.complications:
                st.markdown(f'<div class="alert-card">⚠️ {c}</div>', unsafe_allow_html=True)
        else:
            st.success("No complications recorded.")

        # Surgeon notes
        st.markdown("#### 📝 Surgeon Notes by Phase")
        for phase_name, note in st.session_state.surgeon_notes.items():
            if note.strip():
                with st.expander(f"📋 {phase_name}"):
                    st.write(note)

        # Robot performance
        st.markdown("#### 🦾 Robot Performance")
        rs = st.session_state.robot_state
        p1,p2,p3,p4 = st.columns(4)
        p1.metric("Final Precision",  f"{rs['precision_score']:.1f}%")
        p2.metric("Total Steps",      rs.get("total_steps",0))
        p3.metric("Phases Done",      f"{min(st.session_state.phase_idx, len(SURGICAL_PHASES))}/{len(SURGICAL_PHASES)}")
        p4.metric("E-Stop Triggered", "YES" if rs.get("emergency_stop") else "NO")

        st.divider()

        # Download report
        st.markdown("#### 💾 DOWNLOAD PROCEDURE REPORT")
        report_text = generate_report(
            patient               = patient,
            vitals_history        = st.session_state.vitals_history,
            procedure_log         = st.session_state.procedure_log,
            robot_state           = st.session_state.robot_state,
            phase_idx             = st.session_state.phase_idx,
            surgeon_notes         = st.session_state.surgeon_notes,
            complications         = st.session_state.complications,
        )
        st.download_button(
            label     = "📥 DOWNLOAD REPORT (.txt)",
            data      = report_text,
            file_name = f'ARIA_Report_{patient.get("id","PT")}_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.txt',
            mime      = "text/plain",
            use_container_width=True,
        )

        with st.expander("👁 Preview Report"):
            st.code(report_text, language=None)
