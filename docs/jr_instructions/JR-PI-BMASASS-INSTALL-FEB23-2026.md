# Jr Instruction: Install Pi Agent on bmasass

**Task ID:** PI-BMASASS
**Kanban:** #1886
**Priority:** 2
**Assigned:** Software Engineer Jr.

---

## Overview

Install Node.js 22 and Pi Agent on bmasass (M4 Max 128GB, 192.168.132.21) so it can serve as an air-gapped local CLI using its own DeepSeek-R1-70B model.

---

## Step 1: Install Node.js 22 via Homebrew

Run on bmasass (192.168.132.21):

```text
brew install node@22
node --version
npm --version
```

Expected: Node v22.x.x, npm v10.x.x

---

## Step 2: Install Pi Agent globally

```text
npm install -g @mariozechner/pi-coding-agent
which pi
pi --version
```

---

## Step 3: Create models.json for bmasass

Create `/Users/Shared/ganuda/config/pi/models.json`

```json
{
  "providers": {
    "bmasass-mlx": {
      "baseUrl": "http://localhost:8800/v1",
      "api": "openai-completions",
      "apiKey": "not-needed",
      "models": [
        {
          "id": "/Users/Shared/ganuda/models/DeepSeek-R1-Distill-Llama-70B-4bit",
          "name": "DeepSeek R1 70B Llama (bmasass local)",
          "input": ["text"],
          "contextWindow": 32768,
          "maxTokens": 8192,
          "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
        }
      ]
    },
    "redfin-vllm": {
      "baseUrl": "http://192.168.132.222:8000/v1",
      "api": "openai-completions",
      "apiKey": "not-needed",
      "models": [
        {
          "id": "/ganuda/models/qwen2.5-72b-instruct-awq",
          "name": "Qwen 72B (redfin)",
          "input": ["text"],
          "contextWindow": 32768,
          "maxTokens": 8192,
          "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
        }
      ]
    }
  }
}
```

Then symlink to Pi config:

```text
mkdir -p ~/.pi/agent
ln -sf /Users/Shared/ganuda/config/pi/models.json ~/.pi/agent/models.json
```

---

## Step 4: Create shell aliases

Append to `~/.zshrc` on bmasass:

<<<<<<< SEARCH
# End of .zshrc
=======
# Pi Agent — Cherokee AI Federation
alias pi-local='pi --provider bmasass-mlx'
alias pi-qwen='pi --provider redfin-vllm'
alias pi-reason='pi --provider bmasass-mlx'

# End of .zshrc
>>>>>>> REPLACE

If `# End of .zshrc` does not exist, append the alias block to the end of the file.

---

## Step 5: Verify

```text
pi --list-models
pi --provider bmasass-mlx --print --no-session "What is 2+2? Answer in one word."
```

Expected: Both models listed, inference returns "Four" or "4".

---

## Notes

- bmasass uses Homebrew (not nvm) since it is macOS
- localhost:8800 for local model (no nftables issue)
- redfin:8000 access may require nftables rule on redfin — verify connectivity
- Federation extension (separate Jr task) will be symlinked after creation
