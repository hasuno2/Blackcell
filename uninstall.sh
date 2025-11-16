#!/usr/bin/env bash
set -euo pipefail

WATCHDOG_INSTALL_ROOT="${WATCHDOG_INSTALL_ROOT:-$HOME/.local/share/watchdog}"
VENV_DIR="$WATCHDOG_INSTALL_ROOT/.venv"
BIN_DIR="${HOME}/.local/bin"
FORCE=false
LOG_ROOT="$HOME/.watchdog"

info() {
    printf '\033[1;32m[watchdog]\033[0m %s\n' "$*"
}

error() {
    printf '\033[1;31m[watchdog]\033[0m %s\n' "$*" >&2
}

prompt_yes_no() {
    local prompt="$1"
    if $FORCE; then
        return 0
    fi
    read -r -p "$prompt [y/N]: " response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

remove_path() {
    local path="$1"
    local description="$2"
    if [[ -e "$path" || -L "$path" ]]; then
        if prompt_yes_no "Remove $description at $path?"; then
            rm -rf "$path"
            info "Removed $description ($path)"
        else
            info "Skipped removal of $description."
        fi
    fi
}

remove_symlinks() {
    remove_path "$BIN_DIR/watchdog" "watchdog symlink"
    remove_path "$BIN_DIR/watchdog-tui" "watchdog-tui symlink"
}

uninstall_snippet() {
    local watchdog_bin="$VENV_DIR/bin/watchdog"
    if [[ -x "$watchdog_bin" ]]; then
        info "Running 'watchdog uninstall' to remove shell snippet..."
        if ! "$watchdog_bin" uninstall; then
            error "Failed to run watchdog uninstall. You may need to remove the snippet manually."
        fi
    else
        info "watchdog binary not found in $VENV_DIR; skipping snippet removal."
    fi
}

main() {
    info "Starting Watchdog removal..."
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force)
                FORCE=true
                shift
                ;;
            -h|--help)
                cat <<EOF
Usage: ./uninstall.sh [--force]

--force    Remove without confirmation prompts.
EOF
                exit 0
                ;;
            *)
                error "Unknown argument: $1"
                exit 1
                ;;
        esac
    done

    uninstall_snippet
    remove_symlinks
    remove_path "$WATCHDOG_INSTALL_ROOT" "watchdog virtual environment + install directory"
    remove_path "$LOG_ROOT" "watchdog log directory"

    info "Watchdog uninstall complete."
}

main "$@"
