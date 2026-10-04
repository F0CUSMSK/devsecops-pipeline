import json
import os
from datetime import datetime

# ─────────────────────────────────────────────
# Load report files
# ─────────────────────────────────────────────

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return None

checkov  = load_json("reports/checkov/results_json.json")
tfsec    = load_json("reports/tfsec/tfsec-report.json")
gitleaks = load_json("reports/gitleaks/gitleaks-report.json")
ansible  = load_json("reports/ansible/ansible-lint-report.json")

# ─────────────────────────────────────────────
# Parse each report
# ─────────────────────────────────────────────

def parse_checkov(data):
    if not data:
        return {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "findings": []}
    results = data.get("results", {})
    failed  = results.get("failed_checks", [])
    findings = []
    for f in failed:
        findings.append({
            "file":     f.get("repo_file_path", "unknown"),
            "rule":     f.get("check_id", ""),
            "message":  f.get("check_name", ""),
            "severity": f.get("severity", "MEDIUM") or "MEDIUM"
        })
    severity_count = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        s = f["severity"].upper()
        if s in severity_count:
            severity_count[s] += 1
        else:
            severity_count["MEDIUM"] += 1
    return {
        "total":    len(findings),
        "critical": severity_count["CRITICAL"],
        "high":     severity_count["HIGH"],
        "medium":   severity_count["MEDIUM"],
        "low":      severity_count["LOW"],
        "findings": findings[:10]
    }

def parse_tfsec(data):
    if not data:
        return {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "findings": []}
    results  = data.get("results", []) or []
    findings = []
    severity_count = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in results:
        sev = r.get("severity", "MEDIUM").upper()
        findings.append({
            "file":     r.get("location", {}).get("filename", "unknown"),
            "rule":     r.get("rule_id", ""),
            "message":  r.get("description", ""),
            "severity": sev
        })
        if sev in severity_count:
            severity_count[sev] += 1
        else:
            severity_count["MEDIUM"] += 1
    return {
        "total":    len(findings),
        "critical": severity_count["CRITICAL"],
        "high":     severity_count["HIGH"],
        "medium":   severity_count["MEDIUM"],
        "low":      severity_count["LOW"],
        "findings": findings[:10]
    }

def parse_gitleaks(data):
    if not data:
        return {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "findings": []}
    leaks    = data if isinstance(data, list) else []
    findings = []
    for l in leaks:
        findings.append({
            "file":     l.get("File", "unknown"),
            "rule":     l.get("RuleID", ""),
            "message":  l.get("Description", "Secret detected"),
            "severity": "CRITICAL"
        })
    return {
        "total":    len(findings),
        "critical": len(findings),
        "high":     0,
        "medium":   0,
        "low":      0,
        "findings": findings[:10]
    }

def parse_ansible(data):
    empty = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "findings": []}
    if not data:
        return empty
    findings = []
    severity_count = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    sev_map = {
        "very-high": "HIGH", "high": "HIGH",
        "medium": "MEDIUM", "low": "LOW",
        "very-low": "LOW", "info": "LOW",
    }
    violations = []
    if isinstance(data, dict):
        # ansible-lint >= 6 JSON: {"rule-id": [{file, line, column, message, severity}, ...]}
        for rule_id, items in data.items():
            if not isinstance(items, list):
                continue
            for i in items:
                violations.append((rule_id, i))
    elif isinstance(data, list):
        for i in data:
            violations.append((i.get("rule", {}).get("id", ""), i))
    for rule_id, i in violations:
        sev = sev_map.get(str(i.get("severity", "medium")).lower(), "MEDIUM")
        loc = i.get("file", "unknown")
        if i.get("line"):
            loc += f":{i['line']}"
        findings.append({
            "file":     loc,
            "rule":     rule_id,
            "message":  i.get("message", ""),
            "severity": sev
        })
        severity_count[sev] += 1
    return {
        "total":    len(findings),
        "critical": severity_count["CRITICAL"],
        "high":     severity_count["HIGH"],
        "medium":   severity_count["MEDIUM"],
        "low":      severity_count["LOW"],
        "findings": findings[:10]
    }

c = parse_checkov(checkov)
t = parse_tfsec(tfsec)
g = parse_gitleaks(gitleaks)
a = parse_ansible(ansible)

total_findings  = c["total"] + t["total"] + g["total"] + a["total"]
total_critical  = c["critical"] + t["critical"] + g["critical"] + a["critical"]
total_high      = c["high"] + t["high"] + g["high"] + a["high"]
total_medium    = c["medium"] + t["medium"] + g["medium"] + a["medium"]
total_low       = c["low"] + t["low"] + g["low"] + a["low"]

# ─────────────────────────────────────────────
# Build findings rows
# ─────────────────────────────────────────────

