#!/bin/bash
#
# Cherokee Constitutional AI - CLI Helper Functions
#

# Source colors
source "$(dirname "${BASH_SOURCE[0]}")/cherokee_colors.sh"

# Cherokee banner
cherokee_banner() {
    echo -e "${TECH_BLUE}╔════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${TECH_BLUE}║${RESET}  🏛️  ${CHEROKEE_GOLD}CHEROKEE CONSTITUTIONAL AI${RESET}                           ${TECH_BLUE}║${RESET}"
    echo -e "${TECH_BLUE}║${RESET}      ${DIM}Democratic • Documented • Deployed${RESET}                  ${TECH_BLUE}║${RESET}"
    echo -e "${TECH_BLUE}╚════════════════════════════════════════════════════════════╝${RESET}"
    echo ""
}

# Section header
section() {
    echo ""
    echo -e "${CHEROKEE_GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${BOLD}$1${RESET}"
    echo -e "${CHEROKEE_GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo ""
}

# Success message
success() {
    echo -e "${STATUS_ACTIVE}✓${RESET} ${BOLD}$1${RESET}"
}

# Error message
error() {
    echo -e "${STATUS_DOWN}✗${RESET} ${BOLD}$1${RESET}" >&2
}

# Warning message
warning() {
    echo -e "${STATUS_DEGRADED}⚠${RESET} ${BOLD}$1${RESET}"
}

# Info message
info() {
    echo -e "${TECH_BLUE}ℹ${RESET} $1"
}

# Progress indicator
progress() {
    echo -e "${TECH_PURPLE}⟳${RESET} $1..."
}

# Jr. status display
jr_status() {
    local jr_name="$1"
    local status="$2"
    local port="$3"

    case "$status" in
        "active")
            echo -e "  ${STATUS_ACTIVE}◉${RESET} ${BOLD}$jr_name${RESET} ${DIM}(:$port)${RESET} - ${STATUS_ACTIVE}Active${RESET}"
            ;;
        "degraded")
            echo -e "  ${STATUS_DEGRADED}◉${RESET} ${BOLD}$jr_name${RESET} ${DIM}(:$port)${RESET} - ${STATUS_DEGRADED}Degraded${RESET}"
            ;;
        "down")
            echo -e "  ${STATUS_DOWN}○${RESET} ${DIM}$jr_name${RESET} ${DIM}(:$port)${RESET} - ${STATUS_DOWN}Down${RESET}"
            ;;
    esac
}

# Thermal temperature display
thermal_temp() {
    local temp=$1
    local label="$2"

    if [ "$temp" -ge 90 ]; then
        echo -e "${TEMP_WHITE_HOT}●${RESET} $label ${DIM}(${temp}°)${RESET} ${TEMP_WHITE_HOT}WHITE HOT${RESET}"
    elif [ "$temp" -ge 70 ]; then
        echo -e "${TEMP_RED_HOT}●${RESET} $label ${DIM}(${temp}°)${RESET} ${TEMP_RED_HOT}RED HOT${RESET}"
    elif [ "$temp" -ge 40 ]; then
        echo -e "${TEMP_WARM}●${RESET} $label ${DIM}(${temp}°)${RESET} ${TEMP_WARM}WARM${RESET}"
    elif [ "$temp" -ge 20 ]; then
        echo -e "${TEMP_COOL}●${RESET} $label ${DIM}(${temp}°)${RESET} ${TEMP_COOL}COOL${RESET}"
    else
        echo -e "${TEMP_COLD}●${RESET} $label ${DIM}(${temp}°)${RESET} ${TEMP_COLD}COLD${RESET}"
    fi
}

# Thermal progress bar
thermal_progress() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((width * current / total))
    local remaining=$((width - completed))

    # Color based on temperature/progress
    local color
    if [ "$percentage" -ge 80 ]; then
        color="${TEMP_RED_HOT}"
    elif [ "$percentage" -ge 50 ]; then
        color="${TEMP_WARM}"
    elif [ "$percentage" -ge 25 ]; then
        color="${TEMP_COOL}"
    else
        color="${TEMP_COLD}"
    fi

    printf "\r🔥 ["
    printf "${color}"
    printf "%${completed}s" | tr ' ' '█'
    printf "${RESET}"
    printf "%${remaining}s" | tr ' ' '░'
    printf "] %3d%% " "$percentage"
}

# Mitakuye Oyasin footer
mitakuye_oyasin() {
    echo ""
    echo -e "${CHEROKEE_GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "  🦅 ${ITALIC}Mitakuye Oyasin - All My Relations${RESET}"
    echo -e "${CHEROKEE_GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
}

# Four Mountains status
four_mountains_status() {
    echo "⛰️  Four Mountains Status:"

    # Check each mountain with actual ping
    if ping -c 1 -W 1 192.168.132.223 &>/dev/null; then
        echo -e "   🌅 ${BOLD}REDFIN${RESET}   ${DIM}(.223)${RESET} ${STATUS_ACTIVE}✓ Active${RESET}"
    else
        echo -e "   🌅 ${BOLD}REDFIN${RESET}   ${DIM}(.223)${RESET} ${STATUS_DOWN}✗ Down${RESET}"
    fi

    if ping -c 1 -W 1 192.168.132.222 &>/dev/null; then
        echo -e "   🌊 ${BOLD}BLUEFIN${RESET}  ${DIM}(.222)${RESET} ${STATUS_ACTIVE}✓ Active${RESET}"
    else
        echo -e "   🌊 ${BOLD}BLUEFIN${RESET}  ${DIM}(.222)${RESET} ${STATUS_DOWN}✗ Down${RESET}"
    fi

    echo -e "   🔥 ${BOLD}SASASS${RESET}   ${DIM}(.223)${RESET} ${STATUS_ACTIVE}✓ Active${RESET} ${DIM}(logical)${RESET}"

    if ping -c 1 -W 1 192.168.132.242 &>/dev/null; then
        echo -e "   💭 ${BOLD}BIGMAC${RESET}   ${DIM}(.242)${RESET} ${STATUS_ACTIVE}✓ Active${RESET}"
    else
        echo -e "   💭 ${BOLD}BIGMAC${RESET}   ${DIM}(.242)${RESET} ${STATUS_DEGRADED}⚠ Unreachable${RESET}"
    fi
}

# System status
csys_status() {
    cherokee_banner

    section "⛰️ Four Mountains Status"
    four_mountains_status

    section "🦅 Active Jr.s"

    # Check Gateway API health
    if curl -sf http://192.168.132.223:8000/health &>/dev/null; then
        jr_status "Gateway API" "active" "8000"
    else
        jr_status "Gateway API" "down" "8000"
    fi

    jr_status "Trading Jr." "active" "8000"
    jr_status "Email Jr." "active" "8000"
    jr_status "Infrastructure Jr." "active" "8002"
    jr_status "Legal Jr." "degraded" "8003"

    section "💾 GPU Resources"
    echo "  GPU 0: RTX 5070 (REDFIN)"
    echo "  GPU 1: RTX 5070 (REDFIN)"
    echo "  GPU 2: RTX 5070 (BLUEFIN)"

    mitakuye_oyasin
}
