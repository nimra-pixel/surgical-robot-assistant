# surgical_visuals.py — SVG renderers for robot arm and knee map

import math
from surgical_engine import get_arm_svg_path
from surgical_config import SURGICAL_PHASES

def render_robot_arm(state):
    """Render robotic arm as SVG."""
    joints = state["joints"]
    points = get_arm_svg_path(joints)
    phase_idx = state["phase_idx"]
    phase = SURGICAL_PHASES[phase_idx]
    collision_risk = state["collision_risk"]
    emergency = state["emergency_stop"]

    arm_color = "#ff4444" if emergency else ("#ffaa00" if collision_risk > 0.35 else "#00d4ff")
    end_color = "#ff4444" if emergency else "#00ff88"

    W, H = 320, 420

    lines = [
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;background:#060c1a;border-radius:12px;border:1px solid #1e3a5f;">',
        f'<defs>'
        f'<radialGradient id="armglow" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0%" stop-color="{arm_color}" stop-opacity="0.2"/>'
        f'<stop offset="100%" stop-color="{arm_color}" stop-opacity="0"/>'
        f'</radialGradient></defs>',
        # Background grid
        *[f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="#0d1f3c" stroke-width="1"/>' for x in range(0, W, 40)],
        *[f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#0d1f3c" stroke-width="1"/>' for y in range(0, H, 40)],
        # Title
        f'<text x="10" y="20" font-size="11" fill="#00d4ff" font-family="monospace" font-weight="bold">🦾 SURGICAL ARM</text>',
        f'<text x="10" y="35" font-size="9" fill="#5a7a9a" font-family="monospace">Phase: {phase["icon"]} {phase["name"]}</text>',
        f'<text x="10" y="48" font-size="9" fill="#5a7a9a" font-family="monospace">Tool: {state["tool"]}',
    ]

    if state["tool_speed"] > 0:
        lines.append(f'  @ {state["tool_speed"]} RPM</text>')
    else:
        lines.append(f'</text>')

    # Draw arm segments
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i+1]
        width = max(4, 14 - i * 2)
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{arm_color}" stroke-width="{width}" stroke-linecap="round" opacity="0.9"/>'
        )
        # Segment shadow
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="white" stroke-width="1" stroke-linecap="round" opacity="0.15"/>'
        )

    # Draw joints
    for i, (x, y) in enumerate(points):
        r = max(5, 12 - i * 2)
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#0a0f1e" stroke="{arm_color}" stroke-width="2"/>')
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r-3}" fill="{arm_color}" opacity="0.4"/>')

    # End effector tool indicator
    ex, ey = points[-1]
    lines.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="18" fill="{end_color}" opacity="0.15"/>')
    lines.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="8" fill="{end_color}" opacity="0.8"/>')

    # Tremor visualization
    tx = 10
    ty = H - 120
    lines.append(f'<text x="{tx}" y="{ty}" font-size="9" fill="#5a7a9a" font-family="monospace">TREMOR FILTER</text>')
    bar_w = 140
    raw_fill = int(bar_w * min(state["tremor_raw"] / 3.5, 1))
    flt_fill = int(bar_w * min(state["tremor_filtered"] / 3.5, 1))
    lines.append(f'<text x="{tx}" y="{ty+14}" font-size="8" fill="#ff6644" font-family="monospace">RAW</text>')
    lines.append(f'<rect x="{tx+28}" y="{ty+6}" width="{bar_w}" height="6" fill="#1e3a5f" rx="3"/>')
    lines.append(f'<rect x="{tx+28}" y="{ty+6}" width="{raw_fill}" height="6" fill="#ff6644" rx="3"/>')
    lines.append(f'<text x="{tx}" y="{ty+28}" font-size="8" fill="#00ff88" font-family="monospace">FILTERED</text>')
    lines.append(f'<rect x="{tx+50}" y="{ty+20}" width="{bar_w}" height="6" fill="#1e3a5f" rx="3"/>')
    lines.append(f'<rect x="{tx+50}" y="{ty+20}" width="{flt_fill}" height="6" fill="#00ff88" rx="3"/>')

    # Precision score
    lines.append(f'<text x="{tx}" y="{ty+50}" font-size="9" fill="#5a7a9a" font-family="monospace">PRECISION</text>')
    prec = state["precision_score"]
    p_color = "#00ff88" if prec > 95 else "#ffd700" if prec > 90 else "#ff4444"
    lines.append(f'<text x="{tx+65}" y="{ty+50}" font-size="12" fill="{p_color}" font-family="monospace" font-weight="bold">{prec:.1f}%</text>')

    # Force applied
    lines.append(f'<text x="{tx}" y="{ty+68}" font-size="9" fill="#5a7a9a" font-family="monospace">FORCE APPLIED</text>')
    f_color = "#ff4444" if state["force_applied"] > 40 else "#ffd700" if state["force_applied"] > 20 else "#00d4ff"
    lines.append(f'<text x="{tx+85}" y="{ty+68}" font-size="12" fill="{f_color}" font-family="monospace" font-weight="bold">{state["force_applied"]}N</text>')

    # Collision risk
    lines.append(f'<text x="{tx}" y="{ty+86}" font-size="9" fill="#5a7a9a" font-family="monospace">COLLISION RISK</text>')
    cr = state["collision_risk"]
    cr_color = "#ff4444" if cr > 0.35 else "#ffd700" if cr > 0.2 else "#00ff88"
    lines.append(f'<rect x="{tx+90}" y="{ty+78}" width="80" height="8" fill="#1e3a5f" rx="4"/>')
    lines.append(f'<rect x="{tx+90}" y="{ty+78}" width="{int(80*cr)}" height="8" fill="{cr_color}" rx="4"/>')
    lines.append(f'<text x="{tx+175}" y="{ty+86}" font-size="8" fill="{cr_color}" font-family="monospace">{cr:.0%}</text>')

    # Emergency stop indicator
    if emergency:
        lines.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ff0000" opacity="0.08"/>')
        lines.append(f'<text x="{W//2}" y="{H//2}" text-anchor="middle" font-size="18" fill="#ff4444" font-weight="bold" font-family="monospace">🛑 E-STOP</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def render_knee_map(state, active_zone=None):
    """Render orthopedic knee joint map as SVG."""
    phase_idx = state["phase_idx"]
    W, H = 320, 420
    cx, cy = W // 2, H // 2 - 20

    # Zone highlighting based on phase
    phase_zones = {
        0: None,
        1: "cartilage",
        2: "femur",
        3: "implant",
        4: "implant",
        5: None,
        6: None,
    }
    highlighted = phase_zones.get(phase_idx)

    lines = [
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;background:#060c1a;border-radius:12px;border:1px solid #1e3a5f;">',
        f'<text x="10" y="20" font-size="11" fill="#00d4ff" font-family="monospace" font-weight="bold">🦴 KNEE JOINT MAP</text>',
        f'<text x="10" y="35" font-size="9" fill="#5a7a9a" font-family="monospace">Total Knee Replacement (TKR) — Right Knee</text>',
    ]

    def zone_color(zone_key):
        from surgical_config import KNEE_ZONES
        z = KNEE_ZONES[zone_key]
        if zone_key == highlighted:
            return "#00d4ff"
        risk_colors = {"low": "#3a5a3a", "medium": "#5a4a1a", "high": "#5a2a1a", "critical": "#5a0a0a"}
        return risk_colors.get(z["risk"], "#2a3a5a")

    def zone_stroke(zone_key):
        from surgical_config import KNEE_ZONES
        z = KNEE_ZONES[zone_key]
        if zone_key == highlighted:
            return "#00d4ff"
        risk_strokes = {"low": "#4a8a4a", "medium": "#8a6a2a", "high": "#8a3a2a", "critical": "#cc2222"}
        return risk_strokes.get(z["risk"], "#2a4a6a")

    # Femur (top bone)
    lines.append(f'<ellipse cx="{cx}" cy="{cy-80}" rx="55" ry="70" fill="{zone_color("femur")}" stroke="{zone_stroke("femur")}" stroke-width="2"/>')
    lines.append(f'<text x="{cx}" y="{cy-85}" text-anchor="middle" font-size="9" fill="#c9d8f0" font-family="monospace">FEMUR</text>')

    # Femoral condyles
    lines.append(f'<ellipse cx="{cx-28}" cy="{cy-20}" rx="20" ry="14" fill="{zone_color("femur")}" stroke="{zone_stroke("femur")}" stroke-width="1.5"/>')
    lines.append(f'<ellipse cx="{cx+28}" cy="{cy-20}" rx="20" ry="14" fill="{zone_color("femur")}" stroke="{zone_stroke("femur")}" stroke-width="1.5"/>')

    # Cartilage layer
    lines.append(f'<ellipse cx="{cx-28}" cy="{cy-8}" rx="18" ry="6" fill="{zone_color("cartilage")}" stroke="{zone_stroke("cartilage")}" stroke-width="1.5" opacity="0.8"/>')
    lines.append(f'<ellipse cx="{cx+28}" cy="{cy-8}" rx="18" ry="6" fill="{zone_color("cartilage")}" stroke="{zone_stroke("cartilage")}" stroke-width="1.5" opacity="0.8"/>')

    # Meniscus
    lines.append(f'<ellipse cx="{cx-28}" cy="{cy+6}" rx="16" ry="5" fill="{zone_color("meniscus")}" stroke="{zone_stroke("meniscus")}" stroke-width="1.5" opacity="0.8"/>')
    lines.append(f'<ellipse cx="{cx+28}" cy="{cy+6}" rx="16" ry="5" fill="{zone_color("meniscus")}" stroke="{zone_stroke("meniscus")}" stroke-width="1.5" opacity="0.8"/>')

    # Tibia (bottom bone)
    lines.append(f'<rect x="{cx-52}" y="{cy+14}" width="104" height="90" rx="10" fill="{zone_color("tibia")}" stroke="{zone_stroke("tibia")}" stroke-width="2"/>')
    lines.append(f'<text x="{cx}" y="{cy+65}" text-anchor="middle" font-size="9" fill="#c9d8f0" font-family="monospace">TIBIA</text>')

    # Patella (front)
    lines.append(f'<ellipse cx="{cx-95}" cy="{cy-10}" rx="18" ry="22" fill="{zone_color("patella")}" stroke="{zone_stroke("patella")}" stroke-width="1.5"/>')
    lines.append(f'<text x="{cx-95}" y="{cy-30}" text-anchor="middle" font-size="8" fill="#c9d8f0" font-family="monospace">PAT</text>')

    # ACL
    lines.append(f'<line x1="{cx-10}" y1="{cy-15}" x2="{cx+15}" y2="{cy+12}" stroke="{zone_stroke("ligament_acl")}" stroke-width="3" opacity="0.8"/>')
    lines.append(f'<text x="{cx+20}" y="{cy}" font-size="8" fill="#ff9999" font-family="monospace">ACL</text>')

    # PCL
    lines.append(f'<line x1="{cx+10}" y1="{cy-15}" x2="{cx-15}" y2="{cy+12}" stroke="{zone_stroke("ligament_pcl")}" stroke-width="3" opacity="0.8"/>')
    lines.append(f'<text x="{cx-45}" y="{cy}" font-size="8" fill="#ff9999" font-family="monospace">PCL</text>')

    # Popliteal artery (back)
    lines.append(f'<line x1="{cx+70}" y1="{cy-40}" x2="{cx+70}" y2="{cy+60}" stroke="{zone_stroke("vessel")}" stroke-width="4" opacity="0.7"/>')
    lines.append(f'<text x="{cx+75}" y="{cy+20}" font-size="7" fill="#ff6666" font-family="monospace">POP.</text>')
    lines.append(f'<text x="{cx+75}" y="{cy+30}" font-size="7" fill="#ff6666" font-family="monospace">ART.</text>')

    # Peroneal nerve
    lines.append(f'<path d="M {cx+65} {cy+80} Q {cx+80} {cy+100} {cx+60} {cy+120}" stroke="{zone_stroke("nerve")}" stroke-width="2" fill="none" opacity="0.7"/>')
    lines.append(f'<text x="{cx+68}" y="{cy+110}" font-size="7" fill="#ffb366" font-family="monospace">NERVE</text>')

    # Implant zone highlight
    if phase_idx in [3, 4]:
        lines.append(f'<rect x="{cx-48}" y="{cy+14}" width="96" height="20" rx="4" fill="#00d4ff" opacity="0.25" stroke="#00d4ff" stroke-width="1.5"/>')
        lines.append(f'<text x="{cx}" y="{cy+28}" text-anchor="middle" font-size="8" fill="#00d4ff" font-family="monospace">IMPLANT ZONE</text>')

    # Robot tool position indicator
    tool_positions = {
        0: (cx, cy - 50),
        1: (cx - 28, cy - 15),
        2: (cx, cy - 30),
        3: (cx, cy + 20),
        4: (cx, cy + 20),
        5: (cx, cy),
        6: (cx - 28, cy - 40),
    }
    tp = tool_positions.get(phase_idx, (cx, cy))
    cr = state["collision_risk"]
    tool_color = "#ff4444" if cr > 0.35 else "#00d4ff"
    lines.append(f'<circle cx="{tp[0]}" cy="{tp[1]}" r="10" fill="{tool_color}" opacity="0.3"/>')
    lines.append(f'<circle cx="{tp[0]}" cy="{tp[1]}" r="4" fill="{tool_color}"/>')
    lines.append(f'<circle cx="{tp[0]}" cy="{tp[1]}" r="14" fill="none" stroke="{tool_color}" stroke-width="1" stroke-dasharray="3,3"/>')

    # Legend
    legend_y = H - 75
    lines.append(f'<text x="10" y="{legend_y}" font-size="8" fill="#5a7a9a" font-family="monospace">RISK LEGEND</text>')
    risks = [("LOW", "#4a8a4a"), ("MED", "#8a6a2a"), ("HIGH", "#8a3a2a"), ("CRIT", "#cc2222")]
    for i, (label, color) in enumerate(risks):
        lx = 10 + i * 72
        lines.append(f'<rect x="{lx}" y="{legend_y+6}" width="10" height="8" fill="{color}" rx="2"/>')
        lines.append(f'<text x="{lx+13}" y="{legend_y+14}" font-size="8" fill="#8aaccc" font-family="monospace">{label}</text>')

    # Phase progress bar
    pb_y = H - 25
    total_phases = len(SURGICAL_PHASES)
    lines.append(f'<text x="10" y="{pb_y-5}" font-size="8" fill="#5a7a9a" font-family="monospace">PROCEDURE PROGRESS</text>')
    lines.append(f'<rect x="10" y="{pb_y}" width="{W-20}" height="8" fill="#1e3a5f" rx="4"/>')
    prog_w = int((W-20) * (phase_idx + 1) / total_phases)
    lines.append(f'<rect x="10" y="{pb_y}" width="{prog_w}" height="8" fill="#00d4ff" rx="4"/>')
    lines.append(f'<text x="{W-30}" y="{pb_y+8}" font-size="8" fill="#00d4ff" font-family="monospace">{int((phase_idx+1)/total_phases*100)}%</text>')

    lines.append("</svg>")
    return "\n".join(lines)
