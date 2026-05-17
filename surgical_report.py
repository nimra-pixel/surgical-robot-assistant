# surgical_report.py — PDF report generator

import io
import datetime

def generate_report(patient, vitals_history, procedure_log, robot_state, phase_idx, surgeon_notes, complications):
    """Generate a clinical procedure report as text (downloadable as .txt)."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []

    lines.append("=" * 65)
    lines.append("        ARIA SURGICAL ROBOT — PROCEDURE REPORT")
    lines.append("=" * 65)
    lines.append(f"  Generated: {now}")
    lines.append(f"  Procedure: Total Knee Replacement (TKR) — Right Knee")
    lines.append("")

    # Patient info
    lines.append("-" * 65)
    lines.append("  PATIENT INFORMATION")
    lines.append("-" * 65)
    lines.append(f"  Patient ID  : {patient.get('id', 'N/A')}")
    lines.append(f"  Name        : {patient.get('name', 'N/A')}")
    lines.append(f"  Age         : {patient.get('age', 'N/A')} years")
    lines.append(f"  Weight      : {patient.get('weight', 'N/A')} kg")
    lines.append(f"  BMI         : {patient.get('bmi', 'N/A')}")
    lines.append(f"  ASA Class   : {patient.get('asa', 'N/A')}")
    lines.append(f"  Surgeon     : {patient.get('surgeon', 'N/A')}")
    lines.append(f"  Implant     : {patient.get('implant', 'N/A')} — Size {patient.get('implant_size', 'N/A')}")
    lines.append(f"  Comorbidities: {', '.join(patient.get('comorbidities', [])) or 'None'}")
    lines.append(f"  Anesthesia  : {patient.get('anesthesia', 'General')}")
    lines.append("")

    # Surgical settings
    lines.append("-" * 65)
    lines.append("  ROBOT SETTINGS")
    lines.append("-" * 65)
    lines.append(f"  Max Force    : {patient.get('force_limit', 50)} N")
    lines.append(f"  Max Speed    : {patient.get('speed_limit', 3500)} RPM")
    lines.append(f"  Tremor Filter: {'Active' if patient.get('tremor_filter', True) else 'Inactive'}")
    lines.append("")

    # Procedure summary
    lines.append("-" * 65)
    lines.append("  PROCEDURE SUMMARY")
    lines.append("-" * 65)
    lines.append(f"  Phases completed : {phase_idx + 1} / 7")
    lines.append(f"  Total steps      : {robot_state.get('total_steps', 0)}")
    lines.append(f"  Final precision  : {robot_state.get('precision_score', 0):.1f}%")
    lines.append(f"  Max force applied: {robot_state.get('force_applied', 0)} N")
    lines.append(f"  Tremor (raw/filt): {robot_state.get('tremor_raw', 0)} / {robot_state.get('tremor_filtered', 0)} mm")
    lines.append(f"  Emergency stops  : {'YES — procedure halted' if robot_state.get('emergency_stop') else 'None'}")
    lines.append("")

    # Vitals summary
    if vitals_history:
        lines.append("-" * 65)
        lines.append("  VITALS SUMMARY (Final Reading)")
        lines.append("-" * 65)
        v = vitals_history[-1]
        lines.append(f"  Heart Rate  : {v.get('heart_rate', '--')} bpm")
        lines.append(f"  Blood Press.: {v.get('bp_sys', '--')}/{v.get('bp_dia', '--')} mmHg")
        lines.append(f"  SpO2        : {v.get('spo2', '--')}%")
        lines.append(f"  Temperature : {v.get('temperature', '--')} °C")
        lines.append(f"  Resp. Rate  : {v.get('resp_rate', '--')} breaths/min")
        lines.append("")

    # Complications
    lines.append("-" * 65)
    lines.append("  INTRAOPERATIVE COMPLICATIONS")
    lines.append("-" * 65)
    if complications:
        for c in complications:
            lines.append(f"  ⚠ {c}")
    else:
        lines.append("  None reported")
    lines.append("")

    # Surgeon notes
    lines.append("-" * 65)
    lines.append("  SURGEON NOTES")
    lines.append("-" * 65)
    for i, (phase, note) in enumerate(surgeon_notes.items()):
        if note.strip():
            lines.append(f"  [{phase}]")
            lines.append(f"  {note}")
            lines.append("")
    if not any(n.strip() for n in surgeon_notes.values()):
        lines.append("  No notes recorded")
    lines.append("")

    # Procedure log excerpt
    lines.append("-" * 65)
    lines.append("  PROCEDURE LOG (Last 20 entries)")
    lines.append("-" * 65)
    for entry in procedure_log[-20:]:
        lines.append(f"  [{entry['step']:03d}] {entry['phase']:20s} | {entry['event'][:55]}")
    lines.append("")
    lines.append("=" * 65)
    lines.append("  END OF REPORT — ARIA Surgical Robot Assistant v2.0")
    lines.append("=" * 65)

    return "\n".join(lines)
