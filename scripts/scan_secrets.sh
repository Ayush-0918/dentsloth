#!/usr/bin/env bash
# scripts/scan_secrets.sh — Scan exported agent session logs or codebase for secrets before sharing
# Usage: ./scripts/scan_secrets.sh [file_or_directory_to_scan]

set -euo pipefail

TARGET="${1:-.}"
echo "=================================================================="
echo " 🛡️  DentSloth Secret Scanner — Pre-Submission Review"
echo " Target: ${TARGET}"
echo "=================================================================="

PATTERNS=(
  "AIza[0-9A-Za-z_\\-]{35}"                                # Google Gemini / Cloud API Key
  "sk-[0-9A-Za-z]{20,}"                                    # OpenAI / LLM API Key
  "mongodb\\+srv://[^:]+:[^@]+@"                           # MongoDB Atlas URI with password
  "https://[a-f0-9]+@[a-z0-9.]+\\.ingest\\.sentry\\.io"    # Sentry DSN with client key
  "xi-api-key"                                             # ElevenLabs API Key
  "ghp_[0-9A-Za-z]{36}"                                    # GitHub Personal Access Token
  "gho_[0-9A-Za-z]{36}"                                    # GitHub OAuth Token
  "rnd_[0-9A-Za-z]{24,}"                                   # Render API Key
  "tabpfn_[0-9A-Za-z]{20,}"                                # TabPFN Cloud Token
)

FOUND=0

for PATTERN in "${PATTERNS[@]}"; do
  # Grep recursively, ignoring git directory, venv, node_modules, and binary files
  MATCHES=$(grep -rnEI "${PATTERN}" "${TARGET}" \
    --exclude-dir=".git" \
    --exclude-dir=".venv" \
    --exclude-dir="node_modules" \
    --exclude-dir="__pycache__" \
    --exclude="*.db" \
    --exclude="*.png" \
    --exclude="*.jpg" \
    --exclude="scan_secrets.sh" \n    --exclude=".env.example" 2>/dev/null || true)

  if [ -n "${MATCHES}" ]; then
    echo "⚠️  POTENTIAL SECRET MATCH for pattern: ${PATTERN}"
    echo "${MATCHES}" | head -n 5
    FOUND=$((FOUND + 1))
  fi
done

echo "------------------------------------------------------------------"
if [ "${FOUND}" -eq 0 ]; then
  echo "✅ SCAN PASSED: Zero leaked API keys or credentials detected."
  echo "   Safe to submit to DevRelay / DEV Challenge post."
  exit 0
else
  echo "❌ SCAN FAILED: Detected ${FOUND} potential secret match(es)."
  echo "   Please sanitize or redact them before publishing."
  exit 1
fi
