#!/usr/bin/env bash
# Generic provider wrapper example.
#
# Copy this OUTSIDE the repository, e.g. ~/.local/bin/my-agent-wrapper, and adapt
# only provider-specific behavior. The workbench already injects these values:
#
#   WORKBENCH_ACCOUNT_PROFILE
#   WORKBENCH_ACCOUNT_SELECTOR
#   WORKBENCH_ACCOUNT_EMAIL_HINT       (display-only)
#   WORKBENCH_AUTH_STRATEGY
#   WORKBENCH_AUTH_CONTEXT             (when applicable)
#
# For auth_strategy=codex_home it also exports CODEX_HOME.
# For auth_strategy=claude_config_dir it also exports CLAUDE_CONFIG_DIR.
# For auth_strategy=isolated_launcher it exports WORKBENCH_ACCOUNT_LAUNCHER.
#
# Never place passwords, tokens, cookies, auth.json contents, or browser-session
# data in this wrapper or in the project repository.
set -euo pipefail

profile="${WORKBENCH_ACCOUNT_PROFILE:-unknown}"
selector="${WORKBENCH_ACCOUNT_SELECTOR:-unknown}"
strategy="${WORKBENCH_AUTH_STRATEGY:-selector_only}"

printf 'workbench profile=%s selector=%s strategy=%s\n' "$profile" "$selector" "$strategy" >&2

case "$strategy" in
  codex_home)
    : "${CODEX_HOME:?CODEX_HOME was not injected}"
    # Example interactive: exec codex "$@"
    ;;
  claude_config_dir)
    : "${CLAUDE_CONFIG_DIR:?CLAUDE_CONFIG_DIR was not injected}"
    # Example interactive: exec claude "$@"
    ;;
  isolated_launcher)
    : "${WORKBENCH_ACCOUNT_LAUNCHER:?isolated launcher was not injected}"
    # Example Antigravity: exec "$WORKBENCH_ACCOUNT_LAUNCHER" "$@"
    ;;
  selector_only)
    # Custom provider: interpret WORKBENCH_ACCOUNT_SELECTOR yourself.
    ;;
  *)
    echo "unknown auth strategy: $strategy" >&2
    exit 64
    ;;
esac

# If AND ONLY IF the provider positively reports account/quota exhaustion,
# translate that specific condition to exit 75 so the workbench can fail over.
echo "Configure this example wrapper outside the repo before use." >&2
exit 64
