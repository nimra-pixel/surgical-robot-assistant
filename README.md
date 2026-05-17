# 🏥 ARIA — Autonomous Robotic Intelligence Assistant

An AI-powered orthopedic surgical robot simulator featuring:

- 🦾 **5-DOF Robotic Arm** — live joint angle simulation with tremor filtering
- 🦴 **Knee Joint Map** — anatomical SVG with active zone highlighting
- 🧠 **ARIA AI Guidance** — real-time surgical instructions via Groq + Llama 3
- 📊 **Live Patient Vitals** — HR, BP, SpO₂, temperature, respiratory rate
- ⚠️ **Alert System** — collision risk, tremor spikes, vital anomalies
- 🛑 **Emergency Stop** — instant halt with visual indicator
- 📋 **Procedure Log** — full step-by-step surgical record
- 7 surgical phases: Preparation → Incision → Bone Resection → Alignment → Fixation → Irrigation → Closure

## Quick Start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
```bash
git init && git add . && git commit -m "ARIA surgical robot"
git remote add origin https://github.com/nimra-pixel/surgical-robot-assistant.git
git push -u origin main
```
Streamlit secrets: `GROQ_API_KEY = "gsk_..."`
