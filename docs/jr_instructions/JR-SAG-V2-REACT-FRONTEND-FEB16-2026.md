# Jr Instruction: SAG v2 React Chat Frontend

**Task ID**: SAG-V2-FRONTEND
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**Sprint**: RC-2026-02E
**Dependencies**: SAG-V2-FASTAPI
**use_rlm**: false

## Objective
Create a lightweight React chat UI for SAG v2 using Vite. Supports SSE streaming, tool call visualization, and settings panel for LLM endpoint configuration. Build to static files served by FastAPI.

## Step 1: Create package.json

Create `/ganuda/services/sag-v2/frontend/package.json`

```json
{
  "name": "sag-v2-frontend",
  "private": true,
  "version": "2.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-markdown": "^9.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.4.0"
  }
}
```

## Step 2: Create vite.config.js

Create `/ganuda/services/sag-v2/frontend/vite.config.js`

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:4100'
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
```

## Step 3: Create index.html

Create `/ganuda/services/sag-v2/frontend/index.html`

```text
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SAG v2 — Resource Allocation Assistant</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; }
    #root { height: 100vh; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
```

## Step 4: Create main.jsx

Create `/ganuda/services/sag-v2/frontend/src/main.jsx`

```javascript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

## Step 5: Create App.jsx

Create `/ganuda/services/sag-v2/frontend/src/App.jsx`

```javascript
import React, { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100vh', maxWidth: '900px', margin: '0 auto', padding: '0 16px' },
  header: { padding: '16px 0', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: '18px', fontWeight: 600, color: '#38bdf8' },
  subtitle: { fontSize: '12px', color: '#64748b' },
  messages: { flex: 1, overflowY: 'auto', padding: '16px 0' },
  msg: { marginBottom: '16px', padding: '12px 16px', borderRadius: '8px', lineHeight: 1.6 },
  userMsg: { background: '#1e3a5f', marginLeft: '48px' },
  assistantMsg: { background: '#1e293b', marginRight: '48px' },
  toolCall: { background: '#1a2332', border: '1px solid #334155', borderRadius: '6px', padding: '8px 12px', margin: '8px 0', fontSize: '13px' },
  toolName: { color: '#a78bfa', fontWeight: 600 },
  inputArea: { padding: '16px 0', borderTop: '1px solid #334155', display: 'flex', gap: '8px' },
  input: { flex: 1, padding: '12px 16px', background: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#e2e8f0', fontSize: '14px', outline: 'none' },
  button: { padding: '12px 24px', background: '#2563eb', border: 'none', borderRadius: '8px', color: 'white', fontSize: '14px', fontWeight: 600, cursor: 'pointer' },
  buttonDisabled: { opacity: 0.5, cursor: 'not-allowed' },
  settings: { fontSize: '12px', color: '#64748b', cursor: 'pointer', textDecoration: 'underline' },
}

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [config, setConfig] = useState(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    fetch('/api/config').then(r => r.json()).then(setConfig).catch(() => {})
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMsg = { role: 'user', content: input }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          history: newMessages.filter(m => m.role === 'user' || m.role === 'assistant').map(m => ({ role: m.role, content: m.content })),
        }),
      })
      const data = await resp.json()
      if (data.response) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
      } else if (data.error) {
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${data.error}` }])
      }
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Connection error: ${e.message}` }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <div style={styles.title}>SAG v2 — Resource Allocation Assistant</div>
          <div style={styles.subtitle}>
            {config ? `${config.llm?.provider} / ${config.llm?.model}` : 'Connecting...'}
          </div>
        </div>
      </div>

      <div style={styles.messages}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', padding: '48px 0', color: '#64748b' }}>
            <p style={{ fontSize: '16px', marginBottom: '8px' }}>Ask about team availability, project assignments, or workload</p>
            <p style={{ fontSize: '13px' }}>Try: "Who is available next week?" or "Show me team utilization for February"</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{ ...styles.msg, ...(m.role === 'user' ? styles.userMsg : styles.assistantMsg) }}>
            <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>
              {m.role === 'user' ? 'You' : 'SAG Assistant'}
            </div>
            {m.role === 'assistant' ? (
              <ReactMarkdown>{m.content}</ReactMarkdown>
            ) : (
              <div>{m.content}</div>
            )}
          </div>
        ))}
        {loading && (
          <div style={{ ...styles.msg, ...styles.assistantMsg }}>
            <div style={{ color: '#64748b' }}>Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div style={styles.inputArea}>
        <input
          style={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about team availability, projects, or workload..."
          disabled={loading}
        />
        <button
          style={{ ...styles.button, ...(loading ? styles.buttonDisabled : {}) }}
          onClick={sendMessage}
          disabled={loading}
        >
          Send
        </button>
      </div>
    </div>
  )
}

export default App
```

## Manual Steps (TPM)
- On redfin: `cd /ganuda/services/sag-v2/frontend && npm install && npm run build`
- Verify: `ls /ganuda/services/sag-v2/frontend/dist/index.html`
