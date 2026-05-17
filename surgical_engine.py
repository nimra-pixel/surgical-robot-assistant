# surgical_engine.py — Simulation engine for surgical robot

import random
import math
from surgical_config import VITALS_NORMAL, SURGICAL_PHASES

def init_robot_state():
    return {
        "joints": {"Base": 0.0, "Shoulder": 0.0, "Elbow": 90.0, "Wrist": 0.0, "End Effector": 0.0},
        "position": (300, 300),  # SVG canvas position
        "tool": "Drill",
        "tool_speed": 0,
        "tremor_raw": 0.0,
        "tremor_filtered": 0.0,
        "precision_score": 100.0,
        "force_applied": 0.0,
        "emergency_stop": False,
        "collision_risk": 0.0,
        "operating": False,
        "phase_idx": 0,
        "phase_step": 0,
        "procedure_log": [],
        "total_steps": 0,
        "alerts": [],
    }

def init_vitals():
    return {
        "heart_rate":  75,
        "bp_sys":      120,
        "bp_dia":      78,
        "spo2":        98,
        "temperature": 36.6,
        "resp_rate":   14,
        "anesthesia":  95,
    }

def update_vitals(vitals, phase_idx, emergency=False):
    """Simulate realistic vital sign changes during surgery."""
    hr_min, hr_max = VITALS_NORMAL["heart_rate"]
    phase_stress = [0, 5, 15, 12, 8, 3, 2][phase_idx] if phase_idx < 7 else 0

    if emergency:
        phase_stress += 25

    vitals["heart_rate"]  = max(50, min(130, vitals["heart_rate"]  + random.randint(-2, 3) + (1 if phase_stress > 10 else 0)))
    vitals["bp_sys"]      = max(90, min(160, vitals["bp_sys"]      + random.randint(-3, 3) + (2 if phase_stress > 10 else 0)))
    vitals["bp_dia"]      = max(60, min(100, vitals["bp_dia"]      + random.randint(-2, 2)))
    vitals["spo2"]        = max(88, min(100, vitals["spo2"]        + random.randint(-1, 1)))
    vitals["temperature"] = round(max(35.5, min(38.5, vitals["temperature"] + random.uniform(-0.05, 0.05))), 1)
    vitals["resp_rate"]   = max(10, min(24,  vitals["resp_rate"]   + random.randint(-1, 1)))
    vitals["anesthesia"]  = max(80, min(100, vitals["anesthesia"]  + random.randint(-1, 1)))
    return vitals

def get_vitals_status(vitals):
    """Return alert level for each vital."""
    alerts = []
    if vitals["heart_rate"] > 100 or vitals["heart_rate"] < 55:
        alerts.append(f"⚠️ HR {vitals['heart_rate']} bpm — outside normal range")
    if vitals["bp_sys"] > 145 or vitals["bp_sys"] < 95:
        alerts.append(f"⚠️ BP {vitals['bp_sys']}/{vitals['bp_dia']} mmHg — abnormal")
    if vitals["spo2"] < 94:
        alerts.append(f"🚨 SpO₂ {vitals['spo2']}% — CRITICAL LOW")
    if vitals["temperature"] > 38.0:
        alerts.append(f"⚠️ Temp {vitals['temperature']}°C — elevated")
    return alerts

def update_robot(state, phase_idx, step):
    """Update robot arm joints and metrics per step."""
    phase = SURGICAL_PHASES[phase_idx]
    t = step * 0.15

    # Phase-specific joint targets
    phase_joints = {
        0: {"Base": 0,   "Shoulder": 20,  "Elbow": 80,  "Wrist": 10,  "End Effector": 0},
        1: {"Base": 15,  "Shoulder": 35,  "Elbow": 70,  "Wrist": 20,  "End Effector": 30},
        2: {"Base": 30,  "Shoulder": 50,  "Elbow": 60,  "Wrist": 35,  "End Effector": 60},
        3: {"Base": 20,  "Shoulder": 40,  "Elbow": 65,  "Wrist": 25,  "End Effector": 45},
        4: {"Base": 25,  "Shoulder": 45,  "Elbow": 62,  "Wrist": 30,  "End Effector": 50},
        5: {"Base": 10,  "Shoulder": 30,  "Elbow": 75,  "Wrist": 15,  "End Effector": 20},
        6: {"Base": 5,   "Shoulder": 25,  "Elbow": 82,  "Wrist": 8,   "End Effector": 10},
    }

    targets = phase_joints.get(phase_idx, phase_joints[0])
    for joint, target in targets.items():
        current = state["joints"][joint]
        state["joints"][joint] = round(current + (target - current) * 0.12 + math.sin(t) * 0.5, 2)

    # Tremor simulation + filtering
    raw_tremor = random.uniform(0, 3.5) if phase["risk"] == "high" else random.uniform(0, 1.5)
    filtered = raw_tremor * 0.08  # tremor compensation
    state["tremor_raw"] = round(raw_tremor, 2)
    state["tremor_filtered"] = round(filtered, 2)

    # Precision score
    tremor_penalty = raw_tremor * 2
    state["precision_score"] = round(max(85, min(100, state["precision_score"] - tremor_penalty * 0.01 + 0.05)), 1)

    # Force applied
    force_map = {0: 2, 1: 8, 2: 45, 3: 25, 4: 35, 5: 5, 6: 4}
    base_force = force_map.get(phase_idx, 5)
    state["force_applied"] = round(base_force + random.uniform(-2, 2), 1)

    # Tool
    tool_map = {0: "Probe", 1: "Scalpel", 2: "Oscillating Saw", 3: "Alignment Guide", 4: "Impactor", 5: "Irrigator", 6: "Suture"}
    state["tool"] = tool_map.get(phase_idx, "Probe")
    state["tool_speed"] = {0: 0, 1: 20, 2: 3200, 3: 0, 4: 0, 5: 150, 6: 0}.get(phase_idx, 0)

    # Collision risk
    high_risk_phases = [2, 3]
    state["collision_risk"] = round(
        random.uniform(0.15, 0.45) if phase_idx in high_risk_phases else random.uniform(0.02, 0.15), 2
    )

    # Alerts
    state["alerts"] = []
    if state["collision_risk"] > 0.35:
        state["alerts"].append("⚠️ High collision risk — reduce speed")
    if state["tremor_raw"] > 2.5:
        state["alerts"].append("⚠️ Tremor spike detected — tremor filter active")
    if state["force_applied"] > 50:
        state["alerts"].append("🚨 Excessive force — ease pressure")
    if state["emergency_stop"]:
        state["alerts"].append("🛑 EMERGENCY STOP ACTIVATED")

    state["total_steps"] += 1
    return state

def get_arm_svg_path(joints):
    """Compute 2D projected arm positions from joint angles."""
    L = [0, 80, 70, 55, 40, 25]  # segment lengths
    angles = [
        0,
        math.radians(joints["Base"] - 90),
        math.radians(joints["Shoulder"] - 90),
        math.radians(joints["Elbow"] - 90),
        math.radians(joints["Wrist"] - 90),
        math.radians(joints["End Effector"] - 90),
    ]

    cx, cy = 160, 60  # base position on SVG
    points = [(cx, cy)]
    cumulative_angle = -math.pi / 2

    for i in range(1, len(L)):
        cumulative_angle += angles[i]
        nx = points[-1][0] + L[i] * math.cos(cumulative_angle)
        ny = points[-1][1] + L[i] * math.sin(cumulative_angle)
        points.append((nx, ny))

    return points
