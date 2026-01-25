# Jr Instructions: A2UI Proof-of-Concept Implementation

**Task ID**: RESEARCH-A2UI-001
**Priority**: MEDIUM
**Target**: Any node with Node.js/Python capability
**Requires**: Node.js 18+, Python 3.10+, internet access for npm/pip
**Council Review**: APPROVED WITH CONDITIONS - Build PoC before production adoption
**Status**: READY FOR IMPLEMENTATION

---

## Executive Summary

Google A2UI (Agent-to-User Interface) is an open-source protocol that lets AI agents generate rich, interactive UIs via declarative JSON without executing code. The Council has endorsed evaluation with a proof-of-concept before production adoption.

This Jr instruction implements a PoC demonstrating A2UI capabilities for Cherokee AI Federation use cases.

---

## A2UI Overview

### What It Is
- **Declarative JSON protocol** for agent-generated UIs
- Agents output JSON describing components, clients render natively
- **No code execution** - security through pre-approved component catalog
- **Framework-agnostic** - same JSON works on React, Flutter, Angular, mobile

### Key Resources
- GitHub: https://github.com/google/A2UI (8.4k stars)
- Docs: https://a2ui.org/
- CopilotKit Integration: https://www.copilotkit.ai/ag-ui-and-a2ui
- License: Apache 2.0

### How It Works
```
1. Agent generates A2UI JSON payload describing UI components
2. JSON transported to client (via AG-UI, REST, WebSocket, etc.)
3. Client's A2UI Renderer parses JSON
4. Renderer maps abstract components to native widgets
```

---

## PoC Architecture

### Option 1: Standalone A2UI Renderer (Recommended for PoC)

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  vLLM/Council   │────▶│  A2UI JSON   │────▶│  Web Renderer   │
│  (redfin)       │     │  Generator   │     │  (React/Lit)    │
└─────────────────┘     └──────────────┘     └─────────────────┘
```

### Option 2: CopilotKit + AG-UI Integration

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  vLLM Backend   │────▶│  AG-UI       │────▶│  CopilotKit     │
│  (redfin)       │     │  Transport   │     │  Frontend       │
└─────────────────┘     └──────────────┘     └─────────────────┘
```

---

## Implementation Steps

### Phase 1: Environment Setup

```bash
# Create project directory
mkdir -p /ganuda/projects/a2ui-poc
cd /ganuda/projects/a2ui-poc

# Initialize Node.js project
npm init -y

# Install A2UI dependencies
npm install @anthropic-ai/sdk  # For agent integration
npm install lit                 # For web components renderer

# Clone A2UI reference implementation
git clone https://github.com/google/A2UI.git a2ui-reference
```

### Phase 2: A2UI JSON Generator

Create a Python module that generates A2UI-compliant JSON from Federation data:

