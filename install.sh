#!/usr/bin/env bash
set -euo pipefail

WATCHDOG_INSTALL_ROOT="${WATCHDOG_INSTALL_ROOT:-$HOME/.local/share/watchdog}"
VENV_DIR="$WATCHDOG_INSTALL_ROOT/.venv"
BIN_DIR="${HOME}/.local/bin"
INSTALL_MODE="${WATCHDOG_INSTALL_MODE:-pypi}"
FORCE=false
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

info() {
    printf '\033[1;32m[watchdog]\033[0m %s\n' "$*"
}

error() {
    printf '\033[1;31m[watchdog]\033[0m %s\n' "$*" >&2
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        error "Missing required command: $1"
        exit 1
    fi
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

ensure_dirs() {
    mkdir -p "$WATCHDOG_INSTALL_ROOT"
    mkdir -p "$BIN_DIR"
}

create_venv() {
    if [[ -d "$VENV_DIR" ]]; then
        info "Virtual environment already exists at $VENV_DIR"
        if prompt_yes_no "Recreate the virtual environment?"; then
            rm -rf "$VENV_DIR"
            python3 -m venv "$VENV_DIR"
        fi
    else
        python3 -m venv "$VENV_DIR"
    fi
    # shellcheck disable=SC1090
    source "$VENV_DIR/bin/activate"
    python -m pip install --upgrade pip
}

install_watchdog() {
    case "$INSTALL_MODE" in
        local)
            info "Installing watchdog from local repository."
            python -m pip install --upgrade "$REPO_DIR/watchdog"
            ;;
        editable)
            info "Installing watchdog in editable mode."
            python -m pip install --upgrade -e "$REPO_DIR/watchdog"
            ;;
        pypi|*)
            info "Installing watchdog-cli from PyPI."
            python -m pip install --upgrade watchdog-cli
            ;;
    esac
}

prepare_symlink() {
    local target="$1"
    local link_path="$2"
    if [[ -L "$link_path" ]]; then
        local current
        current="$(readlink "$link_path")" || current=""
        if [[ "$current" == "$target" ]]; then
            info "$link_path already points to $target"
            return 1
        fi
    fi
    if [[ -e "$link_path" || -L "$link_path" ]]; then
        if prompt_yes_no "Path $link_path exists. Overwrite?"; then
            local backup="${link_path}.bak.$(date +%s)"
            mv "$link_path" "$backup"
            info "Backed up $link_path to $backup"
        else
            info "Skipping update for $link_path"
            return 1
        fi
    fi
    return 0
}

symlink_bin() {
    local watchdog_target="$VENV_DIR/bin/watchdog"
    local tui_target="$VENV_DIR/bin/watchdog-tui"
    if prepare_symlink "$watchdog_target" "$BIN_DIR/watchdog"; then
        ln -sf "$watchdog_target" "$BIN_DIR/watchdog"
    fi
    if prepare_symlink "$tui_target" "$BIN_DIR/watchdog-tui"; then
        ln -sf "$tui_target" "$BIN_DIR/watchdog-tui"
    fi
    info "Symlinked watchdog binaries into $BIN_DIR"
}

run_post_install() {
    info "Running watchdog doctor (optional)..."
    if ! "$VENV_DIR/bin/watchdog" doctor; then
        error "Watchdog doctor reported issues. Investigate above output."
    fi
    info "Injecting shell snippet via 'watchdog install'..."
    "$VENV_DIR/bin/watchdog" install
}

symlink_bin() {
    ln -sf "$VENV_DIR/bin/watchdog" "$BIN_DIR/watchdog"
    ln -sf "$VENV_DIR/bin/watchdog-tui" "$BIN_DIR/watchdog-tui"
    info "Symlinked watchdog binaries into $BIN_DIR"
}

main() {
    info "Starting Watchdog installation..."
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force)
                FORCE=true
                shift
                ;;
            --mode)
                INSTALL_MODE="$2"
                shift 2
                ;;
            --mode=*)
                INSTALL_MODE="${1#*=}"
                shift
                ;;
            --local)
                INSTALL_MODE="local"
                shift
                ;;
            --editable)
                INSTALL_MODE="editable"
                shift
                ;;
            -h|--help)
                cat <<EOF
Usage: ./install.sh [--force] [--mode pypi|local|editable]

--force           Skip confirmation prompts and overwrite existing files.
--mode <mode>     Choose installation source (default: pypi).
                  pypi      Install watchdog-cli from PyPI.
                  local     Install from this repository's watchdog/ folder.
                  editable  Install the repo in editable mode.
EOF
                exit 0
                ;;
            *)
                error "Unknown argument: $1"
                exit 1
                ;;
        esac
    done

    require_cmd python3
    require_cmd pip

    ensure_dirs
    create_venv
    install_watchdog
    symlink_bin
    run_post_install

    info "Watchdog installation complete."
    echo "Open a new terminal to start logging. Run 'watchdog doctor' if something looks off."
}

main "$@"
