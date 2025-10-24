// Aniwaya Background Service Worker
// War Chief Integration Jr - Guardian Bridge & Extension Management

console.log('🦅 Aniwaya background service worker started');

const GUARDIAN_API = 'http://localhost:8765';

// Extension installation handler
chrome.runtime.onInstalled.addListener(() => {
  console.log('🔥 Aniwaya installed - Cherokee Constitutional AI');
  console.log('Mitakuye Oyasin - All Our Relations');

  // Initialize extension storage
  chrome.storage.local.set({
    aniwayaVersion: '0.1.0',
    installed: new Date().toISOString(),
    thermalMonitorActive: true,
    guardianProtectionLevel: 'SACRED'
  });
});

// Message handler for dashboard → Guardian API communication
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('📨 Message received:', message.type);

  if (message.type === 'EVALUATE_QUERY') {
    // Evaluate query through Guardian
    evaluateWithGuardian(message.query)
      .then(result => sendResponse({success: true, data: result}))
      .catch(error => sendResponse({success: false, error: error.message}));

    return true; // Async response
  }

  if (message.type === 'FETCH_THERMAL_MEMORY') {
    // Fetch recent thermal memory data
    fetchThermalMemory()
      .then(data => sendResponse({success: true, data}))
      .catch(error => sendResponse({success: false, error: error.message}));

    return true; // Async response
  }

  if (message.type === 'REQUEST_DELETION') {
    // Handle user deletion request
    requestDataDeletion(message.entryId, message.userId)
      .then(result => sendResponse({success: true, data: result}))
      .catch(error => sendResponse({success: false, error: error.message}));

    return true; // Async response
  }
});

// Guardian API: Evaluate query
async function evaluateWithGuardian(query) {
  try {
    const response = await fetch(`${GUARDIAN_API}/evaluate`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query})
    });

    if (!response.ok) {
      throw new Error(`Guardian API error: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('🛡️  Guardian evaluation:', data);
    return data;
  } catch (error) {
    console.error('Guardian API connection failed:', error);
    // Fallback: basic PII detection
    return {
      allowed: !containsPII(query),
      protection_level: 'PRIVATE',
      redacted_content: query,
      offline: true
    };
  }
}

// Fetch thermal memory data from PostgreSQL
async function fetchThermalMemory() {
  try {
    const response = await fetch(`${GUARDIAN_API}/thermal/recent`, {
      method: 'GET'
    });

    if (!response.ok) {
      throw new Error(`Thermal API error: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('🔥 Thermal memory fetched:', data);
    return data;
  } catch (error) {
    console.error('Thermal API connection failed:', error);
    // Return placeholder data
    return {
      temperature: 85,
      phaseCoherence: 0.92,
      accessCount: 15,
      sacredFloor: 40,
      offline: true
    };
  }
}

// Request data deletion (respects HIPAA + 40° floor)
async function requestDataDeletion(entryId, userId) {
  try {
    const response = await fetch(`${GUARDIAN_API}/deletion/request`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({entryId, userId})
    });

    if (!response.ok) {
      throw new Error(`Deletion API error: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('🗑️  Deletion request:', data);
    return data;
  } catch (error) {
    console.error('Deletion API connection failed:', error);
    return {
      allowed: false,
      reason: 'API unavailable',
      offline: true
    };
  }
}

// Basic PII detection fallback (when Guardian API offline)
function containsPII(text) {
  const piiPatterns = [
    /\b\d{3}-\d{2}-\d{4}\b/,  // SSN
    /\b\d{3}-\d{3}-\d{4}\b/,  // Phone
    /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/  // Email
  ];

  return piiPatterns.some(pattern => pattern.test(text));
}

// Periodic thermal memory sync (every 30 seconds)
setInterval(async () => {
  const settings = await chrome.storage.local.get(['thermalMonitorActive']);

  if (settings.thermalMonitorActive) {
    const thermalData = await fetchThermalMemory();
    await chrome.storage.local.set({latestThermalData: thermalData});
    console.log('🔥 Thermal memory synced');
  }
}, 30000);

console.log('✅ Aniwaya background service worker ready');
