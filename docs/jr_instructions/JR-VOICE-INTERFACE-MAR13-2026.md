# JR INSTRUCTION: Voice Interface — Talk to the Federation

**Task**: Add voice input and voice output to the desktop assistant so users can speak to the council and hear responses. Browser-native Speech API for input, TTS for output. No external service dependency — runs local or via existing infrastructure.
**Priority**: P3
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 3
**Depends On**: Desktop assistant frontend (JR-DESKTOP-ASSISTANT-FRONTEND), gateway chat sessions

## Context

The icing on the cake. Chief wants to talk to the federation, not type. Joe's frontend runs in a browser — the Web Speech API gives us free speech recognition. For output, we can use browser-native SpeechSynthesis or route through a Piper TTS model on BigMac's Ollama stack.

Two-way voice: speak a question → council processes → answer spoken back.

## Step 1: Voice Input — Browser Speech Recognition

Add to Joe's ChatWindow or create a new VoiceChat component:

```typescript
// src/modules/Chat/VoiceInput.tsx

import React, { useState, useRef } from 'react'
import { Mic, MicOff } from 'lucide-react'

interface VoiceInputProps {
  onTranscript: (text: string) => void
  disabled?: boolean
}

export const VoiceInput: React.FC<VoiceInputProps> = ({ onTranscript, disabled }) => {
  const [isListening, setIsListening] = useState(false)
  const recognitionRef = useRef<any>(null)

  const startListening = () => {
    const SpeechRecognition = (window as any).SpeechRecognition
      || (window as any).webkitSpeechRecognition

    if (!SpeechRecognition) {
      alert('Speech recognition not supported in this browser')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = false
    recognition.lang = 'en-US'

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript
      onTranscript(transcript)
      setIsListening(false)
    }

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error)
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition
    recognition.start()
    setIsListening(true)
  }

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
    setIsListening(false)
  }

  return (
    <button
      onClick={isListening ? stopListening : startListening}
      disabled={disabled}
      className={`px-4 py-2 rounded-lg transition-colors ${
        isListening
          ? 'bg-red-600 hover:bg-red-700 text-white animate-pulse'
          : 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-white'
      } disabled:opacity-50`}
      aria-label={isListening ? 'Stop listening' : 'Start voice input'}
    >
      {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
    </button>
  )
}
```

Wire into ChatWindow — add the mic button next to the Send button:

```typescript
// In ChatWindow.tsx, next to the Send button:
<VoiceInput
  onTranscript={(text) => {
    setInput(text)
    // Auto-send after voice input
    handleSendMessage()
  }}
  disabled={isSending}
/>
```

## Step 2: Voice Output — Speak the Response

Browser-native TTS (zero dependencies):

```typescript
// src/modules/Chat/VoiceOutput.tsx

export function speakText(text: string, rate: number = 1.0) {
  if (!('speechSynthesis' in window)) return

  // Cancel any ongoing speech
  window.speechSynthesis.cancel()

  const utterance = new SpeechSynthesisUtterance(text)
  utterance.rate = rate
  utterance.pitch = 1.0
  utterance.volume = 1.0

  // Prefer a natural voice if available
  const voices = window.speechSynthesis.getVoices()
  const preferred = voices.find(v =>
    v.name.includes('Samantha') ||  // macOS
    v.name.includes('Google US') || // Chrome
    v.name.includes('Microsoft') || // Windows
    v.lang === 'en-US'
  )
  if (preferred) {
    utterance.voice = preferred
  }

  window.speechSynthesis.speak(utterance)
}

// Toggle component
import React, { useState } from 'react'
import { Volume2, VolumeX } from 'lucide-react'

export const VoiceToggle: React.FC<{
  enabled: boolean
  onToggle: (enabled: boolean) => void
}> = ({ enabled, onToggle }) => (
  <button
    onClick={() => onToggle(!enabled)}
    className={`p-2 rounded-lg ${enabled ? 'text-blue-600' : 'text-gray-400'}`}
    aria-label={enabled ? 'Disable voice output' : 'Enable voice output'}
  >
    {enabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
  </button>
)
```

Wire into ChatWindow — auto-speak assistant responses:

```typescript
// After receiving assistant response:
if (voiceEnabled) {
  speakText(assistantMessage.content)
}
```

## Step 3: Piper TTS on BigMac (Optional — Higher Quality)

For more natural voice, run Piper TTS locally on BigMac:

```bash
# Install Piper on BigMac
pip3 install piper-tts

# Download a voice model
mkdir -p /Users/Shared/ganuda/models/piper
cd /Users/Shared/ganuda/models/piper
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx
curl -LO https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json
```

Create TTS API endpoint on BigMac:

```python
# /Users/Shared/ganuda/services/tts_bridge.py
"""Piper TTS bridge — high-quality voice synthesis on BigMac.
Port 9200. Federation can POST text, get back WAV audio.
"""

from flask import Flask, request, send_file
import subprocess
import tempfile
import os

app = Flask(__name__)
PIPER_MODEL = "/Users/Shared/ganuda/models/piper/en_US-amy-medium.onnx"

@app.route("/speak", methods=["POST"])
def speak():
    text = request.json.get("text", "")
    if not text:
        return {"error": "no text"}, 400

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        proc = subprocess.run(
            ["piper", "--model", PIPER_MODEL, "--output_file", f.name],
            input=text.encode(), capture_output=True, timeout=30
        )
        if proc.returncode != 0:
            return {"error": proc.stderr.decode()}, 500
        return send_file(f.name, mimetype="audio/wav")

@app.route("/health")
def health():
    return {"status": "healthy", "service": "piper-tts"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9200)
```

Frontend can then:
```typescript
async function speakViaPiper(text: string) {
  const resp = await fetch('http://100.106.9.80:9200/speak', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  const blob = await resp.blob()
  const audio = new Audio(URL.createObjectURL(blob))
  audio.play()
}
```

## Step 4: Voice Mode Toggle in Settings

Add to Joe's SettingsPanel:

```
Voice Input: [ON/OFF] — use microphone for chat input
Voice Output: [Browser TTS / Piper TTS / OFF]
Voice Speed: [0.5x — 2.0x slider]
Auto-speak: [ON/OFF] — automatically read responses aloud
```

## Step 5: Hands-Free Mode

When both voice input and output are enabled:

1. User clicks mic (or hotkey)
2. Speaks question: "What tasks are overdue?"
3. Speech Recognition → text → gateway → tool-call loop → kanban_overdue → answer
4. Answer spoken back via TTS
5. User can follow up immediately (session memory active)

Whole loop: speak → hear answer → speak again. No typing needed.

## DO NOT

- Use external speech APIs (Google Cloud Speech, AWS Polly) — keep it sovereign, local
- Make voice the default — it's opt-in via settings toggle
- Stream TTS before the full response is ready — partial speech is jarring
- Skip the browser-native fallback — Piper is nice-to-have, browser TTS must always work
- Send audio to the gateway — speech recognition happens in the browser, only text goes over the wire

## Acceptance Criteria

- Mic button in ChatWindow captures speech and sends as text
- Browser TTS reads assistant responses aloud when enabled
- Settings panel has voice input/output toggles
- Hands-free conversation loop works (speak → hear → speak)
- Optional: Piper TTS on BigMac for higher quality voice
- No external API dependencies — all local/browser-native
- Works on Chrome, Safari, Firefox (Edge bonus)
