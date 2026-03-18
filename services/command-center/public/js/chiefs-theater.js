// Chiefs Deliberation Theater — AppRegistry version
// Replays council votes with animated timeline

(function() {
    const app = {
        id: 'chiefs-theater',
        title: 'Chiefs Theater',
        tags: ['chiefs', 'theater', 'deliberation', 'council', 'vote', 'governance'],
        _interval: null,

        open(savedPos) {
            if (WindowManager.exists(this.id)) {
                WindowManager.focus(this.id);
                return;
            }
            WindowManager.create({
                id: this.id,
                title: this.title,
                width: savedPos?.width || 900,
                height: savedPos?.height || 700,
                x: savedPos?.x || 150,
                y: savedPos?.y || 80,
                html: this.render(),
                onclose: () => this.cleanup()
            });
            this.loadLatestVote();
        },

        render() {
            return `<div class="wc-pad" style="height:100%;display:flex;flex-direction:column">
                <div class="wc-toolbar">
                    <h3 class="wc-heading">Chiefs Deliberation Theater</h3>
                    <button class="wc-btn" onclick="AppRegistry.get('chiefs-theater').loadLatestVote()">Latest Vote</button>
                </div>
                <p style="color:var(--text-muted);margin-bottom:12px">Watch tribal council deliberations replay</p>

                <!-- Council Chamber -->
                <div id="chiefs-council" style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:12px"></div>

                <!-- Timeline -->
                <div style="background:var(--bg-card);padding:12px;border-radius:6px;margin-bottom:12px">
                    <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                        <strong style="color:var(--accent)">Deliberation Timeline</strong>
                        <span id="ct-position" style="color:var(--text-muted)">Step 0 / 0</span>
                    </div>
                    <input type="range" id="ct-scrubber" min="0" max="0" value="0" style="width:100%"
                           onchange="AppRegistry.get('chiefs-theater').seekToStep(parseInt(this.value))">
                </div>

                <!-- Consensus -->
                <div style="background:var(--bg-card);padding:12px;border-radius:6px;margin-bottom:12px">
                    <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                        <strong style="color:var(--accent)">Consensus Level</strong>
                        <span id="ct-consensus" style="color:var(--good)">0%</span>
                    </div>
                    <div style="background:var(--bg-primary);height:16px;border-radius:8px;overflow:hidden">
                        <div id="ct-bar" style="width:0%;height:100%;background:linear-gradient(90deg,var(--accent),var(--good));transition:width 0.5s"></div>
                    </div>
                </div>

                <!-- Thought Chains -->
                <div id="ct-chains" style="flex:1;overflow-y:auto;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:12px">
                    <div class="wc-empty">Waiting for deliberation data...</div>
                </div>
            </div>`;
        },

        async loadLatestVote() {
            const chiefs = [
                {role: 'turtle', title: 'Turtle', icon: '&#129426;', color: '#4169E1'},
                {role: 'coyote', title: 'Coyote', icon: '&#129446;', color: '#FFD700'},
                {role: 'raven', title: 'Raven', icon: '&#129413;', color: '#9370DB'},
                {role: 'eagle_eye', title: 'Eagle Eye', icon: '&#129413;', color: '#FF8C00'},
                {role: 'spider', title: 'Spider', icon: '&#128376;', color: '#DC143C'}
            ];

            const council = document.getElementById('chiefs-council');
            if (!council) return;
            council.innerHTML = chiefs.map(c => `
                <div style="background:var(--bg-surface);border:2px solid ${c.color};border-radius:8px;padding:10px;text-align:center">
                    <div style="font-size:28px;margin-bottom:4px">${c.icon}</div>
                    <div style="color:${c.color};font-weight:700;font-size:12px">${c.title}</div>
                    <div id="chief-${c.role}-status" style="font-size:10px;color:var(--text-muted)">Silent</div>
                </div>
            `).join('');

            // Try to load real vote data from API
            let vote = null;
            try {
                const data = await FlowCore.api('/api/tribe/council-votes');
                const votes = data.votes || data || [];
                if (votes.length) vote = votes[0]; // most recent
            } catch (e) { /* fallback below */ }

            if (vote && vote.opinions) {
                this.replayVote(vote, chiefs);
            } else {
                this.replaySimulated(chiefs);
            }
        },

        replayVote(vote, chiefs) {
            const chains = document.getElementById('ct-chains');
            const scrubber = document.getElementById('ct-scrubber');
            const position = document.getElementById('ct-position');
            if (!chains) return;

            // Build steps from real vote opinions
            const steps = Object.entries(vote.opinions || {}).map(([role, opinion], i) => ({
                step: i + 1,
                chief: role,
                thought: typeof opinion === 'string' ? opinion : (opinion.reasoning || opinion.opinion || JSON.stringify(opinion)),
                confidence: opinion.confidence || vote.confidence || 0.5,
                vote: opinion.approve === false ? 'dissent' : 'approve'
            }));

            // Add consensus step
            steps.push({
                step: steps.length + 1,
                chief: 'consensus',
                thought: `Decision: ${vote.decision || 'PROCEED'}. Confidence: ${((vote.confidence || 0) * 100).toFixed(0)}%. Vote ID: ${(vote.vote_id || '').substring(0, 16)}`,
                confidence: vote.confidence || 0.5,
                vote: vote.decision === 'PROCEED' ? 'approve' : 'reject'
            });

            this.animateSteps(steps, chains, scrubber, position);
        },

        replaySimulated(chiefs) {
            const chains = document.getElementById('ct-chains');
            const scrubber = document.getElementById('ct-scrubber');
            const position = document.getElementById('ct-position');
            if (!chains) return;

            const steps = [
                { step: 1, chief: 'turtle', thought: 'Checking reversibility gates. Changes appear reversible — config-only, no schema migration. Approve with standard rollback window.', confidence: 0.90, vote: 'approve' },
                { step: 2, chief: 'coyote', thought: 'Sniffing for blind spots. What happens if the external API returns adversarial content? Valence gate needs injection sanitization.', confidence: 0.65, vote: 'dissent' },
                { step: 3, chief: 'raven', thought: 'Historical pattern check. Similar proposals succeeded 4/5 times. One failure was API rate limiting — ensure backoff strategy.', confidence: 0.80, vote: 'approve' },
                { step: 4, chief: 'eagle_eye', thought: 'Drift analysis: proposal aligns with DC-9 waste heat limits. Consultation budget stays within 20/hr cap.', confidence: 0.85, vote: 'approve' },
                { step: 5, chief: 'spider', thought: 'Web integrity check. Token map isolation verified — never crosses security boundary. PII scrub covers HIPAA identifiers.', confidence: 0.92, vote: 'approve' },
                { step: 6, chief: 'consensus', thought: 'Council consensus: PROCEED with Coyote condition — add input sanitization to valence gate. Confidence: 82%.', confidence: 0.82, vote: 'approve' }
            ];

            this.animateSteps(steps, chains, scrubber, position);
        },

        animateSteps(steps, chains, scrubber, position) {
            if (this._interval) clearInterval(this._interval);
            chains.innerHTML = '';
            if (scrubber) scrubber.max = steps.length - 1;
            this._steps = steps;
            this._currentStep = 0;

            const chiefColors = { turtle: '#4169E1', coyote: '#FFD700', raven: '#9370DB', eagle_eye: '#FF8C00', spider: '#DC143C', consensus: '#D2691E', crawdad: '#32CD32' };
            const chiefTitles = { turtle: 'Turtle', coyote: 'Coyote', raven: 'Raven', eagle_eye: 'Eagle Eye', spider: 'Spider', consensus: 'Tribal Consensus', crawdad: 'Crawdad' };

            this._interval = setInterval(() => {
                if (this._currentStep >= steps.length) {
                    clearInterval(this._interval);
                    this._interval = null;
                    return;
                }
                const step = steps[this._currentStep];
                const color = chiefColors[step.chief] || '#888';
                const title = chiefTitles[step.chief] || step.chief;
                const icon = step.vote === 'approve' ? '&#9989;' : step.vote === 'dissent' ? '&#9888;' : '&#128483;';

                chains.innerHTML += `<div style="margin-bottom:10px;padding:12px;background:var(--bg-surface);border-left:4px solid ${color};border-radius:4px">
                    <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                        <strong style="color:${color}">${icon} ${title}</strong>
                        <span style="color:var(--text-muted);font-size:12px">Confidence: ${(step.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div style="color:var(--text-secondary);line-height:1.5;font-size:13px">${step.thought}</div>
                </div>`;
                chains.scrollTop = chains.scrollHeight;

                if (scrubber) scrubber.value = this._currentStep;
                if (position) position.textContent = `Step ${this._currentStep + 1} / ${steps.length}`;

                // Update chief status
                const statusEl = document.getElementById(`chief-${step.chief}-status`);
                if (statusEl) { statusEl.textContent = 'Speaking...'; statusEl.style.color = 'var(--good)'; }

                // Update consensus bar
                const avg = steps.slice(0, this._currentStep + 1).reduce((s, st) => s + st.confidence, 0) / (this._currentStep + 1);
                const bar = document.getElementById('ct-bar');
                const cons = document.getElementById('ct-consensus');
                if (bar) bar.style.width = `${avg * 100}%`;
                if (cons) cons.textContent = `${(avg * 100).toFixed(0)}%`;

                this._currentStep++;
            }, 2000);
        },

        seekToStep(idx) {
            if (!this._steps) return;
            if (this._interval) clearInterval(this._interval);
            this._interval = null;
            const chains = document.getElementById('ct-chains');
            if (!chains) return;

            const chiefColors = { turtle: '#4169E1', coyote: '#FFD700', raven: '#9370DB', eagle_eye: '#FF8C00', spider: '#DC143C', consensus: '#D2691E', crawdad: '#32CD32' };
            const chiefTitles = { turtle: 'Turtle', coyote: 'Coyote', raven: 'Raven', eagle_eye: 'Eagle Eye', spider: 'Spider', consensus: 'Tribal Consensus', crawdad: 'Crawdad' };

            chains.innerHTML = '';
            for (let i = 0; i <= idx && i < this._steps.length; i++) {
                const step = this._steps[i];
                const color = chiefColors[step.chief] || '#888';
                const title = chiefTitles[step.chief] || step.chief;
                const icon = step.vote === 'approve' ? '&#9989;' : step.vote === 'dissent' ? '&#9888;' : '&#128483;';
                chains.innerHTML += `<div style="margin-bottom:10px;padding:12px;background:var(--bg-surface);border-left:4px solid ${color};border-radius:4px">
                    <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                        <strong style="color:${color}">${icon} ${title}</strong>
                        <span style="color:var(--text-muted);font-size:12px">Confidence: ${(step.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div style="color:var(--text-secondary);line-height:1.5;font-size:13px">${step.thought}</div>
                </div>`;
            }
            const position = document.getElementById('ct-position');
            if (position) position.textContent = `Step ${idx + 1} / ${this._steps.length}`;
        },

        cleanup() {
            if (this._interval) clearInterval(this._interval);
            this._interval = null;
        }
    };

    AppRegistry.register(app);
})();