```python
#!/usr/bin/env python3
"""
a2ui_generator.py - Generate A2UI JSON for Cherokee AI Federation

Converts Federation data (Council votes, thermal memory, VetAssist)
into A2UI-compliant JSON payloads.
"""

from typing import Dict, List, Any
import json
from datetime import datetime

class A2UIGenerator:
    """Generate A2UI JSON payloads for Federation interfaces."""

    def __init__(self):
        self.component_id = 0

    def _next_id(self) -> str:
        """Generate unique component ID."""
        self.component_id += 1
        return f"comp_{self.component_id}"

    def generate_council_vote_ui(self, vote_data: Dict[str, Any]) -> Dict:
        """
        Generate A2UI for Council vote display.

        Args:
            vote_data: Council vote response from /v1/council/vote

        Returns:
            A2UI JSON payload
        """
        components = []

        # Header card
        components.append({
            "id": self._next_id(),
            "type": "card",
            "properties": {
                "title": "Council Deliberation",
                "subtitle": vote_data.get("question", "")[:100] + "..."
            },
            "children": []
        })

        # Recommendation badge
        recommendation = vote_data.get("recommendation", "PENDING")
        badge_color = "green" if "APPROVED" in recommendation else "yellow" if "REVIEW" in recommendation else "red"
        components.append({
            "id": self._next_id(),
            "type": "badge",
            "properties": {
                "text": recommendation,
                "color": badge_color
            }
        })

        # Confidence meter
        confidence = vote_data.get("confidence", 0)
        components.append({
            "id": self._next_id(),
            "type": "progress",
            "properties": {
                "label": f"Confidence: {confidence:.1%}",
                "value": confidence,
                "max": 1.0
            }
        })

        # Concerns list
        concerns = vote_data.get("concerns", [])
        if concerns:
            concern_items = []
            for concern in concerns:
                concern_items.append({
                    "id": self._next_id(),
                    "type": "list-item",
                    "properties": {
                        "text": concern,
                        "icon": "warning"
                    }
                })

            components.append({
                "id": self._next_id(),
                "type": "list",
                "properties": {
                    "title": "Specialist Concerns"
                },
                "children": [item["id"] for item in concern_items]
            })
            components.extend(concern_items)

        # Consensus text
        components.append({
            "id": self._next_id(),
            "type": "text",
            "properties": {
                "content": vote_data.get("consensus", ""),
                "variant": "body"
            }
        })

        return {
            "version": "0.8",
            "components": components,
            "data": {
                "vote_id": vote_data.get("audit_hash", ""),
                "timestamp": vote_data.get("timestamp", datetime.now().isoformat())
            }
        }

    def generate_thermal_memory_ui(self, memories: List[Dict]) -> Dict:
        """
        Generate A2UI for thermal memory visualization.

        Args:
            memories: List of thermal memory entries

        Returns:
            A2UI JSON payload
        """
        components = []

        # Header
        components.append({
            "id": self._next_id(),
            "type": "card",
            "properties": {
                "title": "Thermal Memory Archive",
                "subtitle": f"{len(memories)} memories loaded"
            }
        })

        # Memory cards
        for memory in memories[:10]:  # Limit to 10 for PoC
            importance = memory.get("importance", 0.5)
            temp_color = "red" if importance > 0.8 else "orange" if importance > 0.5 else "blue"

            components.append({
                "id": self._next_id(),
                "type": "card",
                "properties": {
                    "title": f"Memory #{memory.get('id', 'N/A')}",
                    "subtitle": memory.get("event_type", "unknown"),
                    "color": temp_color
                },
                "children": []
            })

            # Memory content
            components.append({
                "id": self._next_id(),
                "type": "text",
                "properties": {
                    "content": memory.get("context", "")[:200] + "...",
                    "variant": "body"
                }
            })

            # Importance indicator
            components.append({
                "id": self._next_id(),
                "type": "progress",
                "properties": {
                    "label": f"Temperature: {importance:.2f}",
                    "value": importance,
                    "max": 1.0,
                    "color": temp_color
                }
            })

        return {
            "version": "0.8",
            "components": components,
            "data": {
                "total_memories": len(memories),
                "displayed": min(len(memories), 10)
            }
        }

    def generate_vetassist_form_ui(self, form_type: str = "condition_search") -> Dict:
        """
        Generate A2UI for VetAssist interface.

        Args:
            form_type: Type of form (condition_search, calculator, statement_builder)

        Returns:
            A2UI JSON payload
        """
        components = []

        if form_type == "condition_search":
            # Search header
            components.append({
                "id": self._next_id(),
                "type": "card",
                "properties": {
                    "title": "VA Disability Condition Search",
                    "subtitle": "Find conditions and their ratings"
                }
            })

            # Search input
            search_id = self._next_id()
            components.append({
                "id": search_id,
                "type": "text-field",
                "properties": {
                    "label": "Search conditions",
                    "placeholder": "e.g., tinnitus, PTSD, back pain",
                    "name": "condition_query"
                }
            })

            # Search button
            components.append({
                "id": self._next_id(),
                "type": "button",
                "properties": {
                    "label": "Search",
                    "action": "search_conditions",
                    "variant": "primary"
                }
            })

            # Results placeholder
            components.append({
                "id": self._next_id(),
                "type": "container",
                "properties": {
                    "id": "search_results",
                    "empty_text": "Enter a condition to search"
                },
                "children": []
            })

        elif form_type == "calculator":
            # Calculator header
            components.append({
                "id": self._next_id(),
                "type": "card",
                "properties": {
                    "title": "VA Combined Rating Calculator",
                    "subtitle": "Calculate your combined disability rating"
                }
            })

            # Rating inputs (up to 5)
            for i in range(5):
                components.append({
                    "id": self._next_id(),
                    "type": "number-field",
                    "properties": {
                        "label": f"Rating {i+1} (%)",
                        "name": f"rating_{i}",
                        "min": 0,
                        "max": 100,
                        "step": 10
                    }
                })

            # Calculate button
            components.append({
                "id": self._next_id(),
                "type": "button",
                "properties": {
                    "label": "Calculate Combined Rating",
                    "action": "calculate_rating",
                    "variant": "primary"
                }
            })

            # Result display
            components.append({
                "id": self._next_id(),
                "type": "text",
                "properties": {
                    "content": "",
                    "variant": "heading",
                    "id": "result_display"
                }
            })

        return {
            "version": "0.8",
            "components": components,
            "data": {
                "form_type": form_type
            }
        }


def demo_a2ui_generation():
    """Demonstrate A2UI generation for Federation use cases."""

    generator = A2UIGenerator()

    # Demo 1: Council Vote UI
    sample_vote = {
        "audit_hash": "abc123",
        "question": "Should we adopt A2UI for Federation interfaces?",
        "recommendation": "APPROVED WITH CONDITIONS",
        "confidence": 0.85,
        "concerns": [
            "Crawdad: [SECURITY CONCERN] - Vet component catalog",
            "Gecko: [PERF CONCERN] - Test rendering overhead"
        ],
        "consensus": "Council endorses A2UI adoption with proof-of-concept evaluation.",
        "timestamp": "2025-12-30T06:15:00Z"
    }

    council_ui = generator.generate_council_vote_ui(sample_vote)
    print("=== Council Vote A2UI ===")
    print(json.dumps(council_ui, indent=2))

    # Demo 2: VetAssist Form UI
    vetassist_ui = generator.generate_vetassist_form_ui("condition_search")
    print("\n=== VetAssist Search A2UI ===")
    print(json.dumps(vetassist_ui, indent=2))

    # Save examples
    with open("/ganuda/projects/a2ui-poc/examples/council_vote.json", "w") as f:
        json.dump(council_ui, f, indent=2)

    with open("/ganuda/projects/a2ui-poc/examples/vetassist_search.json", "w") as f:
        json.dump(vetassist_ui, f, indent=2)

    print("\nExamples saved to /ganuda/projects/a2ui-poc/examples/")


if __name__ == "__main__":
    demo_a2ui_generation()
```

