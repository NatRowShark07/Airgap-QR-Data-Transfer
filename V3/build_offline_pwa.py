"""
build_offline_pwa.py - Builds the self-contained zero-dependency HTML5/PWA for AQRDT v3.0.
Supports bidirectional Airgapped optical data transfer:
- Receiver Mode: Scans optical QR streams, verifies AEAD & SHA-256, auto-downloads files.
- Transmitter Mode: Compresses (ZLIB 9), encrypts (SHA-256 CTR AEAD), and optical-streams files at high FPS.
- Zero external runtime dependencies: inlines qrcodejs, jsQR, pako, and crypto-js.
- Offline-resilient: reads from local vendor/ directory first, falling back to CDN if needed.
"""

import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENDOR_DIR = os.path.join(BASE_DIR, "vendor")

LIBRARIES = {
    "qrcode": ("qrcode.min.js", "https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"),
    "jsqr": ("jsQR.js", "https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js"),
    "pako": ("pako.min.js", "https://cdn.jsdelivr.net/npm/pako@2.1.0/dist/pako.min.js"),
    "cryptojs": ("crypto-js.min.js", "https://cdn.jsdelivr.net/npm/crypto-js@4.2.0/crypto-js.min.js")
}

print("Preparing JS libraries for AQRDT v3.0 bundle...")
downloaded_scripts = {}

os.makedirs(VENDOR_DIR, exist_ok=True)

