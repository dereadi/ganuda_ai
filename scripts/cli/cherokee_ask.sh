#!/bin/bash
#
# Cherokee Constitutional AI - Natural Language Interface
# Main "cherokee ask" command
#

# Source functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/cherokee_functions.sh"

# Main ask function
cherokee_ask() {
    local request="$*"

    if [ -z "$request" ]; then
        error "Usage: cherokee ask \"your request here\""
        return 1
    fi

    cherokee_banner
    section "🗣️ Natural Language Request"
    echo -e "Request: ${BOLD}$request${RESET}"
    echo ""

    # Step 1: Route to Synthesis Jr. for planning
    progress "Routing to Synthesis Jr. for planning"

    local plan_response=$(curl -s -X POST http://192.168.132.223:8000/api/gateway/ask \
        -H "Content-Type: application/json" \
        -d "{
            \"question\": \"$request\",
            \"context\": \"Natural language CLI request. You are Synthesis Jr., the orchestrator. Analyze this request and create an execution plan. Identify: 1) Which Jr should handle this (trading_jr, legal_jr, vision_jr, software_engineer_jr, archive_jr), 2) What the deliverable should be, 3) Brief steps. Respond in a clear, structured way.\",
            \"specialist\": \"synthesis\"
        }" 2>/dev/null)

    if [ $? -ne 0 ] || [ -z "$plan_response" ]; then
        # Gateway might not support specialist routing, try direct
        plan_response=$(curl -s -X POST http://localhost:11434/api/generate \
            -d "{
                \"model\": \"qwen2.5:14b\",
                \"prompt\": \"You are Synthesis Jr. of Cherokee Constitutional AI. User request: '$request'. Create a brief execution plan: 1) Which Jr should handle this? 2) What will be delivered? 3) Key steps. Be concise.\",
                \"stream\": false
            }" 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin).get('response', ''))" 2>/dev/null)
    fi

    # Display plan
    section "📋 Execution Plan"
    if [ -n "$plan_response" ]; then
        echo "$plan_response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('answer', data.get('response', data)))" 2>/dev/null || echo "$plan_response"
    else
        warning "Could not generate plan, proceeding with direct execution"
    fi

    echo ""

    # Step 2: Determine which Jr. to use
    local target_jr=""

    # Simple keyword routing
    if echo "$request" | grep -iqE "portfolio|trading|stock|market|price"; then
        target_jr="trading_jr"
    elif echo "$request" | grep -iqE "design|visual|diagram|beautiful|style|css"; then
        target_jr="vision"
    elif echo "$request" | grep -iqE "code|script|program|function|deploy|install"; then
        target_jr="software_engineer"
    elif echo "$request" | grep -iqE "legal|document|policy|vote|govern"; then
        target_jr="legal_jr"
    elif echo "$request" | grep -iqE "search|find|history|archive|remember"; then
        target_jr="archive"
    elif echo "$request" | grep -iqE "status|health|system|monitor|check"; then
        target_jr="infra"
    else
        # Default to synthesis for general questions
        target_jr="synthesis"
    fi

    info "Routing to: ${BOLD}$target_jr${RESET}"

    # Step 3: Execute request
    section "⚡ Executing Request"
    progress "Asking $target_jr"

    local response=$(curl -s -X POST http://192.168.132.223:8000/api/${target_jr}/ask \
        -H "Content-Type: application/json" \
        -d "{
            \"question\": \"$request\",
            \"context\": \"CLI natural language request. Provide actionable response.\"
        }" 2>/dev/null)

    if [ $? -ne 0 ] || [ -z "$response" ]; then
        # Try local Ollama as fallback
        response=$(curl -s -X POST http://localhost:11434/api/generate \
            -d "{
                \"model\": \"llama3.1:8b\",
                \"prompt\": \"$request\",
                \"stream\": false
            }" 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin).get('response', ''))" 2>/dev/null)
    fi

    # Display response
    section "💬 Response from $target_jr"

    if [ -n "$response" ]; then
        # Try to extract answer from JSON
        local answer=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('answer', data.get('response', '')))" 2>/dev/null)

        if [ -n "$answer" ]; then
            echo -e "${answer}"
        else
            echo -e "${response}"
        fi

        success "Request completed"
    else
        error "No response received from $target_jr"
        return 1
    fi

    mitakuye_oyasin
}

# Export function
export -f cherokee_ask
