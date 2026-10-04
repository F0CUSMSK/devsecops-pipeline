#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
# DevSecOps local scanner — same 4 scanners as the CI pipeline
# usage: docker run --rm -v "$(pwd):/code" helmi-devsecops-scanner
# exit code: 0 = no findings, 1 = findings detected
# ──────────────────────────────────────────────────────────────
set -uo pipefail

CODE_DIR="${1:-/code}"
cd "$CODE_DIR" || { echo "cannot access $CODE_DIR"; exit 2; }

FAILED=0
section() { printf '\n\033[1;36m══════ %s ══════\033[0m\n' "$1"; }

# ── 1. Checkov — Terraform misconfiguration ──────────────────
section "Checkov — Terraform misconfiguration"
CHECKOV_TARGET="."
[ -d terraform ] && CHECKOV_TARGET="terraform"
checkov -d "$CHECKOV_TARGET" --framework terraform --compact || FAILED=1

# ── 2. Tfsec — deep Terraform analysis ───────────────────────
section "Tfsec — deep Terraform analysis"
TFSEC_TARGET="."
[ -d terraform ] && TFSEC_TARGET="terraform"
tfsec "$TFSEC_TARGET" || FAILED=1

# ── 3. Gitleaks — secret detection ───────────────────────────
section "Gitleaks — secret detection"
if [ -d .git ]; then
  gitleaks detect --source . --redact -v || FAILED=1
else
  echo "no .git directory — scanning working files only"
  gitleaks detect --no-git --source . --redact -v || FAILED=1
fi

# ── 4. Ansible-Lint — playbook analysis ──────────────────────
section "Ansible-Lint — playbook analysis"
ANSIBLE_TARGET="."
[ -d ansible ] && ANSIBLE_TARGET="ansible"
ansible-lint "$ANSIBLE_TARGET" || FAILED=1

# ── Summary ───────────────────────────────────────────────────
section "Summary"
if [ "$FAILED" -eq 0 ]; then
  echo "PASS — no findings detected by any scanner"
else
  echo "FAIL — findings detected (see scanners above)"
fi
exit "$FAILED"
