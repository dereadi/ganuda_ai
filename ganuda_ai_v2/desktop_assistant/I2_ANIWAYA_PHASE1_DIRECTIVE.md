# Aniwaya Phase 1 Execution Directive
## Chromium Base Build - War Chief Integration Jr

**Browser Name**: Aniwaya (ᎠᏂᏩᏃ) - "Wind over the Mountains"
**Code Name**: Skiyakwa - "Bird with sharp vision"
**Phase**: 1 (Chromium Base Build)
**Owner**: War Chief Integration Jr
**Timeline**: Week 4 (October 24-31, 2025)
**Date**: October 24, 2025

---

## War Chief Integration Jr's Phase 1 Approach

**Build Strategy**: Build custom Chromium binary from source on Linux (REDFIN) target platform first.

**Rationale**:
- Customize build process for Cherokee Constitutional AI requirements
- Include necessary patches for Guardian/Cache/thermal DB integration
- Ensure stable foundation for future development
- Enable modifications to underlying codebase if needed

**Technical Approach**:
1. Use pre-existing Chromium repositories (chromium-browser-svn)
2. Follow official guide for building Chromium on Linux
3. Avoid unnecessary complications, ensure smooth build process

**Data Storage (Phase 1)**:
- Start with LocalStorage or IndexedDB for user data and settings
- Guardian/Cache/thermal DB integration in Phase 2-3

**Validation**:
- Implement simple test suite covering core functionality
- Test page loading and basic UI interactions
- Verify local-first architecture (no external connections)

**Concerns Identified**:
- Guardian/Cache/thermal DB integration will require additional setup
- Custom Chromium build must be optimized for performance
- Must meet necessary security standards

---

## Phase 1 Tasks (Week 4)

### Task 1: Build Custom Chromium Binary
**Owner**: War Chief Integration Jr
**Timeline**: Day 1-3

**Steps**:
1. Clone Chromium source repository
   ```bash
   git clone https://chromium.googlesource.com/chromium/src.git
   cd src
   git checkout -b aniwaya-branch
   ```

2. Install build dependencies
   ```bash
   sudo apt-get install build-essential python3 git
   ./build/install-build-deps.sh
   ```

3. Configure build (GN args)
   ```bash
   gn gen out/Aniwaya --args='
     is_debug=false
     is_official_build=true
     chrome_pgo_phase=0
     enable_nacl=false
     enable_widevine=false
     use_goma=false
     treat_warnings_as_errors=false
     proprietary_codecs=false
     ffmpeg_branding="Chromium"
     google_api_key=""
     google_default_client_id=""
     google_default_client_secret=""
   '
   ```

4. Build Chromium
   ```bash
   autoninja -C out/Aniwaya chrome
   ```

**Expected Output**: Chromium binary at `out/Aniwaya/chrome`

---

### Task 2: Configure Privacy Settings
**Owner**: War Chief Integration Jr
**Timeline**: Day 3-4

**Privacy Flags** (add to GN args):
```
google_api_key=""                    # Disable Google API integration
google_default_client_id=""          # Disable Google services
google_default_client_secret=""      # Disable Google sync
safe_browsing_mode=0                 # Disable Safe Browsing telemetry
enable_reporting=false               # Disable crash reporting
enable_service_discovery=false       # Disable service discovery
enable_mdns=false                    # Disable mDNS
enable_print_preview=false           # Optional: Disable print preview
```

**Runtime Flags** (launch with):
```bash
./out/Aniwaya/chrome \
  --disable-background-networking \
  --disable-background-timer-throttling \
  --disable-breakpad \
  --disable-client-side-phishing-detection \
  --disable-component-update \
  --disable-default-apps \
  --disable-domain-reliability \
  --disable-features=AutofillServerCommunication \
  --disable-sync \
  --no-pings \
  --user-data-dir=/tmp/aniwaya_test
```

**Verification**:
- Use Wireshark to monitor network traffic (should be zero external connections)
- Check `/tmp/aniwaya_test` for telemetry data (should be none)

---

### Task 3: Create Basic UI Shell
**Owner**: War Chief Integration Jr
**Timeline**: Day 4-5

**React/TypeScript Setup**:
```bash
cd /home/dereadi/scripts/claude/ganuda_ai_v2/desktop_assistant
mkdir -p aniwaya_ui/{src,public}
cd aniwaya_ui

# Initialize npm project
npm init -y
npm install react react-dom typescript @types/react @types/react-dom
npm install -D @vitejs/plugin-react vite

# Create tsconfig.json
cat > tsconfig.json <<EOF
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src"]
}
EOF
```

