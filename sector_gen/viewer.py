from .generator import parse_profile

# Translation maps based on sector_generation_system.md

AC_MAP = {
    0: "Open, well-serviced, no complications",
    1: "Standard, minor friction",
    2: "Moderate - permits, hazardous approach, poor facilities",
    3: "Difficult - active restrictions, dangerous transit, minimal support",
    4: "Very difficult - hostile entry, survival-level approach hazards",
    5: "Effectively inaccessible",
}

HZ_MAP = {
    0: "Benign",
    1: "Minor (standard precautions sufficient)",
    2: "Moderate (specialized gear required)",
    3: "Severe (life-threatening without significant protection)",
    4: "Extreme (survival measured in hours unprotected)",
    5: "Lethal (minutes)",
}

RX_MAP = {
    'N': "Nothing / subsistence",
    'T': "Trade goods, manufactured products",
    'I': "Industrial capacity, production",
    'M': "Raw materials, extraction",
    'B': "Biological, agricultural, organic",
    'S': "Strategic, military, political leverage",
    'C': "Cultural: knowledge, information, pilgrimage, art",
    'X': "Exotic: unique, resists categorization",
}

PP_MAP = {
    0: "Empty - no permanent inhabitants",
    1: "Outpost - dozens to hundreds; everyone knows everyone",
    2: "Sparse - thousands; frontier texture, visible limits of infrastructure",
    3: "Settled - tens of thousands to low millions; functioning society",
    4: "Populated - high millions; urban centers, layered economy",
    5: "Dense - billions; deep social stratification",
}

PW_MAP = {
    'V': "Void - uninhabited or no effective authority",
    'A': "Anarchic - contested, no dominant power",
    'L': "Local - self-governing, inward-facing",
    'C': "Corporate - commercial entity holds primary power",
    'S': "State - conventional bounded political authority",
    'H': "Hegemonic - dominant, reaches beyond the system",
    'E': "External - governed from elsewhere, client system",
}

TN_MAP = {
    0: "Stable",
    1: "Low friction",
    2: "Active disputes, minor incidents",
    3: "Significant conflict, factional violence",
    4: "Open warfare, systemic breakdown",
    5: "Catastrophic - civilizational collapse in progress",
}

DX_MAP = {
    '-': "Nothing exceptional",
    'X': "Xenobiological - alien life, unusual biosphere",
    'P': "Physical phenomenon - astronomical or geological anomaly",
    'H': "Historical - ruins, significant past events, contested legacy",
    'T': "Technological - unusual capability, artifact, active research",
    'C': "Cultural - singular society, ideology, religious center",
    'R': "Restricted - something deliberately hidden or controlled",
    'W': "Weird - referee wildcard, defies categorization",
}

NI_MAP = {
    0: "Irrelevant at network scale",
    1: "Local significance only",
    2: "Regional node",
    3: "Meaningful sector-level presence",
    4: "Major node, cross-sector relevance",
    5: "Critical - loss would reshape the network",
}

NR_MAP = {
    'B': "Backwater - low connectivity, primarily a destination",
    'T': "Transit - passage point on established routes",
    'H': "Hub - high connectivity, multi-route node",
    'K': "Chokepoint - bottleneck, strategic control point",
    'F': "Frontier - edge of settled or charted space",
    'S': "Sanctuary - refuge, neutral ground, off the main lines",
    'I': "Isolated - effectively disconnected",
}

def translate_profile_dict(profile_str: str) -> dict:
    """Parse profile and return a dictionary of translated labels."""
    try:
        p = parse_profile(profile_str)
    except ValueError as e:
        return {"error": str(e)}

    return {
        'access': AC_MAP.get(p['ac'], "Unknown"),
        'hazard': HZ_MAP.get(p['hz'], "Unknown"),
        'resources': RX_MAP.get(p['rx'], "Unknown"),
        'population': PP_MAP.get(p['pp'], "Unknown"),
        'power': PW_MAP.get(p['pw'], "Unknown"),
        'tension': TN_MAP.get(p['tn'], "Unknown"),
        'distinctiveness': DX_MAP.get(p['dx'], "Unknown"),
        'net_importance': NI_MAP.get(p['ni'], "Unknown") if p['ni'] != '' else None,
        'net_role': NR_MAP.get(p['nr'], "Unknown") if p['nr'] != '' else None,
        'raw': p
    }