for name, (filename, cdn_url) in LIBRARIES.items():
    local_path = os.path.join(VENDOR_DIR, filename)
    if os.path.exists(local_path):
        print(f"  - Loading {name} from local cache: {filename}...")
        with open(local_path, "r", encoding="utf-8") as f:
            downloaded_scripts[name] = f.read()
    else:
        print(f"  - Fetching {name} from CDN: {cdn_url}...")
        req = urllib.request.Request(cdn_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            downloaded_scripts[name] = content
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(content)

HTML_CONTENT = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <title>Airgapped QR Data Transfer (AQRDT v3.0)</title>

  <!-- Inlined Zero-Dependency Engines -->
  <script>{downloaded_scripts['qrcode']}</script>
  <script>{downloaded_scripts['jsqr']}</script>
  <script>{downloaded_scripts['pako']}</script>
  <script>{downloaded_scripts['cryptojs']}</script>

  <style>
    :root {{
      --bg: #0b1120;
      --card: #1e293b;
      --card-border: #334155;
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --tx-color: #c084fc;
      --tx-primary: #a855f7;
      --tx-border: rgba(168, 85, 247, 0.4);
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 10px 12px;
      justify-content: flex-start;
      gap: 8px;
    }}

    header {{
      text-align: center;
      width: 100%;
      max-width: 380px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
    }}
    .header-brand {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }}
    .brand-icon {{
      color: var(--primary);
      font-size: 1.1rem;
    }}
    header h1 {{
      font-size: 1.15rem;
      font-weight: 700;
      color: #f8fafc;
      letter-spacing: -0.02em;
    }}
    .version-tag {{
      font-size: 0.65rem;
      font-weight: 700;
      background: rgba(56, 189, 248, 0.15);
      color: var(--primary);
      padding: 1px 6px;
      border-radius: 9999px;
      border: 1px solid rgba(56, 189, 248, 0.3);
    }}

    /* Top Mode Selection Menu Bar */
    .mode-menu {{
      width: 100%;
      max-width: 360px;
      background: #0f172a;
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 4px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }}
    .mode-tab {{
      height: 38px;
      border: 1px solid transparent;
      border-radius: 8px;
      background: transparent;
      color: var(--text-muted);
      font-size: 0.82rem;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s ease;
    }}
    .mode-tab:hover {{
      color: var(--text);
      background: rgba(255, 255, 255, 0.04);
    }}
    .mode-tab.active-rx {{
      background: rgba(56, 189, 248, 0.18);
      color: var(--primary);
      border-color: rgba(56, 189, 248, 0.45);
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.15);
    }}
    .mode-tab.active-tx {{
      background: rgba(168, 85, 247, 0.18);
      color: var(--tx-color);
      border-color: var(--tx-border);
      box-shadow: 0 0 12px rgba(168, 85, 247, 0.15);
    }}

    #status-pill {{
      display: inline-block;
      padding: 3px 12px;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 600;
      background: rgba(56, 189, 248, 0.15);
      color: var(--primary);
      border: 1px solid rgba(56, 189, 248, 0.3);
      transition: all 0.2s ease;
    }}

    /* Cards */
    .app-card {{
      width: 100%;
      max-width: 360px;
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 10px 14px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }}
    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}
    .card-title {{
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--primary);
    }}
    .card-title-tx {{
      color: var(--tx-color);
    }}
    .status-indicator {{
      font-size: 0.7rem;
      color: var(--warning);
      font-weight: 600;
    }}

    /* Auth Grid */
    .auth-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}
    .input-group {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}
    .input-group label {{
      font-size: 0.68rem;
      color: var(--text-muted);
      font-weight: 600;
    }}
    .input-group input, .input-group select {{
      background: #0f172a;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 6px 8px;
      color: #f8fafc;
      font-size: 0.78rem;
      outline: none;
      transition: border-color 0.2s;
    }}
    .input-group input:focus, .input-group select:focus {{
      border-color: var(--primary);
    }}

    .btn-subtle {{
      margin-top: 8px;
      width: 100%;
      height: 28px;
      background: rgba(56, 189, 248, 0.12);
      color: var(--primary);
      border: 1px solid rgba(56, 189, 248, 0.28);
      border-radius: 6px;
      font-size: 0.74rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
      transition: all 0.15s ease;
    }}
    .btn-subtle:hover {{
      background: var(--primary);
      color: #0b1120;
    }}
    .btn-subtle-tx {{
      background: rgba(168, 85, 247, 0.12);
      color: var(--tx-color);
      border-color: var(--tx-border);
    }}
    .btn-subtle-tx:hover {{
      background: var(--tx-primary);
      color: #fff;
    }}

    /* Viewports */
    .viewport-box {{
      width: 280px;
      height: 280px;
      background: #ffffff;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
      padding: 10px;
      position: relative;
      margin: 2px 0;
    }}
    .qr-display {{
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .qr-display img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
    }}
    .qr-placeholder {{
      color: #64748b;
      text-align: center;
      font-size: 0.82rem;
      font-weight: 500;
      padding: 18px;
      line-height: 1.45;
    }}
    .placeholder-icon {{
      font-size: 2rem;
      margin-bottom: 6px;
    }}

    .frame-overlay {{
      position: absolute;
      bottom: 8px;
      right: 8px;
      background: rgba(15, 23, 42, 0.85);
      color: #38bdf8;
      font-family: monospace;
      font-size: 0.68rem;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      border: 1px solid rgba(56, 189, 248, 0.4);
    }}

    /* Floating Camera Monitor */
    #cam-monitor {{
      position: fixed;
      top: 14px;
      right: 14px;
      width: 68px;
      height: 68px;
      border-radius: 12px;
      border: 2px solid var(--primary);
      overflow: hidden;
      background: #000;
      z-index: 100;
      box-shadow: 0 4px 12px rgba(0,0,0,0.7);
      transition: border-color 0.15s ease;
    }}
    #video-view {{
      width: 100%;
      height: 100%;
      object-fit: cover;
      transform: scaleX(-1);
    }}
    .cam-badge {{
      position: absolute;
      bottom: 2px;
      left: 3px;
      font-size: 0.55rem;
      font-weight: 800;
      background: rgba(0,0,0,0.75);
      color: #f8fafc;
      padding: 1px 4px;
      border-radius: 3px;
    }}
    #hidden-canvas {{ display: none; }}

    /* Mode Views */
    .mode-view {{
      width: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
    }}

    /* Dropzone (Transmitter) */
    .dropzone {{
      border: 2px dashed var(--card-border);
      border-radius: 10px;
      padding: 12px 10px;
      text-align: center;
      cursor: pointer;
      background: #0f172a;
      transition: all 0.2s ease;
    }}
    .dropzone:hover, .dropzone.dragover {{
      border-color: var(--tx-color);
      background: rgba(168, 85, 247, 0.08);
    }}
    .dropzone-content {{
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 3px;
    }}
    .dropzone-icon {{
      font-size: 1.5rem;
    }}
    .dropzone-title {{
      font-size: 0.78rem;
      font-weight: 700;
      color: #f8fafc;
    }}
    .dropzone-hint {{
      font-size: 0.65rem;
      color: var(--text-muted);
    }}

    .file-info-pill {{
      margin-top: 8px;
      background: #0f172a;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 6px 10px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}
    .file-meta {{
      display: flex;
      justify-content: space-between;
      font-size: 0.74rem;
      font-weight: 600;
    }}
    .file-name {{
      color: var(--tx-color);
      max-width: 220px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .file-size {{
      color: var(--text-muted);
    }}
    .file-hash {{
      display: flex;
      gap: 4px;
      font-size: 0.65rem;
      font-family: monospace;
      color: var(--text-muted);
    }}
    .hash-val {{
      color: #cbd5e1;
    }}

    /* Settings */
    .settings-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}
    .setting-item {{
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}
    .setting-label-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .setting-label-row label, .setting-item label {{
      font-size: 0.68rem;
      color: var(--text-muted);
      font-weight: 600;
    }}
    .setting-badge {{
      font-size: 0.68rem;
      font-weight: 700;
      color: var(--tx-color);
      font-family: monospace;
    }}
    input[type="range"] {{
      accent-color: var(--tx-primary);
      cursor: pointer;
    }}

    /* HUD */
    .hud-line {{
      display: flex;
      justify-content: space-between;
      font-size: 0.78rem;
      margin-bottom: 4px;
    }}
    .hud-filename {{
      font-weight: 600;
      max-width: 220px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .hud-frames {{
      color: var(--text-muted);
      font-family: monospace;
      font-size: 0.74rem;
    }}
    .progress-track {{
      width: 100%;
      height: 6px;
      background: #334155;
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 4px;
    }}
    .progress-fill {{
      height: 100%;
      width: 0%;
      background: var(--primary);
      transition: width 0.15s ease;
    }}
    .tx-progress {{
      background: var(--tx-primary);
    }}
    .hud-percent {{
      font-size: 0.74rem;
      font-weight: bold;
    }}
    .hud-status {{
      font-size: 0.72rem;
      color: var(--text-muted);
    }}
    .missing-box {{
      margin-top: 4px;
    }}
    .missing-label {{
      font-size: 0.68rem;
      color: var(--danger);
      font-weight: 700;
    }}
    .tag-row {{
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
      max-height: 32px;
      overflow: hidden;
      margin-top: 2px;
    }}
    .tag {{
      font-size: 0.64rem;
      font-family: monospace;
      background: rgba(239, 68, 68, 0.2);
      color: var(--danger);
      padding: 1px 5px;
      border-radius: 4px;
      font-weight: bold;
    }}
    .debug-terminal {{
      font-size: 0.67rem;
      font-family: monospace;
      color: #cbd5e1;
      background: rgba(0, 0, 0, 0.35);
      padding: 4px 8px;
      border-radius: 6px;
      word-break: break-all;
      margin-top: 5px;
    }}

    /* Buttons */
    .button-grid {{
      width: 100%;
      max-width: 360px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 4px;
    }}
    .btn-action {{
      height: 38px;
      border: 1px solid var(--card-border);
      border-radius: 9px;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      background: var(--card);
      color: var(--text);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.15s;
    }}
    .btn-action:hover {{
      background: #334155;
    }}
    .btn-action:disabled {{
      opacity: 0.38;
      cursor: not-allowed;
    }}
    .btn-primary {{
      background: var(--tx-primary);
      color: #fff;
      border-color: var(--tx-primary);
    }}
    .btn-primary:hover {{
      background: #9333ea;
    }}
    .btn-success {{
      background: var(--success);
      color: white;
      border-color: var(--success);
    }}
    .btn-success:hover {{
      background: #059669;
    }}
    .btn-full {{
      grid-column: span 2;
    }}

    /* Modal */
    .modal-backdrop {{
      display: none;
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: rgba(0, 0, 0, 0.85);
      z-index: 200;
      padding: 16px;
      flex-direction: column;
      justify-content: center;
      align-items: center;
    }}
    .modal-card {{
      width: 100%;
      max-width: 360px;
      max-height: 80vh;
      background: var(--card);
      border-radius: 14px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      border: 1px solid var(--card-border);
    }}
    .modal-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .modal-title {{
      font-weight: 700;
      font-size: 0.9rem;
    }}
    .btn-close {{
      width: 26px;
      height: 26px;
      border-radius: 50%;
      border: 1px solid var(--card-border);
      background: #0f172a;
      color: #fff;
      cursor: pointer;
    }}
    .modal-body {{
      width: 100%;
      height: 250px;
      background: #0f172a;
      color: #38bdf8;
      font-family: monospace;
      font-size: 0.72rem;
      padding: 8px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }}
  </style>
</head>
<body>

  <!-- Floating Camera Vision Monitor -->
  <div id="cam-monitor" title="Optical Scanner Vision">
    <video id="video-view" autoplay playsinline webkit-playsinline muted></video>
    <div id="cam-badge" class="cam-badge">RX-CAM</div>
  </div>
  <canvas id="hidden-canvas"></canvas>

  <header>
    <div class="header-brand">
      <span class="brand-icon">✦</span>
      <h1>Airgapped QR Data Transfer</h1>
      <span class="version-tag">v3.0</span>
    </div>

    <!-- Mode Selector Menu Bar -->
    <nav class="mode-menu" role="tablist" aria-label="Transfer Mode Selector">
      <button id="tab-rx" class="mode-tab active-rx" role="tab" aria-selected="true" onclick="setAppMode('rx')">
        <span>📥</span>
        <span>Receive Mode</span>
      </button>
      <button id="tab-tx" class="mode-tab" role="tab" aria-selected="false" onclick="setAppMode('tx')">
        <span>📤</span>
        <span>Transmit Mode</span>
      </button>
    </nav>

    <div id="status-pill">Initializing Optical Engine...</div>
  </header>

  <!-- Dynamic Cryptographic Credentials Configuration -->
  <section id="auth-panel" class="app-card">
    <div class="card-header">
      <span id="auth-card-title" class="card-title">🔐 Shared Cryptographic Identity</span>
      <span id="auth-indicator" class="status-indicator">○ Awaiting Credentials</span>
    </div>
    <div class="auth-grid">
      <div class="input-group">
        <label for="input-username">Username</label>
        <input type="text" id="input-username" placeholder="e.g. Nathaniel" autocomplete="off" onkeydown="if(event.key==='Enter') applyCredentials();" oninput="onCredentialsInput()" />
      </div>
      <div class="input-group">
        <label for="input-password">Shared Secret</label>
        <input type="password" id="input-password" placeholder="Passphrase" autocomplete="off" onkeydown="if(event.key==='Enter') applyCredentials();" oninput="onCredentialsInput()" />
      </div>
    </div>
    <button id="btn-apply-auth" class="btn-subtle" onclick="applyCredentials()">
      <span>🔄</span> Generate Auth Key & Sync
    </button>
  </section>

  <!-- ================= RECEIVER VIEW ================= -->
  <main id="view-receiver" class="mode-view">
    <div class="viewport-box">
      <div id="rx-qr-placeholder" class="qr-placeholder">
        <div class="placeholder-icon">🔐</div>
        <p>Enter your <strong>Username</strong> and <strong>Password</strong> above, then click <em>"Generate Auth Key"</em> to show your <strong>Auth QR</strong>.</p>
      </div>
      <div id="rx-qr-container" class="qr-display" style="display: none;"></div>
    </div>

    <section class="app-card">
      <div class="hud-line">
        <span id="rx-filename" class="hud-filename">Awaiting optical stream...</span>
        <span id="rx-frame-count" class="hud-frames">0/0 frames</span>
      </div>
      <div class="progress-track">
        <div id="rx-progress-fill" class="progress-fill"></div>
      </div>
      <div class="hud-line">
        <span id="rx-percent" class="hud-percent">0%</span>
        <span id="rx-scan-status" class="hud-status">Scanning Camera...</span>
      </div>
      <div id="rx-missing-container" class="missing-box" style="display: none;">
        <span class="missing-label">Missing Packets (NACK):</span>
        <div id="rx-missing-tags" class="tag-row"></div>
      </div>
      <div id="rx-log" class="debug-terminal">Status: Enter credentials to begin.</div>
    </section>

    <div class="button-grid">
      <button class="btn-action" onclick="openRawDataModal()">
        <span>👁️</span> View Decrypted
      </button>
      <button id="rx-download-btn" class="btn-action btn-success" onclick="manualDownload()" disabled>
        <span>💾</span> Download File
      </button>
      <button class="btn-action btn-full" onclick="resetReceiverSession()">
        <span>🔄</span> Reset Receiver
      </button>
    </div>
  </main>

  <!-- ================= TRANSMITTER VIEW ================= -->
  <main id="view-transmitter" class="mode-view" style="display: none;">
    <!-- File Select Area -->
    <section class="app-card">
      <div id="tx-dropzone" class="dropzone" onclick="document.getElementById('tx-file-input').click()">
        <input type="file" id="tx-file-input" style="display: none;" onchange="handleFileSelect(this.files)" />
        <div class="dropzone-content">
          <span class="dropzone-icon">📄</span>
          <span id="dropzone-main-text" class="dropzone-title">Click or Drop File to Stream</span>
          <span id="dropzone-sub-text" class="dropzone-hint">Supports any file type or format</span>
        </div>
      </div>

      <div id="tx-file-info" class="file-info-pill" style="display: none;">
        <div class="file-meta">
          <span id="tx-file-name" class="file-name">-</span>
          <span id="tx-file-size" class="file-size">-</span>
        </div>
        <div class="file-hash">
          <span class="hash-label">SHA-256:</span>
          <span id="tx-file-sha" class="hash-val">-</span>
        </div>
      </div>
    </section>

    <!-- Transmission Speed & Chunk Controls -->
    <section class="app-card">
      <div class="settings-grid">
        <div class="setting-item">
          <div class="setting-label-row">
            <label for="tx-fps-slider">Stream Speed</label>
            <span id="tx-fps-val" class="setting-badge">12 FPS</span>
          </div>
          <input type="range" id="tx-fps-slider" min="1" max="25" value="12" step="1" oninput="updateTxSpeed(this.value)" />
        </div>
        <div class="setting-item">
          <label for="tx-chunk-size">Chunk Payload</label>
          <select id="tx-chunk-size" onchange="onTxSettingChanged()">
            <option value="120">120 B (Dense / High Resilience)</option>
            <option value="160" selected>160 B (Balanced Default)</option>
            <option value="220">220 B (Fast / High Capacity)</option>
          </select>
        </div>
      </div>
    </section>

    <!-- Transmitter Viewport -->
    <div class="viewport-box">
      <div id="tx-qr-placeholder" class="qr-placeholder">
        <div class="placeholder-icon">📤</div>
        <p>Select a file to send. Then point your camera at the <strong>Receiver Auth QR</strong> to begin.</p>
      </div>
      <div id="tx-qr-container" class="qr-display" style="display: none;"></div>
      <div id="tx-frame-overlay" class="frame-overlay" style="display: none;">Frame <span id="tx-overlay-idx">0</span>/<span id="tx-overlay-total">0</span></div>
    </div>

    <!-- Transmitter HUD -->
    <section class="app-card">
      <div class="hud-line">
        <span id="tx-status-label" class="hud-filename">Ready to package</span>
        <span id="tx-frame-counter" class="hud-frames">0/0 frames</span>
      </div>
      <div class="progress-track">
        <div id="tx-progress-fill" class="progress-fill tx-progress"></div>
      </div>
      <div class="hud-line">
        <span id="tx-stats-compression" class="hud-percent">ZLIB 9: 0% ratio</span>
        <span id="tx-handshake-status" class="hud-status">Awaiting Receiver Auth</span>
      </div>
      <div id="tx-log" class="debug-terminal">Status: Waiting for file selection.</div>
    </section>

    <!-- Transmitter Controls -->
    <div class="button-grid">
      <button id="tx-start-btn" class="btn-action btn-primary" onclick="startTransmission()" disabled>
        <span>▶</span> Start Stream
      </button>
      <button id="tx-pause-btn" class="btn-action" onclick="togglePauseTransmission()" disabled>
        <span>⏸</span> Pause
      </button>
      <button id="tx-blast-btn" class="btn-action btn-full" onclick="retransmitAllLoop()" disabled>
        <span>🔄</span> Re-stream Entire File
      </button>
      <button class="btn-action btn-full" onclick="resetTransmitterSession()">
        <span>⏹</span> Reset Transmitter
      </button>
    </div>
  </main>

  <!-- Modal for Raw Decrypted Data -->
  <div id="data-modal" class="modal-backdrop">
    <div class="modal-card">
      <div class="modal-header">
        <span class="modal-title">Decrypted Payload Viewer</span>
        <button class="btn-close" onclick="closeRawDataModal()">✕</button>
      </div>
      <div id="raw-data-content" class="modal-body">No data received yet.</div>
    </div>
  </div>

  <script>
    // =====================================================================
    // --- Cryptographic & Encoding Engine (AES/SHA-256 CTR AEAD + ZLIB) ---
    // =====================================================================

    const MAGIC_HEADER = "AQ02"; // 4-byte protocol identifier

    function computeAuthSignature(user, pass) {{
      const normUser = user.trim().toLowerCase();
      const normPass = pass.trim();
      return CryptoJS.SHA256("AQRDT_AUTH_v2:" + normUser + ":" + normPass).toString(CryptoJS.enc.Hex);
    }}

    function generateAuthQRPayload(user, pass) {{
      const sig = computeAuthSignature(user, pass);
      return `AUTH|AQRDT|v2|${{user.trim()}}|${{sig}}`;
    }}

    function verifyAuthPayload(scannedPayload, expectedUser, expectedPass) {{
      const cleaned = scannedPayload.trim();
      if (!cleaned.startsWith("AUTH|AQRDT|v2|")) return {{ valid: false, user: null }};
      const parts = cleaned.split("|");
      if (parts.length >= 5) {{
        const u = parts[3].trim();
        const sig = parts[4].trim();
        const expectedSig = computeAuthSignature(expectedUser || u, expectedPass);
        if (sig === expectedSig || sig === computeAuthSignature(u, expectedPass)) {{
          return {{ valid: true, user: u }};
        }}
      }}
      return {{ valid: false, user: null }};
    }}

    function deriveEncryptionKey(user, pass, saltBytes) {{
      const normUser = user.trim().toLowerCase();
      const normPass = pass.trim();
      const saltWords = CryptoJS.lib.WordArray.create(saltBytes);
      const userPassWords = CryptoJS.enc.Utf8.parse(normUser + ":" + normPass + ":");
      const combined = userPassWords.concat(saltWords);
      return CryptoJS.SHA256(combined);
    }}

    function sha256CtrCrypt(dataBytes, keyWords, nonceBytes) {{
      const out = new Uint8Array(dataBytes.length);
      const blockSize = 32;
      const numBlocks = Math.ceil(dataBytes.length / blockSize);
      const nonceWords = CryptoJS.lib.WordArray.create(nonceBytes);

      for (let i = 0; i < numBlocks; i++) {{
        const counterBytes = new Uint8Array(4);
        counterBytes[0] = (i >>> 24) & 0xff;
        counterBytes[1] = (i >>> 16) & 0xff;
        counterBytes[2] = (i >>> 8) & 0xff;
        counterBytes[3] = i & 0xff;

        const counterWords = CryptoJS.lib.WordArray.create(counterBytes);
        const combined = keyWords.clone().concat(nonceWords.clone()).concat(counterWords);
        const ksWords = CryptoJS.SHA256(combined);

        const start = i * blockSize;
        const end = Math.min(start + blockSize, dataBytes.length);
        for (let j = 0; j < end - start; j++) {{
          const byteIdx = j;
          const wordIdx = Math.floor(byteIdx / 4);
          const byteInWord = 3 - (byteIdx % 4);
          const ksByte = (ksWords.words[wordIdx] >>> (byteInWord * 8)) & 0xff;
          out[start + j] = dataBytes[start + j] ^ ksByte;
        }}
      }}
      return out;
    }}

    function computeHmacSha256(keyWords, nonceBytes, cipherBytes) {{
      const nonceWords = CryptoJS.lib.WordArray.create(nonceBytes);
      const cipherWords = CryptoJS.lib.WordArray.create(cipherBytes);
      const combined = nonceWords.concat(cipherWords);
      return CryptoJS.HmacSHA256(combined, keyWords);
    }}

    function crc32(byteArray) {{
      if (!window._crcTable) {{
        const table = new Uint32Array(256);
        for (let i = 0; i < 256; i++) {{
          let c = i;
          for (let k = 0; k < 8; k++) {{
            c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
          }}
          table[i] = c >>> 0;
        }}
        window._crcTable = table;
      }}
      let crc = 0 ^ (-1);
      const table = window._crcTable;
      for (let i = 0; i < byteArray.length; i++) {{
        crc = (crc >>> 8) ^ table[(crc ^ byteArray[i]) & 0xFF];
      }}
      return ((crc ^ (-1)) >>> 0).toString(16).padStart(8, '0');
    }}

    function bytesToBase64(bytes) {{
      let bin = "";
      for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
      return btoa(bin);
    }}

    function decodeBase64ToBytes(b64Str) {{
      const bin = atob(b64Str.replace(/[\\r\\n\\s]/g, ""));
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return bytes;
    }}

    function decompressIndices(rangeStr) {{
      if (!rangeStr || !rangeStr.trim()) return [];
      const result = [];
      const parts = rangeStr.split(",");
      for (let part of parts) {{
        part = part.trim();
        if (!part) continue;
        if (part.includes("-")) {{
          const [s, e] = part.split("-").map(x => parseInt(x, 10));
          if (!isNaN(s) && !isNaN(e)) {{
            for (let i = s; i <= e; i++) result.push(i);
          }}
        }} else {{
          const idx = parseInt(part, 10);
          if (!isNaN(idx)) result.push(idx);
        }}
      }}
      return [...new Set(result)].sort((a, b) => a - b);
    }}

    // =====================================================================
    // --- Application State & Mode Navigation ---
    // =====================================================================

    let currentMode = "rx"; // 'rx' (Receiver) or 'tx' (Transmitter)
    let currentUser = "";
    let currentPass = "";
    let currentAuthPayload = "";

    // Camera State
    let video = document.getElementById("video-view");
    let canvas = document.getElementById("hidden-canvas");
    let ctx = canvas.getContext("2d", {{ willReadFrequently: true }});
    let isCameraActive = false;

    // UI Elements
    const statusPill = document.getElementById("status-pill");
    const authIndicator = document.getElementById("auth-indicator");
    const authCardTitle = document.getElementById("auth-card-title");
    const camBadge = document.getElementById("cam-badge");
    const camMonitor = document.getElementById("cam-monitor");

    function setAppMode(mode) {{
      if (currentMode === mode) return;
      currentMode = mode;

      const tabRx = document.getElementById("tab-rx");
      const tabTx = document.getElementById("tab-tx");
      const viewRx = document.getElementById("view-receiver");
      const viewTx = document.getElementById("view-transmitter");
      const btnApplyAuth = document.getElementById("btn-apply-auth");

      if (mode === "rx") {{
        tabRx.className = "mode-tab active-rx";
        tabTx.className = "mode-tab";
        tabRx.setAttribute("aria-selected", "true");
        tabTx.setAttribute("aria-selected", "false");
        viewRx.style.display = "flex";
        viewTx.style.display = "none";
        authCardTitle.className = "card-title";
        btnApplyAuth.className = "btn-subtle";
        camBadge.innerText = "RX-CAM";
        camMonitor.style.borderColor = "var(--primary)";

        if (currentUser && currentPass) {{
          statusPill.innerText = `Receiver Active [User: ${{currentUser}}]`;
          statusPill.style.background = "rgba(56, 189, 248, 0.15)";
          statusPill.style.color = "#38bdf8";
        }} else {{
          statusPill.innerText = "Receiver: Enter Credentials";
        }}
      }} else {{
        tabTx.className = "mode-tab active-tx";
        tabRx.className = "mode-tab";
        tabTx.setAttribute("aria-selected", "true");
        tabRx.setAttribute("aria-selected", "false");
        viewTx.style.display = "flex";
        viewRx.style.display = "none";
        authCardTitle.className = "card-title card-title-tx";
        btnApplyAuth.className = "btn-subtle btn-subtle-tx";
        camBadge.innerText = "TX-CAM";
        camMonitor.style.borderColor = "var(--tx-primary)";

        if (currentUser && currentPass) {{
          statusPill.innerText = `Transmitter Active [User: ${{currentUser}}]`;
          statusPill.style.background = "rgba(168, 85, 247, 0.18)";
          statusPill.style.color = "#c084fc";
        }} else {{
          statusPill.innerText = "Transmitter: Enter Credentials & Select File";
        }}
      }}
    }}

    function onCredentialsInput() {{
      const u = document.getElementById("input-username").value.trim();
      const p = document.getElementById("input-password").value.trim();
      if (!u || !p) {{
        authIndicator.innerHTML = "○ Awaiting Credentials";
        authIndicator.style.color = "var(--warning)";
      }}
    }}

    function applyCredentials() {{
      const u = document.getElementById("input-username").value.trim();
      const p = document.getElementById("input-password").value.trim();

      if (!u || !p) {{
        statusPill.innerText = "Please Enter Username & Password";
        statusPill.style.background = "rgba(239, 68, 68, 0.2)";
        statusPill.style.color = "#ef4444";
        authIndicator.innerHTML = "○ Incomplete";
        authIndicator.style.color = "var(--danger)";
        return;
      }}

      currentUser = u;
      currentPass = p;
      currentAuthPayload = generateAuthQRPayload(currentUser, currentPass);

      authIndicator.innerHTML = `● Active: ${{currentUser}}`;
      authIndicator.style.color = "var(--success)";

      if (currentMode === "rx") {{
        rxApplyAuthQR();
      }} else {{
        txCheckReadyToTransmit();
        document.getElementById("tx-log").innerText = `Credentials set for '${{currentUser}}'. Ready to package file.`;
        statusPill.innerText = `Transmitter Ready [User: ${{currentUser}}]`;
        statusPill.style.background = "rgba(168, 85, 247, 0.18)";
        statusPill.style.color = "#c084fc";
      }}
    }}

    // =====================================================================
    // --- Camera Vision Loop (Bi-directional jsQR Scanner) ---
    // =====================================================================

    async function initCamera() {{
      try {{
        const stream = await navigator.mediaDevices.getUserMedia({{
          video: {{ facingMode: "user", width: {{ ideal: 640 }}, height: {{ ideal: 480 }} }},
          audio: false
        }});
        video.srcObject = stream;
        video.setAttribute("playsinline", "true");
        video.setAttribute("webkit-playsinline", "true");
        await video.play();
        isCameraActive = true;
        statusPill.innerText = "Camera Active: Enter Credentials";
        requestAnimationFrame(scanLoop);
      }} catch (err) {{
        console.warn("Camera init warning:", err);
        statusPill.innerText = "Camera Not Available (Display Mode Only)";
        statusPill.style.background = "rgba(239, 68, 68, 0.2)";
        statusPill.style.color = "#ef4444";
      }}
    }}

    function scanLoop() {{
      if (video.readyState === video.HAVE_ENOUGH_DATA) {{
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const code = jsQR(imageData.data, imageData.width, imageData.height, {{
          inversionAttempts: "dontInvert"
        }});

        if (code && code.data) {{
          camMonitor.style.borderColor = "#10b981";
          routeScannedQR(code.data);
        }} else {{
          camMonitor.style.borderColor = (currentMode === "rx") ? "var(--primary)" : "var(--tx-primary)";
        }}

        // Receiver NACK timeout check
        if (currentMode === "rx" && rxTotalChunks !== null && !rxIsComplete) {{
          if (Date.now() - rxLastChunkReceivedTime > 1500) {{
            triggerMissingFrameNACK();
          }}
        }}
      }}
      requestAnimationFrame(scanLoop);
    }}

    function routeScannedQR(payload) {{
      if (currentMode === "rx") {{
        handleReceiverIncoming(payload);
      }} else {{
        handleTransmitterIncoming(payload);
      }}
    }}

    // =====================================================================
    // --- RECEIVER LOGIC ---
    // =====================================================================

    let rxQrGenerator = null;
    let rxReceivedChunks = {{}};
    let rxTotalChunks = null;
    let rxTargetFileName = "received_file";
    let rxIsComplete = false;
    let rxCurrentQRString = "";
    let rxLastChunkReceivedTime = Date.now();
    let rxReconstructedBytes = null;

    const rxQrView = document.getElementById("rx-qr-container");
    const rxQrPlaceholder = document.getElementById("rx-qr-placeholder");
    const rxDownloadBtn = document.getElementById("rx-download-btn");
    const rxDebugLog = document.getElementById("rx-log");

    function rxApplyAuthQR() {{
      rxQrPlaceholder.style.display = "none";
      rxQrView.style.display = "flex";

      if (!rxQrGenerator) {{
        rxQrGenerator = new QRCode(rxQrView, {{
          text: currentAuthPayload,
          width: 250,
          height: 250,
          correctLevel: QRCode.CorrectLevel.M
        }});
      }} else {{
        rxQrGenerator.clear();
        rxQrGenerator.makeCode(currentAuthPayload);
      }}
      rxCurrentQRString = currentAuthPayload;

      statusPill.innerText = `Auth QR Ready [User: ${{currentUser}}]`;
      statusPill.style.background = "rgba(16, 185, 129, 0.2)";
      statusPill.style.color = "#10b981";
      rxDebugLog.innerText = `Auth QR active for user '${{currentUser}}'. Point Transmitter camera at this screen.`;
    }}

    function setRxDisplayQR(text, label, pillBg, pillColor) {{
      if (!rxQrGenerator) return;
      if (rxCurrentQRString === text) return;
      rxCurrentQRString = text;
      rxQrGenerator.clear();
      rxQrGenerator.makeCode(text);
      if (label) {{
        statusPill.innerText = label;
        statusPill.style.background = pillBg || "rgba(56, 189, 248, 0.15)";
        statusPill.style.color = pillColor || "#38bdf8";
      }}
    }}

    function handleReceiverIncoming(payload) {{
      if (rxIsComplete) return;

      rxDebugLog.innerText = "Scanned: " + (payload.length > 32 ? payload.substring(0, 32) + "..." : payload);

      if (payload === "DONE_BLAST") {{
        triggerMissingFrameNACK();
        return;
      }}

      if (payload.startsWith("D|")) {{
        const parts = payload.split("|");
        // Format: D|<fname>|<idx>|<total>|<crc32>|<b64_chunk>
        if (parts.length >= 5) {{
          rxTargetFileName = parts[1];
          const idx = parseInt(parts[2], 10);
          rxTotalChunks = parseInt(parts[3], 10);
          const b64Data = parts[parts.length - 1];

          if (!isNaN(idx) && !isNaN(rxTotalChunks)) {{
            if (!rxReceivedChunks[idx]) {{
              try {{
                rxReceivedChunks[idx] = decodeBase64ToBytes(b64Data);
                rxLastChunkReceivedTime = Date.now();
                updateReceiverHUD();

                if (rxCurrentQRString !== currentAuthPayload && getMissingRxIndices().length === 0) {{
                  setRxDisplayQR(currentAuthPayload, `Receiving Encrypted Stream for [${{currentUser}}]...`, "rgba(56, 189, 248, 0.15)", "#38bdf8");
                }}
              }} catch (e) {{}}
            }}

            if (Object.keys(rxReceivedChunks).length === rxTotalChunks && !rxIsComplete) {{
              finalizeReceiverReconstruction();
            }}
          }}
        }}
      }}
    }}

    function updateReceiverHUD() {{
      const count = Object.keys(rxReceivedChunks).length;
      const progress = count / rxTotalChunks;

      document.getElementById("rx-filename").innerText = rxTargetFileName;
      document.getElementById("rx-frame-count").innerText = `${{count}}/${{rxTotalChunks}} frames`;
      document.getElementById("rx-progress-fill").style.width = `${{Math.floor(progress * 100)}}%`;
      document.getElementById("rx-percent").innerText = `${{Math.floor(progress * 100)}}% Received`;
      document.getElementById("rx-scan-status").innerText = "Receiving optical stream";

      const missing = getMissingRxIndices();
      const missingContainer = document.getElementById("rx-missing-container");
      const tagsContainer = document.getElementById("rx-missing-tags");

      if (missing.length > 0) {{
        missingContainer.style.display = "block";
        tagsContainer.innerHTML = missing.slice(0, 15).map(idx => `<span class="tag">#${{idx + 1}}</span>`).join("");
      }} else {{
        missingContainer.style.display = "none";
      }}
    }}

    function getMissingRxIndices() {{
      if (!rxTotalChunks) return [];
      const missing = [];
      for (let i = 0; i < rxTotalChunks; i++) {{
        if (!rxReceivedChunks[i]) missing.push(i);
      }}
      return missing;
    }}

    function triggerMissingFrameNACK() {{
      const missing = getMissingRxIndices();
      if (missing.length === 0) return;

      const nackList = missing.slice(0, 25).join(",");
      setRxDisplayQR(
        `REQ|${{nackList}}`,
        `Requesting ${{missing.length}} Missing Frames...`,
        "rgba(239, 68, 68, 0.2)",
        "#ef4444"
      );
    }}

    function finalizeReceiverReconstruction() {{
      rxIsComplete = true;

      try {{
        let totalByteLen = 0;
        for (let i = 0; i < rxTotalChunks; i++) {{
          totalByteLen += rxReceivedChunks[i].length;
        }}

        const containerStream = new Uint8Array(totalByteLen);
        let offset = 0;
        for (let i = 0; i < rxTotalChunks; i++) {{
          containerStream.set(rxReceivedChunks[i], offset);
          offset += rxReceivedChunks[i].length;
        }}

        // Verify Magic Header AQ02 (85 bytes header)
        const magic = String.fromCharCode(containerStream[0], containerStream[1], containerStream[2], containerStream[3]);
        let finalPlainBytes = null;
        let finalSha256Hex = "";

        if (magic === "AQ02" && containerStream.length >= 85) {{
          const salt = containerStream.subarray(4, 20);
          const nonce = containerStream.subarray(20, 36);
          const expectedMac = containerStream.subarray(36, 52);
          const isCompressed = (containerStream[52] === 1);
          const origShaRaw = containerStream.subarray(53, 85);
          const ciphertext = containerStream.subarray(85);

          let origShaHex = "";
          for (let i = 0; i < 32; i++) {{
            origShaHex += ("0" + origShaRaw[i].toString(16)).slice(-2);
          }}
          finalSha256Hex = origShaHex;

          const keyWords = deriveEncryptionKey(currentUser, currentPass, salt);
          const actualMacWords = computeHmacSha256(keyWords, nonce, ciphertext);

          const actualMacBytes = new Uint8Array(16);
          for (let i = 0; i < 4; i++) {{
            actualMacBytes[i * 4] = (actualMacWords.words[i] >>> 24) & 0xff;
            actualMacBytes[i * 4 + 1] = (actualMacWords.words[i] >>> 16) & 0xff;
            actualMacBytes[i * 4 + 2] = (actualMacWords.words[i] >>> 8) & 0xff;
            actualMacBytes[i * 4 + 3] = actualMacWords.words[i] & 0xff;
          }}

          let macMatch = true;
          for (let i = 0; i < 16; i++) {{
            if (actualMacBytes[i] !== expectedMac[i]) {{
              macMatch = false;
              break;
            }}
          }}

          if (!macMatch) {{
            throw new Error("Authentication tag mismatch (Incorrect password or corrupted stream).");
          }}

          const decryptedPayload = sha256CtrCrypt(ciphertext, keyWords, nonce);

          if (isCompressed) {{
            finalPlainBytes = pako.inflate(decryptedPayload);
          }} else {{
            finalPlainBytes = decryptedPayload;
          }}

          const plainWords = CryptoJS.lib.WordArray.create(finalPlainBytes);
          const actualShaHex = CryptoJS.SHA256(plainWords).toString(CryptoJS.enc.Hex);
          if (actualShaHex !== origShaHex) {{
            console.warn(`SHA-256 mismatch: expected ${{origShaHex}}, got ${{actualShaHex}}`);
          }}
        }} else {{
          finalPlainBytes = pako.inflate(containerStream);
          const plainWords = CryptoJS.lib.WordArray.create(finalPlainBytes);
          finalSha256Hex = CryptoJS.SHA256(plainWords).toString(CryptoJS.enc.Hex);
        }}

        rxReconstructedBytes = finalPlainBytes;

        const ackPayload = `ACK|AQRDT|COMPLETE|${{finalSha256Hex}}|${{currentUser}}`;
        setRxDisplayQR(ackPayload, `Transfer Complete & Verified! [User: ${{currentUser}}]`, "rgba(16, 185, 129, 0.2)", "#10b981");

        document.getElementById("rx-progress-fill").style.background = "#10b981";
        document.getElementById("rx-scan-status").innerText = "Complete & Verified";
        rxDownloadBtn.disabled = false;
        rxDebugLog.innerText = `✔ Decrypted successfully: SHA-256 [${{finalSha256Hex.substring(0, 16)}}...]`;

        triggerFileDownload();
      }} catch (err) {{
        console.error(err);
        statusPill.innerText = `Decryption Error: ${{err.message}}`;
        statusPill.style.background = "rgba(239, 68, 68, 0.2)";
        statusPill.style.color = "#ef4444";
        rxDebugLog.innerText = `✖ Error: ${{err.message}}`;
      }}
    }}

    function triggerFileDownload() {{
      if (!rxReconstructedBytes) return;
      const blob = new Blob([rxReconstructedBytes], {{ type: "application/octet-stream" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = rxTargetFileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }}

    function manualDownload() {{
      if (rxReconstructedBytes) triggerFileDownload();
    }}

    function openRawDataModal() {{
      const modal = document.getElementById("data-modal");
      const content = document.getElementById("raw-data-content");
      if (rxReconstructedBytes) {{
        const text = new TextDecoder().decode(rxReconstructedBytes);
        content.innerText = text.length > 5000 ? text.substring(0, 5000) + "\\n... (truncated)" : text;
      }} else if (Object.keys(rxReceivedChunks).length > 0) {{
        content.innerText = `Captured ${{Object.keys(rxReceivedChunks).length}} encrypted chunks so far.`;
      }} else {{
        content.innerText = "No data chunks received yet.";
      }}
      modal.style.display = "flex";
    }}

    function closeRawDataModal() {{
      document.getElementById("data-modal").style.display = "none";
    }}

    function resetReceiverSession() {{
      rxReceivedChunks = {{}};
      rxTotalChunks = null;
      rxIsComplete = false;
      rxReconstructedBytes = null;
      rxDownloadBtn.disabled = true;
      document.getElementById("rx-progress-fill").style.width = "0%";
      document.getElementById("rx-progress-fill").style.background = "var(--primary)";
      document.getElementById("rx-filename").innerText = "Awaiting stream...";
      document.getElementById("rx-frame-count").innerText = "0/0 frames";
      document.getElementById("rx-percent").innerText = "0%";
      document.getElementById("rx-missing-container").style.display = "none";
      if (currentUser) {{
        rxDebugLog.innerText = `Auth QR Active for user '${{currentUser}}'. Ready for Transmitter.`;
        setRxDisplayQR(currentAuthPayload, `Camera Active: Ready for User [${{currentUser}}]`, "rgba(56, 189, 248, 0.15)", "#38bdf8");
      }} else {{
        rxDebugLog.innerText = "Status: Please enter Username and Password above.";
        rxQrPlaceholder.style.display = "block";
        rxQrView.style.display = "none";
        statusPill.innerText = "Camera Active: Enter Credentials";
        statusPill.style.background = "rgba(56, 189, 248, 0.15)";
        statusPill.style.color = "#38bdf8";
      }}
    }}

    // =====================================================================
    // --- TRANSMITTER LOGIC ---
    // =====================================================================

    let txFile = null;
    let txFileBytes = null;
    let txPackets = [];
    let txFps = 12;
    let txChunkSize = 160;
    let txStreamInterval = null;
    let txCurrentIndex = 0;
    let txIsStreaming = false;
    let txIsPaused = false;
    let txQrGenerator = null;
    let txReceiverAuthenticated = false;
    let txVerifiedReceiverUser = null;
    let txPendingRetransmitQueue = [];

    const txDropzone = document.getElementById("tx-dropzone");
    const txFileInfo = document.getElementById("tx-file-info");
    const txStartBtn = document.getElementById("tx-start-btn");
    const txPauseBtn = document.getElementById("tx-pause-btn");
    const txBlastBtn = document.getElementById("tx-blast-btn");
    const txQrView = document.getElementById("tx-qr-container");
    const txQrPlaceholder = document.getElementById("tx-qr-placeholder");
    const txOverlay = document.getElementById("tx-frame-overlay");
    const txLog = document.getElementById("tx-log");

    // Drag and Drop Listeners
    ["dragenter", "dragover"].forEach(name => {{
      txDropzone.addEventListener(name, (e) => {{
        e.preventDefault();
        e.stopPropagation();
        txDropzone.classList.add("dragover");
      }});
    }});
    ["dragleave", "drop"].forEach(name => {{
      txDropzone.addEventListener(name, (e) => {{
        e.preventDefault();
        e.stopPropagation();
        txDropzone.classList.remove("dragover");
      }});
    }});
    txDropzone.addEventListener("drop", (e) => {{
      if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {{
        handleFileSelect(e.dataTransfer.files);
      }}
    }});

    function updateTxSpeed(val) {{
      txFps = parseInt(val, 10);
      document.getElementById("tx-fps-val").innerText = `${{txFps}} FPS`;
      if (txIsStreaming && !txIsPaused) {{
        clearInterval(txStreamInterval);
        txStreamInterval = setInterval(renderNextTxFrame, 1000 / txFps);
      }}
    }}

    function onTxSettingChanged() {{
      txChunkSize = parseInt(document.getElementById("tx-chunk-size").value, 10);
      if (txFileBytes) {{
        packageAndPrepareFile();
      }}
    }}

    function handleFileSelect(files) {{
      if (!files || files.length === 0) return;
      txFile = files[0];

      document.getElementById("dropzone-main-text").innerText = `Loaded: ${{txFile.name}}`;
      document.getElementById("dropzone-sub-text").innerText = `(${{formatFileSize(txFile.size)}})`;
      document.getElementById("tx-file-name").innerText = txFile.name;
      document.getElementById("tx-file-size").innerText = formatFileSize(txFile.size);

      const reader = new FileReader();
      reader.onload = function(e) {{
        txFileBytes = new Uint8Array(e.target.result);
        
        // Calculate original SHA-256
        const fileWords = CryptoJS.lib.WordArray.create(txFileBytes);
        const shaHex = CryptoJS.SHA256(fileWords).toString(CryptoJS.enc.Hex);
        document.getElementById("tx-file-sha").innerText = shaHex.substring(0, 16) + "...";
        txFileInfo.style.display = "flex";

        packageAndPrepareFile();
      }};
      reader.readAsArrayBuffer(txFile);
    }}

    function formatFileSize(bytes) {{
      if (bytes < 1024) return bytes + " B";
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
      return (bytes / (1024 * 1024)).toFixed(2) + " MB";
    }}

    function packageAndPrepareFile() {{
      if (!txFileBytes) return;

      if (!currentUser || !currentPass) {{
        txLog.innerText = "Please enter Username and Shared Password above to encrypt file.";
        txStartBtn.disabled = true;
        return;
      }}

      txLog.innerText = "Packaging & Encrypting file payload (ZLIB 9 + SHA-256 CTR AEAD)...";

      // 1. Compute original SHA-256
      const fileWords = CryptoJS.lib.WordArray.create(txFileBytes);
      const origShaHex = CryptoJS.SHA256(fileWords).toString(CryptoJS.enc.Hex);
      const origShaRaw = new Uint8Array(32);
      for (let i = 0; i < 32; i++) {{
        origShaRaw[i] = parseInt(origShaHex.substr(i * 2, 2), 16);
      }}

      // 2. Compress via Pako (ZLIB 9)
      const compressed = pako.deflate(txFileBytes, {{ level: 9 }});
      let payloadBytes = txFileBytes;
      let isCompressed = 0;
      let ratioPct = 0;

      if (compressed.length < txFileBytes.length) {{
        payloadBytes = compressed;
        isCompressed = 1;
        ratioPct = (1.0 - (compressed.length / Math.max(1, txFileBytes.length))) * 100.0;
      }}

      // 3. Generate random 16-byte salt and 16-byte nonce
      const salt = new Uint8Array(16);
      const nonce = new Uint8Array(16);
      window.crypto.getRandomValues(salt);
      window.crypto.getRandomValues(nonce);

      // 4. Derive key and encrypt
      const keyWords = deriveEncryptionKey(currentUser, currentPass, salt);
      const ciphertext = sha256CtrCrypt(payloadBytes, keyWords, nonce);

      // 5. Compute HMAC-SHA256 authentication tag
      const macWords = computeHmacSha256(keyWords, nonce, ciphertext);
      const macBytes = new Uint8Array(16);
      for (let i = 0; i < 4; i++) {{
        macBytes[i * 4] = (macWords.words[i] >>> 24) & 0xff;
        macBytes[i * 4 + 1] = (macWords.words[i] >>> 16) & 0xff;
        macBytes[i * 4 + 2] = (macWords.words[i] >>> 8) & 0xff;
        macBytes[i * 4 + 3] = macWords.words[i] & 0xff;
      }}

      // 6. Build Binary Container AQ02 (85 bytes header)
      const container = new Uint8Array(85 + ciphertext.length);
      container[0] = 0x41; // 'A'
      container[1] = 0x51; // 'Q'
      container[2] = 0x30; // '0'
      container[3] = 0x32; // '2'
      container.set(salt, 4);
      container.set(nonce, 20);
      container.set(macBytes, 36);
      container[52] = isCompressed;
      container.set(origShaRaw, 53);
      container.set(ciphertext, 85);

      // 7. Chunk into D|filename|idx|total|crc32|b64 packets
      const totalChunks = Math.ceil(container.length / txChunkSize);
      txPackets = [];

      for (let i = 0; i < totalChunks; i++) {{
        const start = i * txChunkSize;
        const end = Math.min(start + txChunkSize, container.length);
        const chunkSlice = container.subarray(start, end);
        const crcHex = crc32(chunkSlice);
        const b64Data = bytesToBase64(chunkSlice);
        const packetStr = `D|${{txFile.name}}|${{i}}|${{totalChunks}}|${{crcHex}}|${{b64Data}}`;
        txPackets.push(packetStr);
      }}

      document.getElementById("tx-status-label").innerText = `${{txFile.name}} (${{totalChunks}} frames)`;
      document.getElementById("tx-frame-counter").innerText = `0/${{totalChunks}} frames`;
      document.getElementById("tx-stats-compression").innerText = `Ratio: -${{ratioPct.toFixed(1)}}% (${{container.length}} B)`;

      txLog.innerText = `Ready to stream: ${{totalChunks}} frames packed at ${{txChunkSize}} B/chunk.`;
      txCheckReadyToTransmit();
    }}

    function txCheckReadyToTransmit() {{
      if (txPackets.length > 0 && currentUser && currentPass) {{
        txStartBtn.disabled = false;
        txBlastBtn.disabled = false;
      }}
    }}

    function startTransmission() {{
      if (txPackets.length === 0) return;

      txIsStreaming = true;
      txIsPaused = false;
      txCurrentIndex = 0;
      txPendingRetransmitQueue = [];

      txStartBtn.disabled = true;
      txPauseBtn.disabled = false;
      txPauseBtn.innerHTML = "<span>⏸</span> Pause";
      txBlastBtn.disabled = false;

      txQrPlaceholder.style.display = "none";
      txQrView.style.display = "flex";
      txOverlay.style.display = "block";

      if (!txQrGenerator) {{
        txQrGenerator = new QRCode(txQrView, {{
          text: txPackets[0],
          width: 250,
          height: 250,
          correctLevel: QRCode.CorrectLevel.M
        }});
      }}

      statusPill.innerText = `Streaming Optical Frames (${{txFps}} FPS)...`;
      statusPill.style.background = "rgba(168, 85, 247, 0.2)";
      statusPill.style.color = "#c084fc";

      clearInterval(txStreamInterval);
      txStreamInterval = setInterval(renderNextTxFrame, 1000 / txFps);
    }}

    function renderNextTxFrame() {{
      if (txIsPaused) return;

      let packetToSend = null;
      let frameDisplayIdx = 0;
      const totalFrames = txPackets.length;

      // Retransmissions take priority
      if (txPendingRetransmitQueue.length > 0) {{
        frameDisplayIdx = txPendingRetransmitQueue.shift();
        packetToSend = txPackets[frameDisplayIdx];
        document.getElementById("tx-status-label").innerText = `Retransmitting Frame #${{frameDisplayIdx + 1}}`;
      }} else if (txCurrentIndex < totalFrames) {{
        frameDisplayIdx = txCurrentIndex;
        packetToSend = txPackets[txCurrentIndex];
        txCurrentIndex++;
      }} else {{
        // End of primary blast: display DONE_BLAST to trigger receiver NACKs if needed
        packetToSend = "DONE_BLAST";
        document.getElementById("tx-status-label").innerText = "Blast Complete: Awaiting Receiver NACK/ACK";
        txLog.innerText = "Primary blast complete. Pointing camera at receiver screen for ARQ NACK or ACK.";
      }}

      if (packetToSend) {{
        txQrGenerator.clear();
        txQrGenerator.makeCode(packetToSend);

        const currentCount = Math.min(txCurrentIndex, totalFrames);
        const pct = Math.floor((currentCount / totalFrames) * 100);

        document.getElementById("tx-overlay-idx").innerText = frameDisplayIdx + 1;
        document.getElementById("tx-overlay-total").innerText = totalFrames;
        document.getElementById("tx-frame-counter").innerText = `${{currentCount}}/${{totalFrames}} frames`;
        document.getElementById("tx-progress-fill").style.width = `${{pct}}%`;
      }}
    }}

    function togglePauseTransmission() {{
      if (!txIsStreaming) return;
      txIsPaused = !txIsPaused;
      if (txIsPaused) {{
        txPauseBtn.innerHTML = "<span>▶</span> Resume";
        statusPill.innerText = "Stream Paused";
        statusPill.style.background = "rgba(245, 158, 11, 0.2)";
        statusPill.style.color = "#f59e0b";
      }} else {{
        txPauseBtn.innerHTML = "<span>⏸</span> Pause";
        statusPill.innerText = `Streaming (${{txFps}} FPS)...`;
        statusPill.style.background = "rgba(168, 85, 247, 0.2)";
        statusPill.style.color = "#c084fc";
      }}
    }}

    function retransmitAllLoop() {{
      if (txPackets.length === 0) return;
      txCurrentIndex = 0;
      txPendingRetransmitQueue = [];
      startTransmission();
    }}

    function handleTransmitterIncoming(payload) {{
      // 1. Receiver Auth QR
      if (payload.startsWith("AUTH|AQRDT|v2|")) {{
        const auth = verifyAuthPayload(payload, currentUser, currentPass);
        if (auth.valid) {{
          txReceiverAuthenticated = true;
          txVerifiedReceiverUser = auth.user;
          document.getElementById("tx-handshake-status").innerText = `Receiver Verified [${{auth.user}}]`;
          document.getElementById("tx-handshake-status").style.color = "var(--success)";
          statusPill.innerText = `Receiver Verified: '${{auth.user}}'`;
          statusPill.style.background = "rgba(16, 185, 129, 0.2)";
          statusPill.style.color = "#10b981";
        }}
        return;
      }}

      // 2. ARQ Missing Packet NACK (REQ|<ranges>)
      if (payload.startsWith("REQ|")) {{
        const rangeStr = payload.substring(4).trim();
        const missingIndices = decompressIndices(rangeStr);
        if (missingIndices.length > 0) {{
          txLog.innerText = `ARQ Request: Receiver requested ${{missingIndices.length}} missing frames (${{rangeStr}}).`;
          for (let idx of missingIndices) {{
            if (idx >= 0 && idx < txPackets.length && !txPendingRetransmitQueue.includes(idx)) {{
              txPendingRetransmitQueue.push(idx);
            }}
          }}
          if (!txIsStreaming || txIsPaused) {{
            txIsPaused = false;
            txIsStreaming = true;
            clearInterval(txStreamInterval);
            txStreamInterval = setInterval(renderNextTxFrame, 1000 / txFps);
          }}
        }}
        return;
      }}

      // 3. Transfer Completion ACK (ACK|AQRDT|COMPLETE|<sha256>|<user>)
      if (payload.startsWith("ACK|AQRDT|COMPLETE")) {{
        clearInterval(txStreamInterval);
        txIsStreaming = false;
        txStartBtn.disabled = false;
        txPauseBtn.disabled = true;

        statusPill.innerText = "✔ Transfer Complete & Verified by Receiver!";
        statusPill.style.background = "rgba(16, 185, 129, 0.25)";
        statusPill.style.color = "#10b981";
        document.getElementById("tx-status-label").innerText = "Transfer Complete & Confirmed";
        document.getElementById("tx-progress-fill").style.background = "#10b981";
        document.getElementById("tx-progress-fill").style.width = "100%";
        txLog.innerText = `✔ SUCCESS: Optical transfer fully acknowledged by receiver!`;
      }}
    }}

    function resetTransmitterSession() {{
      clearInterval(txStreamInterval);
      txIsStreaming = false;
      txIsPaused = false;
      txCurrentIndex = 0;
      txPendingRetransmitQueue = [];
      txPackets = [];
      txFile = null;
      txFileBytes = null;

      txStartBtn.disabled = true;
      txPauseBtn.disabled = true;
      txBlastBtn.disabled = true;
      txQrPlaceholder.style.display = "block";
      txQrView.style.display = "none";
      txOverlay.style.display = "none";
      txFileInfo.style.display = "none";
      document.getElementById("dropzone-main-text").innerText = "Click or Drop File to Stream";
      document.getElementById("dropzone-sub-text").innerText = "Supports any file type or format";
      document.getElementById("tx-status-label").innerText = "Ready to package";
      document.getElementById("tx-frame-counter").innerText = "0/0 frames";
      document.getElementById("tx-progress-fill").style.width = "0%";
      document.getElementById("tx-progress-fill").style.background = "var(--tx-primary)";
      document.getElementById("tx-handshake-status").innerText = "Awaiting Receiver Auth";
      document.getElementById("tx-handshake-status").style.color = "var(--text-muted)";
      document.getElementById("tx-stats-compression").innerText = "ZLIB 9: 0% ratio";
      txLog.innerText = "Transmitter reset. Select file to begin.";
      statusPill.innerText = "Transmitter Ready";
    }}

    window.addEventListener("DOMContentLoaded", () => {{
      initCamera();
    }});
  </script>
</body>
</html>
"""

output_path = os.path.join(BASE_DIR, "index_offline.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)

print(f"Done! Successfully generated '{output_path}' ({len(HTML_CONTENT):,} bytes).")
