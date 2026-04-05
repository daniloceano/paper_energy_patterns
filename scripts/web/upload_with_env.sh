#!/bin/bash
# Helper script to load environment variables from web/.env.local and run upload

set -e

# Get the repo root (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
ENV_FILE="$REPO_ROOT/web/.env.local"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "❌ File not found: $ENV_FILE"
    exit 1
fi

echo "Loading environment from: $ENV_FILE"

# Load variables from .env.local
set -a  # automatically export all variables
source "$ENV_FILE"
set +a

# Map NEXT_PUBLIC_SUPABASE_URL to SUPABASE_URL if needed
if [[ -z "$SUPABASE_URL" ]] && [[ -n "$NEXT_PUBLIC_SUPABASE_URL" ]]; then
    export SUPABASE_URL="$NEXT_PUBLIC_SUPABASE_URL"
fi

# Verify required variables
if [[ -z "$SUPABASE_URL" ]]; then
    echo "❌ SUPABASE_URL not found in $ENV_FILE"
    exit 1
fi

if [[ -z "$SUPABASE_SERVICE_ROLE_KEY" ]]; then
    echo "❌ SUPABASE_SERVICE_ROLE_KEY not found in $ENV_FILE"
    exit 1
fi

echo "✓ SUPABASE_URL: $SUPABASE_URL"
echo "✓ SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY:0:20}..."
echo ""

# Run the upload script with all arguments passed through
python "$REPO_ROOT/scripts/web/upload_figures_to_supabase.py" "$@"