def translate_system_html(system: dict) -> str:
    """Generate a structured HTML 'Sheet' for the system."""
    t = translate_profile_dict(system.get('profile', ''))
    if "error" in t:
        return f"<p class='error'>Error: {t['error']}</p>"

    sys_id = system.get('id', '')
    html = f"<h3>🗺️ {system.get('name', 'Unknown')} (<code>{system.get('profile', '????')}</code>)</h3>"

    html += "<h4>📌 Intrinsic Characteristics</h4>"
    html += "<ul>"
    if sys_id:
        html += f"<li><b>Coordinates:</b> <code>{sys_id}</code></li>"
    html += f"<li><b>Access (Ac):</b> {t['access']}</li>"
    html += f"<li><b>Hazard (Hz):</b> {t['hazard']}</li>"
    html += f"<li><b>Resources (Rx):</b> {t['resources']}</li>"
    html += f"<li><b>Population (Pp):</b> {t['population']}</li>"
    html += f"<li><b>Authority (Pw):</b> {t['power']}</li>"
    html += f"<li><b>Tension (Tn):</b> {t['tension']}</li>"
    html += f"<li><b>Distinctiveness (Dx):</b> {t['distinctiveness']}</li>"
    html += "</ul>"

    if t['net_importance']:
        html += "<h4>🌐 Interstellar Network Position</h4>"
        html += "<ul>"
        html += f"<li><b>Importance (Ni):</b> {t['net_importance']}</li>"
        html += f"<li><b>Network Role (Nr):</b> {t['net_role']}</li>"
        html += "</ul>"

    notes = system.get('notes', '')
    if notes:
        html += "<h4>📝 GM Notes</h4>"
        html += f"<p><i>{notes}</i></p>"
    
    html += "<p><small><i>(Space for GM annotations and local events)</i></small></p>"
    
    return html

def translate_system(system: dict) -> str:
    """Generate a structured Markdown-style 'Sheet' for the system (plain text)."""
    t = translate_profile_dict(system.get('profile', ''))
    if "error" in t:
        return f"Error: {t['error']}"

    sys_id = system.get('id', '')
    lines = []
    lines.append(f"### 🗺️ {system.get('name', 'Unknown')} (`{system.get('profile', '????')}`)")
    lines.append("")
    lines.append("#### 📌 Intrinsic Characteristics")
    if sys_id:
        lines.append(f"- **Coordinates:** `{sys_id}`")
    lines.append(f"- **Access (Ac):** {t['access']}")
    lines.append(f"- **Hazard (Hz):** {t['hazard']}")
    lines.append(f"- **Resources (Rx):** {t['resources']}")
    lines.append(f"- **Population (Pp):** {t['population']}")
    lines.append(f"- **Authority (Pw):** {t['power']}")
    lines.append(f"- **Tension (Tn):** {t['tension']}")
    lines.append(f"- **Distinctiveness (Dx):** {t['distinctiveness']}")
    lines.append("")

    if t['net_importance']:
        lines.append("#### 🌐 Interstellar Network Position")
        lines.append(f"- **Importance (Ni):** {t['net_importance']}")
        lines.append(f"- **Network Role (Nr):** {t['net_role']}")
        lines.append("")

    notes = system.get('notes', '')
    if notes:
        lines.append("#### 📝 GM Notes")
        lines.append(f"*{notes}*")
        lines.append("")

    lines.append("*(Space for GM annotations and local events)*")
    
    return "\n".join(lines)
