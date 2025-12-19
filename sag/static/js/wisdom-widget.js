/**
 * Pathfinder Wisdom Widget for SAG
 * Natural language infrastructure queries
 */

const WISDOM_API = 'http://192.168.132.223:5678';

class WisdomWidget {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.render();
    }

    render() {
        this.container.innerHTML = `
            <div class="wisdom-widget card">
                <div class="card-header">
                    <h5>🔮 Ask Pathfinder Wisdom</h5>
                    <span class="wisdom-accuracy badge bg-success">Accuracy: Loading...</span>
                </div>
                <div class="card-body">
                    <div class="input-group mb-3">
                        <input type="text" class="form-control wisdom-input"
                               placeholder="Why is GPU utilization low?"
                               onkeypress="if(event.key==='Enter') wisdomWidget.ask()">
                        <button class="btn btn-primary" onclick="wisdomWidget.ask()">Ask</button>
                    </div>
                    <div class="wisdom-response"></div>
                    <div class="wisdom-feedback d-none">
                        <small>Was this helpful?</small>
                        <button class="btn btn-sm btn-outline-success" onclick="wisdomWidget.feedback(true)">👍</button>
                        <button class="btn btn-sm btn-outline-danger" onclick="wisdomWidget.feedback(false)">👎</button>
                    </div>
                </div>
            </div>
        `;
        this.loadHealth();
    }

    async loadHealth() {
        try {
            const resp = await fetch(`${WISDOM_API}/wisdom/health`);
            const data = await resp.json();
            const accuracy = (data.overall_accuracy * 100).toFixed(0);
            this.container.querySelector('.wisdom-accuracy').textContent =
                `Accuracy: ${accuracy}% (${data.total_validated} predictions)`;
        } catch (e) {
            this.container.querySelector('.wisdom-accuracy').textContent = 'Wisdom Offline';
        }
    }

    async ask() {
        const input = this.container.querySelector('.wisdom-input');
        const responseDiv = this.container.querySelector('.wisdom-response');
        const question = input.value.trim();

        if (!question) return;

        responseDiv.innerHTML = '<div class="spinner-border spinner-border-sm"></div> Thinking...';

        try {
            const resp = await fetch(`${WISDOM_API}/wisdom/query`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question, include_metrics: true})
            });
            const data = await resp.json();

            this.currentPredictionId = data.prediction_id;

            responseDiv.innerHTML = `
                <div class="alert alert-info">
                    <strong>Wisdom says:</strong><br>
                    ${data.answer.replace(/\n/g, '<br>')}
                    <hr>
                    <small>
                        Confidence: ${(data.confidence * 100).toFixed(0)}% |
                        LLM: ${data.llm_used}
                    </small>
                </div>
            `;

            this.container.querySelector('.wisdom-feedback').classList.remove('d-none');

        } catch (e) {
            responseDiv.innerHTML = `<div class="alert alert-danger">Error: ${e.message}</div>`;
        }
    }

    async feedback(helpful) {
        if (!this.currentPredictionId) return;

        try {
            await fetch(`${WISDOM_API}/wisdom/feedback`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    prediction_id: this.currentPredictionId,
                    helpful: helpful,
                    accurate: helpful
                })
            });

            this.container.querySelector('.wisdom-feedback').innerHTML =
                '<small class="text-success">Thanks for the feedback!</small>';

            // Refresh accuracy
            this.loadHealth();

        } catch (e) {
            console.error('Feedback error:', e);
        }
    }
}

// Initialize when DOM ready
let wisdomWidget;
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('wisdom-container');
    if (container) {
        wisdomWidget = new WisdomWidget('wisdom-container');
    }
});