# surgical_config.py — Configuration for Orthopedic Surgical Robot Assistant

SURGERY_TYPE = "Total Knee Replacement (TKR)"

SURGICAL_PHASES = [
    {"id": 0, "name": "Preparation",      "icon": "🔧", "duration": 5,  "risk": "low"},
    {"id": 1, "name": "Incision",          "icon": "🔪", "duration": 8,  "risk": "medium"},
    {"id": 2, "name": "Bone Resection",    "icon": "🦴", "duration": 12, "risk": "high"},
    {"id": 3, "name": "Implant Alignment", "icon": "🎯", "duration": 10, "risk": "high"},
    {"id": 4, "name": "Implant Fixation",  "icon": "🔩", "duration": 8,  "risk": "medium"},
    {"id": 5, "name": "Irrigation",        "icon": "💧", "duration": 5,  "risk": "low"},
    {"id": 6, "name": "Closure",           "icon": "🩹", "duration": 6,  "risk": "low"},
]

ARM_JOINTS = ["Base", "Shoulder", "Elbow", "Wrist", "End Effector"]

KNEE_ZONES = {
    "femur":        {"label": "Femur",           "risk": "medium"},
    "tibia":        {"label": "Tibia",           "risk": "medium"},
    "patella":      {"label": "Patella",         "risk": "low"},
    "cartilage":    {"label": "Cartilage",       "risk": "high"},
    "meniscus":     {"label": "Meniscus",        "risk": "high"},
    "ligament_acl": {"label": "ACL",             "risk": "critical"},
    "ligament_pcl": {"label": "PCL",             "risk": "critical"},
    "nerve":        {"label": "Peroneal Nerve",  "risk": "critical"},
    "vessel":       {"label": "Popliteal Art.",  "risk": "critical"},
    "implant":      {"label": "Implant Zone",    "risk": "low"},
}

VITALS_NORMAL = {
    "heart_rate":  (60, 90),
    "bp_sys":      (110, 130),
    "bp_dia":      (70, 85),
    "spo2":        (96, 100),
    "temperature": (36.0, 37.2),
    "resp_rate":   (12, 18),
}

IMPLANT_OPTIONS = [
    "Zimmer Biomet NexGen",
    "Stryker Triathlon",
    "DePuy Synthes Attune",
    "Smith+Nephew Journey II",
    "Exactech Vanguard",
]

IMPLANT_SIZES = ["Small (1)", "Medium (2)", "Medium-Large (3)", "Large (4)", "X-Large (5)"]

ASA_CLASSES = {
    "ASA I — Healthy patient": 1,
    "ASA II — Mild systemic disease": 2,
    "ASA III — Severe systemic disease": 3,
    "ASA IV — Life-threatening disease": 4,
}

COMORBIDITIES = [
    "Diabetes Mellitus",
    "Hypertension",
    "Osteoporosis",
    "Obesity (BMI>30)",
    "Coronary Artery Disease",
    "COPD",
    "Anticoagulation Therapy",
    "Previous Knee Surgery",
]

AI_SYSTEM_PROMPT = """You are ARIA (Autonomous Robotic Intelligence Assistant), an AI surgical assistant 
specializing in orthopedic procedures, specifically Total Knee Replacement (TKR).

Patient profile: {patient_profile}
Current surgical phase: {phase}
Robot status: {robot_status}
Patient vitals: {vitals}
Active alerts: {alerts}
Surgeon force limit: {force_limit}N | Speed limit: {speed_limit} RPM

Respond in 2-3 sentences max. Be clinical, precise, and actionable.
Focus on: safety warnings, technique guidance, or next steps.
Consider the patient's comorbidities when relevant. Never say you're an AI."""
