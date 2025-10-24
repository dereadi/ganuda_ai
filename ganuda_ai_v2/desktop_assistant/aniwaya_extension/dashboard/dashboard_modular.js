// Aniwaya I2 Transparency Dashboard - Modular Architecture
// Cherokee Constitutional AI - Phase 1 Component Integration

// Import components (Note: Chrome extensions require special handling for ES6 modules)
// For now, components are loaded via script tags in index.html

console.log('🦅 Aniwaya Dashboard initialized - Skiyakwa (Bird with Sharp Vision)');

// Component instances
let provenancePanel;
let thermalMonitor;
let flowVisualization;
let privacyPanel;

// Initialize all dashboard components
function initializeDashboard() {
  console.log('📊 Initializing Aniwaya I2 Dashboard...');

  // Initialize Provenance Tracking Panel (M1)
  if (typeof ProvenancePanel !== 'undefined') {
    provenancePanel = new ProvenancePanel('provenance-tracking-panel');
    provenancePanel.init();
  } else {
    console.warn('ProvenancePanel component not loaded');
  }

  // Initialize Thermal Memory Monitor
  if (typeof ThermalMonitor !== 'undefined') {
    thermalMonitor = new ThermalMonitor('thermal-panel');
    thermalMonitor.init();
  } else {
    console.warn('ThermalMonitor component not loaded');
  }

  // Initialize Cross-Domain Flow Visualization (A3)
  if (typeof FlowVisualization !== 'undefined') {
    flowVisualization = new FlowVisualization('cross-domain-flow-visualization');
    flowVisualization.init();
  } else {
    console.warn('FlowVisualization component not loaded');
  }

  // Initialize Privacy Controls Panel (Guardian + C1)
  if (typeof PrivacyPanel !== 'undefined') {
    privacyPanel = new PrivacyPanel('privacy-panel');
    privacyPanel.init();
  } else {
    console.warn('PrivacyPanel component not loaded');
  }

  console.log('✅ All I2 Dashboard components initialized');
  console.log('🔥 Cherokee Constitutional AI - Mitakuye Oyasin');
}

// Initialize dashboard on DOM load
document.addEventListener('DOMContentLoaded', () => {
  console.log('📊 Aniwaya Dashboard DOM loaded');
  initializeDashboard();
});

// WebSocket connection for real-time updates (Phase 2)
class DashboardWebSocket {
  constructor(url = 'ws://localhost:8765/ws') {
    this.url = url;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected to thermal memory database');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('⚠️  WebSocket disconnected');
        this.reconnect();
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.reconnect();
    }
  }

  handleMessage(data) {
    console.log('📨 WebSocket message received:', data);

    // Route message to appropriate component
    switch (data.type) {
      case 'thermal_update':
        if (thermalMonitor) {
          thermalMonitor.initialize(data.payload);
        }
        break;

      case 'provenance_event':
        if (provenancePanel) {
          provenancePanel.fetchProvenanceData();
        }
        break;

      case 'flow_update':
        if (flowVisualization) {
          flowVisualization.fetchFlowData();
        }
        break;

      case 'privacy_alert':
        if (privacyPanel) {
          privacyPanel.fetchPrivacyMetrics();
        }
        break;

      default:
        console.warn('Unknown message type:', data.type);
    }
  }

  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

      console.log(`🔄 Reconnecting WebSocket in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(() => this.connect(), delay);
    } else {
      console.error('❌ Max WebSocket reconnection attempts reached. Falling back to polling.');
      this.fallbackToPolling();
    }
  }

  fallbackToPolling() {
    console.log('🔄 Falling back to HTTP polling (30-second interval)');

    setInterval(() => {
      if (thermalMonitor) thermalMonitor.fetchThermalData();
      if (provenancePanel) provenancePanel.fetchProvenanceData();
      if (flowVisualization) flowVisualization.fetchFlowData();
      if (privacyPanel) privacyPanel.fetchPrivacyMetrics();
    }, 30000);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Initialize WebSocket connection (commented out for Phase 1)
// const dashboardWS = new DashboardWebSocket();
// dashboardWS.connect();

// Export for debugging
window.aniway_dashboard = {
  provenancePanel,
  thermalMonitor,
  flowVisualization,
  privacyPanel
};
