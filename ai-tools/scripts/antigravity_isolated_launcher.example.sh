#!/usr/bin/env bash
# EXAMPLE ONLY -- copy outside the repository and adapt to your OS.
#
# Linux example for an Antigravity profile whose credentials live in another
# OS user's secure keyring. Replace `agy-account-1` with your actual local user.
# The account's browser login is completed manually once inside that isolated
# user/keyring context.
set -euo pipefail

AGY_OS_USER="agy-account-1"   # REPLACE_ME
exec sudo -u "$AGY_OS_USER" -H agy "$@"