### Phase 3: Simple Web Renderer

Create a minimal HTML/JS renderer to display A2UI JSON:

```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cherokee AI Federation - A2UI PoC</title>
    <style>
        :root {
            --federation-blue: #1e3a5f;
            --federation-gold: #d4a012;
            --bg-dark: #0d1117;
            --text-light: #c9d1d9;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-dark);
            color: var(--text-light);
            margin: 0;
            padding: 20px;
        }

        .a2ui-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
        }

        .a2ui-card-title {
            color: var(--federation-gold);
            font-size: 1.2em;
            margin: 0 0 8px 0;
        }

        .a2ui-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .a2ui-badge.green { background: #238636; }
        .a2ui-badge.yellow { background: #9e6a03; }
        .a2ui-badge.red { background: #da3633; }

        .a2ui-progress {
            background: #30363d;
            border-radius: 4px;
            height: 8px;
            margin: 8px 0;
            overflow: hidden;
        }

        .a2ui-progress-bar {
            height: 100%;
            background: var(--federation-gold);
            transition: width 0.3s ease;
        }

        .a2ui-text-field {
            width: 100%;
            padding: 10px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: var(--text-light);
            font-size: 1em;
            margin: 8px 0;
        }

        .a2ui-button {
            background: var(--federation-blue);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            margin: 8px 0;
        }

        .a2ui-button:hover {
            background: #2a4a7f;
        }

        .a2ui-button.primary {
            background: var(--federation-gold);
            color: black;
        }

        .a2ui-list {
            list-style: none;
            padding: 0;
            margin: 8px 0;
        }

        .a2ui-list-item {
            padding: 8px 0;
            border-bottom: 1px solid #30363d;
        }

        #a2ui-container {
            max-width: 800px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 24px;
        }

        .header h1 {
            color: var(--federation-gold);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Cherokee AI Federation</h1>
        <p>A2UI Proof of Concept</p>
    </div>

    <div id="a2ui-container">
        <p>Loading A2UI interface...</p>
    </div>

    <script>
        /**
         * A2UI Renderer - Maps A2UI JSON to HTML elements
         */
        class A2UIRenderer {
            constructor(container) {
                this.container = container;
                this.componentMap = new Map();
            }

            render(a2uiPayload) {
                this.container.innerHTML = '';
                this.componentMap.clear();

                const { components, data } = a2uiPayload;

                for (const component of components) {
                    const element = this.renderComponent(component);
                    if (element) {
                        this.componentMap.set(component.id, element);
                        this.container.appendChild(element);
                    }
                }

                return this.componentMap;
            }

            renderComponent(component) {
                const { type, properties, children } = component;

                switch (type) {
                    case 'card':
                        return this.renderCard(properties, children);
                    case 'badge':
                        return this.renderBadge(properties);
                    case 'progress':
                        return this.renderProgress(properties);
                    case 'text':
                        return this.renderText(properties);
                    case 'text-field':
                        return this.renderTextField(properties);
                    case 'number-field':
                        return this.renderNumberField(properties);
                    case 'button':
                        return this.renderButton(properties);
                    case 'list':
                        return this.renderList(properties, children);
                    case 'list-item':
                        return this.renderListItem(properties);
                    case 'container':
                        return this.renderContainer(properties, children);
                    default:
                        console.warn(`Unknown component type: ${type}`);
                        return null;
                }
            }

            renderCard(props, children) {
                const card = document.createElement('div');
                card.className = 'a2ui-card';

                if (props.title) {
                    const title = document.createElement('h3');
                    title.className = 'a2ui-card-title';
                    title.textContent = props.title;
                    card.appendChild(title);
                }

                if (props.subtitle) {
                    const subtitle = document.createElement('p');
                    subtitle.textContent = props.subtitle;
                    card.appendChild(subtitle);
                }

                return card;
            }

            renderBadge(props) {
                const badge = document.createElement('span');
                badge.className = `a2ui-badge ${props.color || 'blue'}`;
                badge.textContent = props.text;
                return badge;
            }

            renderProgress(props) {
                const container = document.createElement('div');

                if (props.label) {
                    const label = document.createElement('div');
                    label.textContent = props.label;
                    container.appendChild(label);
                }

                const progress = document.createElement('div');
                progress.className = 'a2ui-progress';

                const bar = document.createElement('div');
                bar.className = 'a2ui-progress-bar';
                bar.style.width = `${(props.value / props.max) * 100}%`;

                progress.appendChild(bar);
                container.appendChild(progress);

                return container;
            }

            renderText(props) {
                const text = document.createElement(props.variant === 'heading' ? 'h2' : 'p');
                text.textContent = props.content;
                if (props.id) text.id = props.id;
                return text;
            }

            renderTextField(props) {
                const container = document.createElement('div');

                if (props.label) {
                    const label = document.createElement('label');
                    label.textContent = props.label;
                    container.appendChild(label);
                }

                const input = document.createElement('input');
                input.type = 'text';
                input.className = 'a2ui-text-field';
                input.name = props.name;
                input.placeholder = props.placeholder || '';

                container.appendChild(input);
                return container;
            }

            renderNumberField(props) {
                const container = document.createElement('div');

                if (props.label) {
                    const label = document.createElement('label');
                    label.textContent = props.label;
                    container.appendChild(label);
                }

                const input = document.createElement('input');
                input.type = 'number';
                input.className = 'a2ui-text-field';
                input.name = props.name;
                input.min = props.min;
                input.max = props.max;
                input.step = props.step;

                container.appendChild(input);
                return container;
            }

            renderButton(props) {
                const button = document.createElement('button');
                button.className = `a2ui-button ${props.variant || ''}`;
                button.textContent = props.label;
                button.dataset.action = props.action;

                button.addEventListener('click', () => {
                    console.log(`A2UI Action: ${props.action}`);
                    // Dispatch custom event for action handling
                    window.dispatchEvent(new CustomEvent('a2ui-action', {
                        detail: { action: props.action }
                    }));
                });

                return button;
            }

            renderList(props, children) {
                const list = document.createElement('ul');
                list.className = 'a2ui-list';

                if (props.title) {
                    const title = document.createElement('h4');
                    title.textContent = props.title;
                    list.insertAdjacentElement('beforebegin', title);
                }

                return list;
            }

            renderListItem(props) {
                const item = document.createElement('li');
                item.className = 'a2ui-list-item';
                item.textContent = props.text;
                return item;
            }

            renderContainer(props, children) {
                const container = document.createElement('div');
                if (props.id) container.id = props.id;
                if (props.empty_text) {
                    container.textContent = props.empty_text;
                }
                return container;
            }
        }

        // Initialize renderer
        const container = document.getElementById('a2ui-container');
        const renderer = new A2UIRenderer(container);

        // Load sample A2UI payload
        async function loadA2UI() {
            try {
                // Try to fetch from examples directory
                const response = await fetch('examples/council_vote.json');
                if (response.ok) {
                    const payload = await response.json();
                    renderer.render(payload);
                } else {
                    // Use inline demo payload
                    const demoPayload = {
                        version: "0.8",
                        components: [
                            {
                                id: "1",
                                type: "card",
                                properties: {
                                    title: "A2UI PoC Active",
                                    subtitle: "Cherokee AI Federation interface renderer"
                                }
                            },
                            {
                                id: "2",
                                type: "badge",
                                properties: {
                                    text: "DEMO MODE",
                                    color: "yellow"
                                }
                            },
                            {
                                id: "3",
                                type: "text",
                                properties: {
                                    content: "This is a proof-of-concept A2UI renderer. Generate JSON payloads from the Federation backend to render real interfaces.",
                                    variant: "body"
                                }
                            }
                        ]
                    };
                    renderer.render(demoPayload);
                }
            } catch (error) {
                console.error('Error loading A2UI:', error);
                container.innerHTML = '<p>Error loading A2UI interface. Check console for details.</p>';
            }
        }

        // Handle A2UI actions
        window.addEventListener('a2ui-action', (event) => {
            const { action } = event.detail;
            console.log('Handling action:', action);

            // Add action handlers here
            switch (action) {
                case 'search_conditions':
                    alert('Search action triggered - connect to VetAssist API');
                    break;
                case 'calculate_rating':
                    alert('Calculate action triggered - connect to rating calculator');
                    break;
                default:
                    console.log('Unhandled action:', action);
            }
        });

        // Load on page ready
        loadA2UI();
    </script>
</body>
</html>
```