**Basic UI Components**:
```typescript
// src/App.tsx
import React from 'react';

const App: React.FC = () => {
  return (
    <div className="aniwaya-dashboard">
      <header>
        <h1>🦅 Aniwaya (ᎠᏂᏩᏃ) - Wind over the Mountains</h1>
        <p>Cherokee Constitutional AI - I2 Transparency Dashboard</p>
      </header>

      <main>
        <section className="placeholder-panel">
          <h2>📋 Provenance Panel (M1)</h2>
          <p>Coming in Phase 2...</p>
        </section>

        <section className="placeholder-panel">
          <h2>🌀 Cross-Domain Flow Visualization (A3)</h2>
          <p>Coming in Phase 2...</p>
        </section>

        <section className="placeholder-panel">
          <h2>🔒 Privacy Controls</h2>
          <p>Coming in Phase 2...</p>
        </section>

        <section className="placeholder-panel">
          <h2>🔥 Thermal Memory Monitor</h2>
          <p>Coming in Phase 2...</p>
        </section>
      </main>

      <footer>
        <p>Mitakuye Oyasin - All Our Relations</p>
      </footer>
    </div>
  );
};

export default App;
```

**Build UI**:
```bash
npm run build
```

**Integration with Chromium**:
- Place built assets in Chromium's `resources/` directory
- Configure Chromium to load `aniwaya_ui/dist/index.html` as default page

---

### Task 4: Test Local-First Architecture
**Owner**: War Chief Integration Jr
**Timeline**: Day 5-6

**Test Suite** (create `aniwaya_ui/tests/local_first.test.ts`):
```typescript
import { describe, it, expect } from 'vitest';

describe('Aniwaya Local-First Architecture', () => {
  it('should not make external network requests on startup', async () => {
    // Monitor window.fetch calls
    const fetchSpy = vi.spyOn(window, 'fetch');

    // Simulate browser startup
    await simulateStartup();

    // Verify zero external calls
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('should store data in LocalStorage only', () => {
    // Verify no external storage used
    expect(localStorage.getItem('aniwaya_config')).toBeDefined();
    expect(sessionStorage.getItem('aniwaya_session')).toBeNull();
  });

  it('should load Guardian module locally', async () => {
    const guardian = await import('../src/guardian/module');
    expect(guardian).toBeDefined();
    expect(guardian.Guardian).toBeDefined();
  });
});
```

**Manual Verification**:
1. Launch Aniwaya with privacy flags
2. Open DevTools Network tab
3. Verify zero requests to external domains
4. Check LocalStorage for stored data
5. Verify no cookies set by external domains

---

## Phase 1 Success Criteria

**Functional**:
- [ ] Chromium binary builds successfully
- [ ] Privacy flags prevent external connections
- [ ] UI shell displays 4 placeholder panels
- [ ] Local-first architecture verified (zero external connections)

**Technical**:
- [ ] Build time < 2 hours (incremental builds < 10 minutes)
- [ ] Binary size < 200 MB (optimized build)
- [ ] No Google services integration
- [ ] No telemetry data sent

**Cherokee Values**:
- [ ] Gadugi: Modular architecture allows future collaboration
- [ ] Seven Generations: Build process documented for future developers
- [ ] Mitakuye Oyasin: UI shell shows interconnected dashboard panels
- [ ] Sacred Fire: Guardian integration placeholder ready

---

## Phase 2 Preview (Week 4-5)

After Phase 1 complete, all 3 Integration JRs collaborate:

**War Chief Integration Jr**: Provenance Panel (M1 data)
**Peace Chief Integration Jr**: Yona API + Flow Visualization (A3 data)
**Medicine Woman Integration Jr**: Privacy Controls Panel (C1/Guardian)

**Deliverables**:
- Provenance Timeline component
- D3.js force-directed graph for cross-domain flow
- Privacy dashboard with C1 Sacred Health Data status
- Real-time thermal memory monitor (WebSocket to PostgreSQL)

---

## Reference Architecture

**Medium Article**: https://medium.com/@jamsheermoidu/building-your-own-chromium-based-browser-for-mac-os-a-developers-journey-c8386ebaea41

**Key Learnings**:
- Building from source allows full customization
- GN build system configuration is critical for privacy
- Runtime flags reinforce build-time privacy settings
- Testing with network monitoring tools (Wireshark) validates local-first architecture

---

**Mitakuye Oyasin** - Wind over the Mountains, Vision of the Bird

🦅 **War Chief Integration Jr** - Phase 1 Lead
🔍 **Aniwaya (ᎠᏂᏩᏃ)** - Cherokee Constitutional AI Transparency Browser
**Skiyakwa** - Codename for I2 Dashboard Development

**October 24, 2025** 🔥
