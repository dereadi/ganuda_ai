# JR INSTRUCTION: Sasass Desktop Assistant — Tauri + Voice Chat

**Task**: Build a native macOS desktop assistant on sasass using Tauri (Rust + webview). Voice input via Whisper.cpp, voice output via macOS AVSpeechSynthesizer, chat via Cherokee Gateway tool-call loop. System tray, session persistence, hands-free conversation mode.
**Priority**: P1
**Date**: 2026-03-13
**TPM**: Claude Opus
**Story Points**: 8
**Council Vote**: #798ad0b7 (ToolSet pattern), #4df2e34784f1b36c (MyBrain adoption)
**Depends On**: Gateway tool-call loop (DONE — #1380), ToolSets (DONE), chat sessions schema (DONE)
**Target Node**: sasass (192.168.132.241 / 100.93.205.120 Tailscale) — macOS, 64GB unified memory, Apple Silicon

## Context

Chief wants to talk to the federation from sasass — not type. Tauri gives us a native macOS app with a Rust backend (DC memory: "Use Rust when speed matters"). Whisper.cpp runs natively on Apple Silicon with Metal acceleration — fast local STT, no external API. The gateway on redfin (100.116.27.89:8080) now has the tool-call loop live with 6 read tools. This app connects sasass to the full federation nervous system.

Architecture: Tauri app (Rust) → webview (TypeScript/HTML/CSS) → Cherokee Gateway (redfin) → Qwen 72B + ToolSets + thermal memory + 21 rings

## Step 1: Scaffold Tauri Project on Sasass

```bash
# On sasass — /Users/Shared/ganuda/apps/desktop-assistant
cd /Users/Shared/ganuda/apps
cargo install create-tauri-app
cargo create-tauri-app desktop-assistant --template vanilla-ts

cd desktop-assistant

# Verify it builds
cargo tauri dev
```

Project structure:
```
desktop-assistant/
├── src-tauri/           # Rust backend
│   ├── src/
│   │   ├── main.rs      # Tauri entry, command handlers
│   │   ├── gateway.rs   # Cherokee Gateway HTTP client
│   │   ├── voice.rs     # Whisper.cpp STT + macOS TTS
│   │   └── session.rs   # Local session cache (SQLite)
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/                 # Frontend (webview)
│   ├── index.html
│   ├── main.ts
│   ├── chat.ts          # Chat UI logic
│   ├── voice.ts         # Voice button + waveform
│   └── styles.css
└── package.json
```

## Step 2: Rust Gateway Client

```rust
// src-tauri/src/gateway.rs

use reqwest::Client;
use serde::{Deserialize, Serialize};

const GATEWAY_URL: &str = "http://100.116.27.89:8080";

#[derive(Serialize)]
struct ChatRequest {
    messages: Vec<Message>,
    max_tokens: u32,
    temperature: f32,
    tools: Option<bool>,
    session_id: Option<String>,
}

#[derive(Serialize, Deserialize, Clone)]
struct Message {
    role: String,
    content: String,
}

#[derive(Deserialize)]
struct ChatResponse {
    choices: Vec<Choice>,
    tool_calls_made: Option<Vec<ToolCall>>,
    tool_iterations: Option<u32>,
    usage: Option<Usage>,
}

#[derive(Deserialize)]
struct Choice {
    message: Message,
}

#[derive(Deserialize, Clone)]
pub struct ToolCall {
    pub name: String,
    pub success: bool,
    pub latency_ms: f64,
}

#[derive(Deserialize)]
struct Usage {
    total_tokens: u32,
}

pub struct GatewayClient {
    client: Client,
    api_key: String,
}

impl GatewayClient {
    pub fn new(api_key: String) -> Self {
        Self {
            client: Client::builder()
                .timeout(std::time::Duration::from_secs(120))
                .build()
                .unwrap(),
            api_key,
        }
    }

    pub async fn chat(&self, content: &str, use_tools: bool) -> Result<(String, Vec<ToolCall>), String> {
        let req = ChatRequest {
            messages: vec![Message {
                role: "user".into(),
                content: content.into(),
            }],
            max_tokens: 500,
            temperature: 0.7,
            tools: if use_tools { Some(true) } else { None },
            session_id: None,
        };

        let resp = self.client
            .post(format!("{}/v1/chat/completions", GATEWAY_URL))
            .header("Authorization", format!("Bearer {}", self.api_key))
            .json(&req)
            .send()
            .await
            .map_err(|e| format!("Gateway error: {}", e))?;

        let data: ChatResponse = resp.json().await
            .map_err(|e| format!("Parse error: {}", e))?;

        let content = data.choices.first()
            .map(|c| c.message.content.clone())
            .unwrap_or_default();
        let tools = data.tool_calls_made.unwrap_or_default();

        Ok((content, tools))
    }

    pub async fn health(&self) -> Result<bool, String> {
        let resp = self.client
            .get(format!("{}/health", GATEWAY_URL))
            .send()
            .await
            .map_err(|e| format!("{}", e))?;
        Ok(resp.status().is_success())
    }
}
```

## Step 3: Whisper.cpp Voice Input (Rust)

Use `whisper-rs` crate — Rust bindings for whisper.cpp with Metal acceleration on Apple Silicon.

```toml
# Cargo.toml dependencies
[dependencies]
whisper-rs = { version = "0.12", features = ["metal"] }
cpal = "0.15"  # Cross-platform audio capture
```

```rust
// src-tauri/src/voice.rs

use whisper_rs::{WhisperContext, WhisperContextParameters, FullParams, SamplingStrategy};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::{Arc, Mutex};

const MODEL_PATH: &str = "/Users/Shared/ganuda/models/whisper/ggml-base.en.bin";

pub struct VoiceEngine {
    whisper: WhisperContext,
}

impl VoiceEngine {
    pub fn new() -> Result<Self, String> {
        let params = WhisperContextParameters::default();
        let ctx = WhisperContext::new_with_params(MODEL_PATH, params)
            .map_err(|e| format!("Whisper init failed: {:?}", e))?;
        Ok(Self { whisper: ctx })
    }

    /// Record from microphone until silence detected, return audio samples
    pub fn record_until_silence(&self) -> Result<Vec<f32>, String> {
        let host = cpal::default_host();
        let device = host.default_input_device()
            .ok_or("No input device found")?;

        let config = device.default_input_config()
            .map_err(|e| format!("No input config: {}", e))?;

        let samples: Arc<Mutex<Vec<f32>>> = Arc::new(Mutex::new(Vec::new()));
        let samples_clone = samples.clone();
        let silence_counter: Arc<Mutex<u32>> = Arc::new(Mutex::new(0));
        let silence_clone = silence_counter.clone();

        let stream = device.build_input_stream(
            &config.into(),
            move |data: &[f32], _: &cpal::InputCallbackInfo| {
                let rms: f32 = (data.iter().map(|s| s * s).sum::<f32>() / data.len() as f32).sqrt();
                let mut s = samples_clone.lock().unwrap();
                s.extend_from_slice(data);

                let mut sc = silence_clone.lock().unwrap();
                if rms < 0.01 {
                    *sc += 1;
                } else {
                    *sc = 0;
                }
            },
            |err| eprintln!("Audio error: {}", err),
            None,
        ).map_err(|e| format!("Stream error: {}", e))?;

        stream.play().map_err(|e| format!("Play error: {}", e))?;

        // Wait for speech + silence (1.5 seconds of silence = done)
        loop {
            std::thread::sleep(std::time::Duration::from_millis(100));
            let sc = silence_counter.lock().unwrap();
            let s = samples.lock().unwrap();
            // ~1.5s silence at 44100 Hz / 1024 chunk size ≈ 65 chunks
            if *sc > 65 && s.len() > 16000 {
                break;
            }
            // Safety cap: 30 seconds max
            if s.len() > 44100 * 30 {
                break;
            }
        }

        drop(stream);
        let result = samples.lock().unwrap().clone();
        Ok(result)
    }

    /// Transcribe audio samples to text
    pub fn transcribe(&self, samples: &[f32]) -> Result<String, String> {
        let mut state = self.whisper.create_state()
            .map_err(|e| format!("State error: {:?}", e))?;

        let mut params = FullParams::new(SamplingStrategy::Greedy { best_of: 1 });
        params.set_language(Some("en"));
        params.set_print_special(false);
        params.set_print_progress(false);
        params.set_print_realtime(false);
        params.set_print_timestamps(false);

        state.full(params, samples)
            .map_err(|e| format!("Transcribe error: {:?}", e))?;

        let n_segments = state.full_n_segments()
            .map_err(|e| format!("Segment error: {:?}", e))?;

        let mut text = String::new();
        for i in 0..n_segments {
            if let Ok(segment) = state.full_get_segment_text(i) {
                text.push_str(&segment);
            }
        }

        Ok(text.trim().to_string())
    }
}

/// macOS TTS via AVSpeechSynthesizer (calls `say` command as simple fallback)
pub fn speak_text(text: &str, rate: f32) {
    let rate_arg = format!("{}", (rate * 200.0) as u32); // macOS `say` rate
    std::process::Command::new("say")
        .args(["-r", &rate_arg, text])
        .spawn()
        .ok();
}

/// Stop any ongoing speech
pub fn stop_speaking() {
    std::process::Command::new("killall")
        .arg("say")
        .output()
        .ok();
}
```

## Step 4: Tauri Commands (main.rs)

```rust
// src-tauri/src/main.rs

mod gateway;
mod voice;

use gateway::GatewayClient;
use voice::VoiceEngine;
use std::sync::Mutex;
use tauri::{Manager, SystemTray, SystemTrayEvent, CustomMenuItem, SystemTrayMenu};

struct AppState {
    gateway: GatewayClient,
    voice: Option<VoiceEngine>,
    voice_output_enabled: bool,
    voice_rate: f32,
}

#[tauri::command]
async fn send_message(
    state: tauri::State<'_, Mutex<AppState>>,
    message: String,
    use_tools: bool,
) -> Result<serde_json::Value, String> {
    let gateway = {
        let s = state.lock().unwrap();
        s.gateway.clone() // Gateway client is cheap to clone (Arc internally)
    };

    let (content, tool_calls) = gateway.chat(&message, use_tools).await?;

    // Auto-speak if enabled
    {
        let s = state.lock().unwrap();
        if s.voice_output_enabled {
            voice::speak_text(&content, s.voice_rate);
        }
    }

    Ok(serde_json::json!({
        "content": content,
        "tool_calls": tool_calls,
    }))
}

#[tauri::command]
async fn voice_listen(
    state: tauri::State<'_, Mutex<AppState>>,
) -> Result<String, String> {
    let s = state.lock().unwrap();
    let engine = s.voice.as_ref().ok_or("Voice engine not initialized")?;

    let samples = engine.record_until_silence()?;
    let text = engine.transcribe(&samples)?;
    Ok(text)
}

#[tauri::command]
fn speak(
    state: tauri::State<'_, Mutex<AppState>>,
    text: String,
) -> Result<(), String> {
    let s = state.lock().unwrap();
    voice::speak_text(&text, s.voice_rate);
    Ok(())
}

#[tauri::command]
fn stop_speech() -> Result<(), String> {
    voice::stop_speaking();
    Ok(())
}

#[tauri::command]
fn set_voice_output(
    state: tauri::State<'_, Mutex<AppState>>,
    enabled: bool,
    rate: Option<f32>,
) -> Result<(), String> {
    let mut s = state.lock().unwrap();
    s.voice_output_enabled = enabled;
    if let Some(r) = rate {
        s.voice_rate = r;
    }
    Ok(())
}

#[tauri::command]
async fn check_health(
    state: tauri::State<'_, Mutex<AppState>>,
) -> Result<bool, String> {
    let s = state.lock().unwrap();
    s.gateway.health().await
}

fn main() {
    // Load API key from config
    let api_key = std::fs::read_to_string("/Users/Shared/ganuda/config/secrets.env")
        .unwrap_or_default()
        .lines()
        .find(|l| l.starts_with("LLM_GATEWAY_API_KEY="))
        .map(|l| l.split('=').nth(1).unwrap_or("").to_string())
        .unwrap_or_default();

    let voice_engine = VoiceEngine::new().ok();
    if voice_engine.is_some() {
        println!("[DESKTOP] Whisper voice engine initialized");
    } else {
        println!("[DESKTOP] Voice engine unavailable — download model first");
    }

    let state = AppState {
        gateway: GatewayClient::new(api_key),
        voice: voice_engine,
        voice_output_enabled: false,
        voice_rate: 1.0,
    };

    // System tray
    let tray_menu = SystemTrayMenu::new()
        .add_item(CustomMenuItem::new("open", "Open Chat"))
        .add_item(CustomMenuItem::new("voice", "Toggle Voice"))
        .add_item(CustomMenuItem::new("quit", "Quit"));

    let tray = SystemTray::new().with_menu(tray_menu);

    tauri::Builder::default()
        .system_tray(tray)
        .on_system_tray_event(|app, event| match event {
            SystemTrayEvent::MenuItemClick { id, .. } => match id.as_str() {
                "open" => {
                    if let Some(window) = app.get_window("main") {
                        window.show().unwrap();
                        window.set_focus().unwrap();
                    }
                }
                "quit" => std::process::exit(0),
                _ => {}
            },
            SystemTrayEvent::LeftClick { .. } => {
                if let Some(window) = app.get_window("main") {
                    window.show().unwrap();
                    window.set_focus().unwrap();
                }
            }
            _ => {}
        })
        .manage(Mutex::new(state))
        .invoke_handler(tauri::generate_handler![
            send_message,
            voice_listen,
            speak,
            stop_speech,
            set_voice_output,
            check_health,
        ])
        .run(tauri::generate_context!())
        .expect("error running tauri application");
}
```

## Step 5: Frontend Chat UI

```html
<!-- src/index.html -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Cherokee Federation — Desktop Assistant</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div id="app">
        <header>
            <h1>Cherokee Federation</h1>
            <div id="status-indicator" class="status-dot offline"></div>
            <button id="voice-toggle" class="icon-btn" title="Toggle voice output">🔇</button>
        </header>

        <div id="chat-messages"></div>

        <div id="input-area">
            <textarea id="chat-input" placeholder="Ask the federation..." rows="2"></textarea>
            <button id="send-btn" title="Send">➤</button>
            <button id="mic-btn" class="icon-btn" title="Voice input">🎙</button>
        </div>

        <div id="tool-calls-bar" class="hidden"></div>
    </div>
    <script type="module" src="main.ts"></script>
</body>
</html>
```

```typescript
// src/main.ts
const { invoke } = window.__TAURI__.tauri;

const messagesDiv = document.getElementById('chat-messages')!;
const inputEl = document.getElementById('chat-input') as HTMLTextAreaElement;
const sendBtn = document.getElementById('send-btn')!;
const micBtn = document.getElementById('mic-btn')!;
const voiceToggle = document.getElementById('voice-toggle')!;
const statusDot = document.getElementById('status-indicator')!;
const toolBar = document.getElementById('tool-calls-bar')!;

let voiceOutputEnabled = false;
let isListening = false;

// Check gateway health on startup
async function checkHealth() {
    try {
        const healthy = await invoke('check_health');
        statusDot.className = healthy ? 'status-dot online' : 'status-dot offline';
    } catch {
        statusDot.className = 'status-dot offline';
    }
}

function addMessage(role: string, content: string, toolCalls?: any[]) {
    const msg = document.createElement('div');
    msg.className = `message ${role}`;
    msg.textContent = content;
    messagesDiv.appendChild(msg);

    if (toolCalls && toolCalls.length > 0) {
        toolBar.className = 'tool-calls-bar';
        toolBar.innerHTML = toolCalls.map((tc: any) =>
            `<span class="tool-tag ${tc.success ? 'success' : 'fail'}">${tc.name} (${tc.latency_ms}ms)</span>`
        ).join('');
    } else {
        toolBar.className = 'tool-calls-bar hidden';
    }

    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    inputEl.value = '';
    addMessage('user', text);
    sendBtn.disabled = true;

    try {
        const result: any = await invoke('send_message', {
            message: text,
            useTools: true,
        });
        addMessage('assistant', result.content, result.tool_calls);
    } catch (e: any) {
        addMessage('error', `Error: ${e}`);
    }

    sendBtn.disabled = false;
    inputEl.focus();
}

async function voiceListen() {
    if (isListening) return;
    isListening = true;
    micBtn.classList.add('listening');

    try {
        const transcript: string = await invoke('voice_listen');
        if (transcript) {
            inputEl.value = transcript;
            await sendMessage();
        }
    } catch (e: any) {
        addMessage('error', `Voice error: ${e}`);
    }

    isListening = false;
    micBtn.classList.remove('listening');
}

// Event listeners
sendBtn.addEventListener('click', sendMessage);
inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
micBtn.addEventListener('click', voiceListen);

voiceToggle.addEventListener('click', async () => {
    voiceOutputEnabled = !voiceOutputEnabled;
    voiceToggle.textContent = voiceOutputEnabled ? '🔊' : '🔇';
    await invoke('set_voice_output', { enabled: voiceOutputEnabled });
});

// Startup
checkHealth();
setInterval(checkHealth, 30000);
```

## Step 6: Download Whisper Model on Sasass

```bash
# On sasass
mkdir -p /Users/Shared/ganuda/models/whisper
cd /Users/Shared/ganuda/models/whisper

# Base English model — good balance of speed/accuracy on Apple Silicon
curl -LO https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
# ~142 MB, runs in ~0.5s on M-series chips
```

## Step 7: Secrets Config on Sasass

```bash
# /Users/Shared/ganuda/config/secrets.env (create if not exists)
LLM_GATEWAY_API_KEY=ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5
```

## Step 8: Build and Install

```bash
cd /Users/Shared/ganuda/apps/desktop-assistant
cargo tauri build

# Install the .dmg or .app from target/release/bundle/
# Or run in dev mode:
cargo tauri dev
```

## Voice Conversation Loop (Hands-Free)

When voice output is ON:
1. Click mic (or hotkey — Cmd+Shift+V)
2. Speak: "What tasks are overdue?"
3. Whisper.cpp transcribes locally (~0.5s on Apple Silicon)
4. Gateway tool-call loop: kanban_get_overdue_tasks → Qwen 72B → grounded answer
5. macOS `say` speaks the answer
6. Click mic again for follow-up

Full loop: speak → hear → speak. No typing needed.

## Step 9: Register as Federation Ring (Necklace)

The desktop assistant is internal hardware (sasass) — it registers as an **Associate** ring, not a Temp.

```sql
-- Run on bluefin (192.168.132.222)
INSERT INTO duplo_tool_registry (
    tool_name, tool_type, ring_type, provider, endpoint_url,
    canonical_schema, ring_status, source_node, description
) VALUES (
    'sasass_desktop_assistant',
    'chat_interface',
    'associate',
    'tauri_whisper',
    'http://100.93.205.120:9300',  -- sasass Tailscale IP, local health endpoint
    '{"input": "voice_or_text", "output": "text_plus_tts", "stt": "whisper.cpp", "tts": "macos_say"}',
    'active',
    'sasass',
    'Native macOS desktop assistant on sasass. Whisper.cpp voice input, macOS TTS output, Cherokee Gateway chat with tool-call loop.'
);
```

Add a lightweight health endpoint to the Tauri app (Rust side) so Fire Guard can monitor it:

```rust
// In main.rs — spawn a tiny HTTP health server on port 9300
use std::thread;
use tiny_http::{Server, Response};

fn start_health_server() {
    thread::spawn(|| {
        let server = Server::http("0.0.0.0:9300").unwrap();
        for request in server.incoming_requests() {
            let response = Response::from_string(
                r#"{"status":"healthy","service":"sasass-desktop-assistant","stt":"whisper.cpp"}"#
            ).with_header(
                tiny_http::Header::from_bytes(&b"Content-Type"[..], &b"application/json"[..]).unwrap()
            );
            request.respond(response).ok();
        }
    });
}
```

Call `start_health_server()` in `main()` before `tauri::Builder`.

The ring registration means:
- Fire Guard monitors the app (health check on 100.93.205.120:9300)
- Chain protocol can route voice-capable tasks to sasass
- Ring metering tracks usage
- Shows up in federation status page alongside the 21 other active rings

## DO NOT

- Use Electron — Tauri is lighter, Rust backend aligns with DC memory ("use Rust when speed matters")
- Send audio to the gateway — STT happens locally on sasass via Whisper.cpp
- Use external speech APIs (Google, AWS) — keep it sovereign
- Hardcode the API key in the binary — read from secrets.env at startup
- Skip the system tray — Chief wants it persistent, not a window he has to find
- Make voice the default on launch — it's opt-in via toggle

## Acceptance Criteria

- Tauri app builds and runs on sasass (macOS, Apple Silicon)
- Chat messages route through Cherokee Gateway tool-call loop
- "What tasks are overdue?" returns real data from jr_work_queue
- Mic button captures speech, Whisper.cpp transcribes locally
- Voice toggle enables macOS TTS for responses
- System tray with Open/Voice/Quit menu
- Tool calls shown in UI (which tools were invoked, latency)
- Gateway health indicator (green/red dot)
- Works over Tailscale to redfin (100.116.27.89:8080)
- No external API dependencies — all local/federation