### Phase 4: Integration with Federation Backend

```python
#!/usr/bin/env python3
"""
a2ui_server.py - Federation A2UI Backend

Serves A2UI JSON from Council votes and thermal memory.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

# Import generator
from a2ui_generator import A2UIGenerator

generator = A2UIGenerator()

COUNCIL_URL = "http://100.116.27.89:8080"
COUNCIL_API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"


@app.route('/a2ui/council/vote', methods=['POST'])
def council_vote_ui():
    """Generate A2UI for a Council vote."""
    data = request.json
    question = data.get('question', '')

    # Call Council API
    response = requests.post(
        f"{COUNCIL_URL}/v1/council/vote",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": COUNCIL_API_KEY
        },
        json={"question": question},
        timeout=120
    )

    vote_data = response.json()

    # Generate A2UI
    a2ui_payload = generator.generate_council_vote_ui(vote_data)

    return jsonify(a2ui_payload)


@app.route('/a2ui/vetassist/<form_type>', methods=['GET'])
def vetassist_form_ui(form_type):
    """Generate A2UI for VetAssist forms."""
    a2ui_payload = generator.generate_vetassist_form_ui(form_type)
    return jsonify(a2ui_payload)


@app.route('/a2ui/thermal-memory', methods=['GET'])
def thermal_memory_ui():
    """Generate A2UI for thermal memory visualization."""
    # TODO: Connect to actual thermal memory
    sample_memories = [
        {"id": 7210, "importance": 0.95, "event_type": "research_success", "context": "ICL dynamics working..."},
        {"id": 7205, "importance": 0.90, "event_type": "cleanup", "context": "Redfin storage cleanup..."},
    ]

    a2ui_payload = generator.generate_thermal_memory_ui(sample_memories)
    return jsonify(a2ui_payload)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
```

