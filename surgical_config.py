# surgical_config.py — Configuration for Orthopedic Surgical Robot Assistant

SURGERY_TYPE = "Total Knee Replacement (TKR)"

# Surgical phases in order
SURGICAL_PHASES = [
    {"id": 0, "name": "Preparation",       "icon": "🔧", "duration": 5,  "risk": "low"},
    {"id": 1, "name": "Incision",           "icon": "🔪", "duration": 8,  "risk": "medium"},
    {"id": 2, "name": "Bone Resection",     "icon": "🦴", "duration": 12, "risk": "high"},
    {"id": 3, "name": "Implant Alignment",  "icon": "🎯", "duration": 10, "risk": "high"},
    {"id": 4, "name": "Implant Fixation",   "icon": "🔩", "duration": 8,  "risk": "medium"},
    {"id": 5, "name": "Irrigation",         "icon": "💧", "duration": 5,  "risk": "low"},
    {"id": 6, "name": "Closure",            "icon": "🩹", "duration": 6,  "risk": "low"},
]

# Robotic arm joints (degrees of freedom)
ARM_JOINTS = ["Base", "Shoulder", "Elbow", "Wrist", "End Effector"]

# Organ/tissue zones on the knee map
KNEE_ZONES = {
    "femur":        {"label": "Femur",          "color": "#e8d5b0", "risk": "medium"},
    "tibia":        {"label": "Tibia",          "color": "#e8d5b0", "risk": "medium"},
    "patella":      {"label": "Patella",        "color": "#d4c49a", "risk": "low"},
    "cartilage":    {"label": "Cartilage",      "color": "#a8d8a8", "risk": "high"},
    "meniscus":     {"label": "Meniscus",       "color": "#90c9a0", "risk": "high"},
    "ligament_acl": {"label": "ACL",            "color": "#ff9999", "risk": "critical"},
    "ligament_pcl": {"label": "PCL",            "color": "#ff9999", "risk": "critical"},
    "nerve":        {"label": "Peroneal Nerve", "color": "#ffb366", "risk": "critical"},
    "vessel":       {"label": "Popliteal Artery","color": "#ff6666","risk": "critical"},
    "implant":      {"label": "Implant Zone",   "color": "#a0c4ff", "risk": "low"},
}

# Vitals normal ranges
VITALS_NORMAL = {
    "heart_rate":  (60, 90),
    "bp_sys":      (110, 130),
    "bp_dia":      (70, 85),
    "spo2":        (96, 100),
    "temperature": (36.0, 37.2),
    "resp_rate":   (12, 18),
}

AI_SYSTEM_PROMPT = """You are ARIA (Autonomous Robotic Intelligence Assistant), an AI surgical assistant 
specializing in orthopedic procedures, specifically Total Knee Replacement (TKR).

Your role is to provide precise, concise real-time guidance to the surgical team.
Current surgical phase: {phase}
Robot status: {robot_status}
Patient vitals: {vitals}
Active alerts: {alerts}

Respond in 2-3 sentences max. Be clinical, precise, and actionable.
Focus on: safety warnings, technique guidance, or next steps.
Never say you're an AI. Speak as a surgical assistant."""
