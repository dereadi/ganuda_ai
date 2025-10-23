#!/bin/bash
# Cherokee Constitutional AI - Build JR Ollama Models
# Builds all 5 Cherokee-trained brain region models from Modelfiles

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
🦅 Building Cherokee Constitutional AI JR Models
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   5 Brain Regions with Cherokee Corpus
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
echo -e "${NC}"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}❌ Ollama not found. Please install from https://ollama.ai${NC}"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama not running. Starting...${NC}"
    ollama serve &
    sleep 5
fi

# Base model required (Llama 3.1 8B)
BASE_MODEL="llama3.1:8b"
echo -e "${BLUE}📦 Checking base model: $BASE_MODEL${NC}"

if ! ollama list | grep -q "$BASE_MODEL"; then
    echo -e "${YELLOW}⚠️  Base model not found. Pulling $BASE_MODEL...${NC}"
    ollama pull "$BASE_MODEL"
fi

echo -e "${GREEN}✅ Base model ready${NC}"
echo ""

# Build each JR model
JR_MODELS=(
    "memory_jr"
    "meta_jr"
    "executive_jr"
    "integration_jr"
    "conscience_jr"
)

MODELFILE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/modelfiles" && pwd)"

for jr in "${JR_MODELS[@]}"; do
    MODEL_NAME="${jr}_resonance:latest"
    MODELFILE="$MODELFILE_DIR/${jr}.Modelfile"

    echo -e "${BLUE}🧠 Building $MODEL_NAME from Modelfile...${NC}"

    if [ ! -f "$MODELFILE" ]; then
        echo -e "${RED}❌ Modelfile not found: $MODELFILE${NC}"
        exit 1
    fi

    # Build model from Modelfile
    ollama create "$MODEL_NAME" -f "$MODELFILE"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $MODEL_NAME built successfully${NC}"
    else
        echo -e "${RED}❌ Failed to build $MODEL_NAME${NC}"
        exit 1
    fi

    echo ""
done

# Verify all models are available
echo -e "${BLUE}📊 Verifying Cherokee JR models...${NC}"
echo ""

for jr in "${JR_MODELS[@]}"; do
    MODEL_NAME="${jr}_resonance:latest"
    if ollama list | grep -q "$MODEL_NAME"; then
        SIZE=$(ollama list | grep "$MODEL_NAME" | awk '{print $3" "$4}')
        echo -e "${GREEN}✅ $MODEL_NAME ($SIZE)${NC}"
    else
        echo -e "${RED}❌ $MODEL_NAME not found${NC}"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🦅 All 5 Cherokee JR models built successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Test with:"
echo "  ollama run memory_jr_resonance:latest 'What is thermal memory?'"
echo ""
echo "Or use the CLI executor:"
echo "  python3 cli/jr_executor.py --jr memory_jr --prompt 'What is thermal memory?'"
echo ""
echo -e "${BLUE}🔥 Mitakuye Oyasin - All My Relations!${NC}"