def findings_rows(findings, scanner):
    if not findings:
        return f'<tr><td colspan="4" class="empty">No findings loaded for {scanner}</td></tr>'
    rows = ""
    for f in findings:
        sev   = f["severity"].upper()
        badge = f'<span class="badge badge-{sev.lower()}">{sev}</span>'
        rows += f"""
        <tr>
          <td><code>{f['file']}</code></td>
          <td><code class="rule-id">{f['rule']}</code></td>
          <td>{f['message']}</td>
          <td>{badge}</td>
        </tr>"""
    return rows

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

# ─────────────────────────────────────────────
# HTML Dashboard
# ─────────────────────────────────────────────

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>DevSecOps Security Dashboard</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:          #0d1117;
      --surface:     #161b22;
      --surface2:    #21262d;
      --border:      #30363d;
      --text:        #e6edf3;
      --text-muted:  #7d8590;
      --critical:    #ff4d4f;
      --high:        #fa8c16;
      --medium:      #fadb14;
      --low:         #52c41a;
      --accent:      #388bfd;
      --accent-glow: rgba(56,139,253,0.15);
    }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', sans-serif;
      font-size: 14px;
      line-height: 1.6;
      min-height: 100vh;
    }}

    /* ── Header ── */
    header {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 24px 40px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .header-left h1 {{
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.3px;
    }}
    .header-left h1 span {{ color: var(--accent); }}
    .header-left p {{
      color: var(--text-muted);
      font-size: 13px;
      margin-top: 2px;
    }}
    .scan-time {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: var(--text-muted);
      background: var(--surface2);
      border: 1px solid var(--border);
      padding: 6px 12px;
      border-radius: 6px;
    }}

    /* ── Main ── */
    main {{ padding: 32px 40px; max-width: 1400px; margin: 0 auto; }}

    /* ── Summary cards ── */
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 16px;
      margin-bottom: 32px;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px;
      text-align: center;
      transition: border-color 0.2s;
    }}
    .card:hover {{ border-color: var(--accent); }}
    .card .num {{
      font-size: 36px;
      font-weight: 700;
      font-family: 'JetBrains Mono', monospace;
      line-height: 1;
      margin-bottom: 6px;
    }}
    .card .label {{
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .card.total   .num {{ color: var(--accent); }}
    .card.critical .num {{ color: var(--critical); }}
    .card.high     .num {{ color: var(--high); }}
    .card.medium   .num {{ color: var(--medium); }}
    .card.low      .num {{ color: var(--low); }}
    .card.scanners .num {{ color: #b392f0; }}

    /* ── Scanner status row ── */
    .scanner-row {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 32px;
    }}
    .scanner-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px 20px;
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .scanner-icon {{
      width: 40px;
      height: 40px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      flex-shrink: 0;
    }}
    .scanner-icon.fail {{ background: rgba(255,77,79,0.15); }}
    .scanner-icon.pass {{ background: rgba(82,196,26,0.15); }}
    .scanner-info .name {{
      font-weight: 600;
      font-size: 14px;
    }}
    .scanner-info .count {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 2px;
    }}
    .status-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      margin-left: auto;
      flex-shrink: 0;
    }}
    .status-dot.fail {{ background: var(--critical); box-shadow: 0 0 6px var(--critical); }}
    .status-dot.pass {{ background: var(--low); box-shadow: 0 0 6px var(--low); }}

    /* ── Section ── */
    .section {{ margin-bottom: 32px; }}
    .section-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }}
    .section-header h2 {{
      font-size: 16px;
      font-weight: 600;
    }}
    .section-header .badge-count {{
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 12px;
      padding: 2px 8px;
      border-radius: 20px;
      font-family: 'JetBrains Mono', monospace;
    }}

    /* ── Table ── */
    .table-wrap {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      overflow: hidden;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    thead tr {{
      background: var(--surface2);
      border-bottom: 1px solid var(--border);
    }}
    th {{
      padding: 12px 16px;
      text-align: left;
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    td {{
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: var(--surface2); }}
    code {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 12px;
      color: var(--accent);
    }}
    .rule-id {{ color: var(--text-muted); }}
    .empty {{
      text-align: center;
      color: var(--text-muted);
      padding: 24px;
      font-style: italic;
    }}

    /* ── Badges ── */
    .badge {{
      display: inline-block;
      padding: 3px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      font-family: 'JetBrains Mono', monospace;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge-critical {{ background: rgba(255,77,79,0.15);  color: var(--critical); border: 1px solid rgba(255,77,79,0.3); }}
    .badge-high     {{ background: rgba(250,140,22,0.15); color: var(--high);     border: 1px solid rgba(250,140,22,0.3); }}
    .badge-medium   {{ background: rgba(250,219,20,0.15); color: var(--medium);   border: 1px solid rgba(250,219,20,0.3); }}
    .badge-low      {{ background: rgba(82,196,26,0.15);  color: var(--low);      border: 1px solid rgba(82,196,26,0.3); }}

    /* ── Footer ── */
    footer {{
      text-align: center;
      padding: 24px;
      color: var(--text-muted);
      font-size: 12px;
      border-top: 1px solid var(--border);
      margin-top: 16px;
    }}
    footer span {{ color: var(--accent); }}
  </style>
</head>
<body>

<header>
  <div class="header-left">
    <h1>🛡️ DevSecOps <span>Security Dashboard</span></h1>
    <p>Shift-Left Static Code Analysis Pipeline · EPI Digital School 2026</p>
  </div>
  <div class="scan-time">⏱ Last scan: {now}</div>
</header>

<main>

  <!-- Summary Cards -->
  <div class="summary-grid">
    <div class="card total">
      <div class="num">{total_findings}</div>
      <div class="label">Total Findings</div>
    </div>
    <div class="card critical">
      <div class="num">{total_critical}</div>
      <div class="label">Critical</div>
    </div>
    <div class="card high">
      <div class="num">{total_high}</div>
      <div class="label">High</div>
    </div>
    <div class="card medium">
      <div class="num">{total_medium}</div>
      <div class="label">Medium</div>
    </div>
    <div class="card low">
      <div class="num">{total_low}</div>
      <div class="label">Low</div>
    </div>
    <div class="card scanners">
      <div class="num">4</div>
      <div class="label">Scanners</div>
    </div>
  </div>

  <!-- Scanner Status -->
  <div class="scanner-row">
    <div class="scanner-card">
      <div class="scanner-icon fail">🔍</div>
      <div class="scanner-info">
        <div class="name">Checkov</div>
        <div class="count">{c['total']} findings · Terraform IaC</div>
      </div>
      <div class="status-dot {'fail' if c['total'] > 0 else 'pass'}"></div>
    </div>
    <div class="scanner-card">
      <div class="scanner-icon fail">🔎</div>
      <div class="scanner-info">
        <div class="name">Tfsec</div>
        <div class="count">{t['total']} findings · Terraform Deep</div>
      </div>
      <div class="status-dot {'fail' if t['total'] > 0 else 'pass'}"></div>
    </div>
    <div class="scanner-card">
      <div class="scanner-icon fail">🔑</div>
      <div class="scanner-info">
        <div class="name">Gitleaks</div>
        <div class="count">{g['total']} findings · Secret Detection</div>
      </div>
      <div class="status-dot {'fail' if g['total'] > 0 else 'pass'}"></div>
    </div>
    <div class="scanner-card">
      <div class="scanner-icon fail">⚙️</div>
      <div class="scanner-info">
        <div class="name">Ansible-Lint</div>
        <div class="count">{a['total']} findings · Playbook Analysis</div>
      </div>
      <div class="status-dot {'fail' if a['total'] > 0 else 'pass'}"></div>
    </div>
  </div>

  <!-- Checkov Results -->
  <div class="section">
    <div class="section-header">
      <h2>🔍 Checkov — Terraform Misconfiguration</h2>
      <span class="badge-count">{c['total']} findings</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>File</th><th>Rule ID</th><th>Description</th><th>Severity</th></tr></thead>
        <tbody>{findings_rows(c['findings'], 'Checkov')}</tbody>
      </table>
    </div>
  </div>

  <!-- Tfsec Results -->
  <div class="section">
    <div class="section-header">
      <h2>🔎 Tfsec — Deep Terraform Analysis</h2>
      <span class="badge-count">{t['total']} findings</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>File</th><th>Rule ID</th><th>Description</th><th>Severity</th></tr></thead>
        <tbody>{findings_rows(t['findings'], 'Tfsec')}</tbody>
      </table>
    </div>
  </div>

  <!-- Gitleaks Results -->
  <div class="section">
    <div class="section-header">
      <h2>🔑 Gitleaks — Secret Detection</h2>
      <span class="badge-count">{g['total']} findings</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>File</th><th>Rule ID</th><th>Description</th><th>Severity</th></tr></thead>
        <tbody>{findings_rows(g['findings'], 'Gitleaks')}</tbody>
      </table>
    </div>
  </div>

  <!-- Ansible-Lint Results -->
  <div class="section">
    <div class="section-header">
      <h2>⚙️ Ansible-Lint — Playbook Analysis</h2>
      <span class="badge-count">{a['total']} findings</span>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Task</th><th>Rule ID</th><th>Description</th><th>Severity</th></tr></thead>
        <tbody>{findings_rows(a['findings'], 'Ansible-Lint')}</tbody>
      </table>
    </div>
  </div>

</main>

<footer>
  Generated by <span>DevSecOps Pipeline</span> · Helmi Mastouri · EPI Digital School 2026
</footer>

</body>
</html>"""

os.makedirs("reports", exist_ok=True)
with open("reports/dashboard.html", "w") as f:
    f.write(html)

print("✅ Dashboard generated at reports/dashboard.html")
print(f"   Total findings : {total_findings}")
print(f"   Critical        : {total_critical}")
print(f"   High            : {total_high}")
print(f"   Medium          : {total_medium}")
print(f"   Low             : {total_low}")