---

## Directory Structure

```
/ganuda/projects/a2ui-poc/
├── README.md
├── package.json
├── a2ui_generator.py      # Python A2UI JSON generator
├── a2ui_server.py         # Flask backend
├── index.html             # Web renderer
├── examples/
│   ├── council_vote.json
│   ├── vetassist_search.json
│   └── thermal_memory.json
└── a2ui-reference/        # Cloned Google A2UI repo
```

---

## Testing Plan

### Test 1: Static Rendering
1. Generate sample A2UI JSON with `a2ui_generator.py`
2. Open `index.html` in browser
3. Verify components render correctly

### Test 2: Council Integration
1. Start `a2ui_server.py`
2. POST to `/a2ui/council/vote` with a question
3. Verify Council vote renders in A2UI format

### Test 3: VetAssist Forms
1. GET `/a2ui/vetassist/condition_search`
2. Verify search form renders
3. Test form interactions

---

## Success Criteria

| Criteria | Target | Status |
|----------|--------|--------|
| A2UI JSON generator works | Generates valid A2UI v0.8 | Pending |
| Web renderer displays components | All component types render | Pending |
| Council votes render correctly | Badge, progress, list work | Pending |
| VetAssist forms functional | Inputs, buttons work | Pending |
| Backend integration complete | API serves A2UI JSON | Pending |

---

## Security Considerations (Per Crawdad)

1. **Component Catalog**: Only allow pre-defined component types in renderer
2. **No eval()**: Never execute dynamic code from A2UI payloads
3. **Input Sanitization**: Escape all text content before rendering
4. **CORS**: Restrict to Federation origins only in production
5. **API Key**: Don't expose Council API key in frontend code

---

## Next Steps After PoC

1. **Evaluate Performance**: Measure rendering latency for complex UIs
2. **Mobile Testing**: Test A2UI on mobile browsers
3. **CopilotKit Integration**: If PoC succeeds, integrate with AG-UI
4. **Production Security Review**: Full security audit before deployment
5. **Council Re-vote**: Present PoC results for production adoption decision

---

## References

- [Google A2UI GitHub](https://github.com/google/A2UI)
- [A2UI Documentation](https://a2ui.org/)
- [CopilotKit AG-UI](https://www.copilotkit.ai/ag-ui-and-a2ui)
- [Council Vote on A2UI](thermal_memory_id: pending)

---

*For Seven Generations - Building interfaces that serve our descendants*
