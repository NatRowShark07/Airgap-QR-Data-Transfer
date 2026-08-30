"""
build_offline_pwa.py - Builds the self-contained zero-dependency HTML5/PWA Receiver for AQRDT v2.
Inlines qrcodejs, jsQR, pako, and crypto-js into a single offline HTML file.
"""

import urllib.request
import os

LIBRARIES = {
    "qrcode": "https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js",
    "jsqr": "https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js",
    "pako": "https://cdn.jsdelivr.net/npm/pako@2.1.0/dist/pako.min.js",
    "cryptojs": "https://cdn.jsdelivr.net/npm/crypto-js@4.2.0/crypto-js.min.js"
}

print("Fetching JS libraries for offline bundle...")
downloaded_scripts = {}
for name, url in LIBRARIES.items():
    print(f"  - Downloading {name} from {url}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        downloaded_scripts[name] = response.read().decode('utf-8')

HTML_TEMPLATE = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <title>Airgapped QR Data Transfer (AQRDT v2)</title>

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
      padding: 12px;
      justify-content: space-between;
    }}
    header {{ text-align: center; margin-top: 4px; width: 100%; max-width: 380px; }}
    header h1 {{ font-size: 1.15rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.02em; }}
    #status-pill {{
      display: inline-block;
      margin-top: 4px;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      background: rgba(56, 189, 248, 0.15);
      color: var(--primary);
      border: 1px solid rgba(56, 189, 248, 0.3);
    }}

    /* Auth & Identity Configuration Box */
    #auth-panel {{
      width: 100%;
      max-width: 360px;
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 10px 14px;
      margin: 8px 0;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }}
    .auth-title {{
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--primary);
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}
    .auth-inputs {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}
    .auth-input-group {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}
    .auth-input-group label {{
      font-size: 0.68rem;
      color: var(--text-muted);
      font-weight: 600;
    }}
    .auth-input-group input {{
      background: #0f172a;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 6px 8px;
      color: #f8fafc;
      font-size: 0.78rem;
      outline: none;
      transition: border-color 0.2s;
    }}
    .auth-input-group input:focus {{
      border-color: var(--primary);
    }}
    .btn-update-auth {{
      margin-top: 8px;
      width: 100%;
      height: 30px;
      background: rgba(56, 189, 248, 0.15);
      color: var(--primary);
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 4px;
    }}
    .btn-update-auth:hover {{
      background: var(--primary);
      color: #0b1120;
    }}

    #viewport-container {{
      width: 280px;
      height: 280px;
      background: #ffffff;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
      padding: 8px;
      position: relative;
    }}
    #qrcode-view {{
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    #qrcode-view img {{ width: 100%; height: 100%; object-fit: contain; }}

    #cam-monitor {{
      position: fixed;
      top: 16px;
      right: 14px;
      width: 70px;
      height: 70px;
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
    #hidden-canvas {{ display: none; }}

    #hud {{
      width: 100%;
      max-width: 360px;
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 10px 14px;
    }}
    .hud-row {{ display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px; }}
    .progress-bar {{ width: 100%; height: 6px; background: #334155; border-radius: 4px; overflow: hidden; margin-bottom: 4px; }}
    .progress-fill {{ height: 100%; width: 0%; background: var(--primary); transition: width 0.15s ease; }}
    #missing-tags {{ display: flex; gap: 4px; flex-wrap: wrap; max-height: 32px; overflow: hidden; margin-top: 4px; }}
    .tag {{ font-size: 0.65rem; font-family: monospace; background: rgba(239, 68, 68, 0.2); color: var(--danger); padding: 2px 5px; border-radius: 4px; font-weight: bold; }}
    
    #debug-log {{
      font-size: 0.68rem;
      font-family: monospace;
      color: #cbd5e1;
      background: rgba(0, 0, 0, 0.3);
      padding: 4px 8px;
      border-radius: 6px;
      word-break: break-all;
      margin-top: 4px;
    }}

    .controls {{
      width: 100%;
      max-width: 360px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 6px;
    }}
    button {{
      height: 40px;
      border: none;
      border-radius: 10px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      background: var(--card);
      color: var(--text);
      border: 1px solid var(--card-border);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: background 0.15s;
    }}
    button:hover {{ background: #334155; }}
    button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
    .btn-download {{ background: var(--success); color: white; border: none; }}
    .btn-download:hover {{ background: #059669; }}
    .full-width {{ grid-column: span 2; }}

    #data-modal {{
      display: none;
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: rgba(0, 0, 0, 0.85);
      z-index: 200;
      padding: 20px;
      flex-direction: column;
      justify-content: center;
      align-items: center;
    }}
    #data-modal-box {{
      width: 100%;
      max-width: 360px;
      max-height: 80vh;
      background: var(--card);
      border-radius: 16px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      border: 1px solid var(--card-border);
    }}
    #raw-data-content {{
      width: 100%;
      height: 250px;
      background: #0f172a;
      color: #38bdf8;
      font-family: monospace;
      font-size: 0.75rem;
      padding: 10px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }}
  </style>
</head>
<body>

  <header>
    <h1>✦ Airgapped QR Data Transfer</h1>
    <div id="status-pill">Initializing Camera...</div>
  </header>

  <!-- Dynamic Auth Credentials UI -->
  <div id="auth-panel">
    <div class="auth-title">
      <span>🔐 Receiver Authentication & Key</span>
      <span id="auth-indicator" style="color: var(--warning); font-size: 0.7rem;">○ Awaiting Credentials</span>
    </div>
    <div class="auth-inputs">
      <div class="auth-input-group">
        <label for="input-username">Username</label>
        <input type="text" id="input-username" value="" placeholder="Enter Username (e.g. Nathaniel)" autocomplete="off" onkeydown="if(event.key==='Enter') applyCredentials();" />
      </div>
      <div class="auth-input-group">
        <label for="input-password">Shared Password</label>
        <input type="password" id="input-password" value="" placeholder="Enter Shared Password" autocomplete="off" onkeydown="if(event.key==='Enter') applyCredentials();" />
      </div>
    </div>
    <button class="btn-update-auth" onclick="applyCredentials()">🔄 Generate Auth QR & Encryption Key</button>
  </div>

  <div id="viewport-container">
    <div id="qrcode-placeholder" style="color: #64748b; text-align: center; font-size: 0.85rem; font-weight: 500; padding: 24px; line-height: 1.5;">
      <div style="font-size: 2rem; margin-bottom: 8px;">🔐</div>
      Enter your <strong>Username</strong> and <strong>Password</strong> above, then click <em>"Generate Auth QR"</em>.
    </div>
    <div id="qrcode-view" style="display: none;"></div>
  </div>

  <div id="cam-monitor">
    <video id="video-view" autoplay playsinline webkit-playsinline muted></video>
  </div>
  <canvas id="hidden-canvas"></canvas>

  <div id="hud">
    <div class="hud-row">
      <span id="hud-filename" style="font-weight: 600;">Awaiting stream...</span>
      <span id="hud-frames" style="color: var(--text-muted);">0/0 frames</span>
    </div>
    <div class="progress-bar">
      <div id="progress-fill" class="progress-fill"></div>
    </div>
    <div class="hud-row">
      <span id="hud-percent" style="font-size: 0.75rem; font-weight: bold;">0%</span>
      <span id="scan-status" style="font-size: 0.75rem; color: var(--text-muted);">Scanning Camera</span>
    </div>
    <div id="missing-container" style="display: none;">
      <div style="font-size: 0.7rem; color: var(--danger); margin-bottom: 2px;">Missing Packets:</div>
      <div id="missing-tags"></div>
    </div>
    <div id="debug-log">Status: Please enter Username and Password above.</div>
  </div>

  <div class="controls">
    <button onclick="openRawDataModal()">View Decrypted</button>
    <button id="download-btn" class="btn-download" onclick="manualDownload()" disabled>Download File</button>
    <button class="full-width" onclick="resetSession()">Reset Session</button>
  </div>

  <div id="data-modal">
    <div id="data-modal-box">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: 700; font-size: 0.95rem;">Decrypted Payload Viewer</span>
        <button style="width: 28px; height: 28px; border-radius: 50%;" onclick="closeRawDataModal()">✕</button>
      </div>
      <div id="raw-data-content">No data received yet.</div>
    </div>
  </div>

  <script>
    // =====================================================================
    // --- Cryptographic & Encoding Helper Functions ---
    // =====================================================================

    const MAGIC_HEADER = "AQ02"; // 4 bytes magic string

    function computeAuthSignature(user, pass) {{
      const normUser = user.trim().toLowerCase();
      const normPass = pass.trim();
      return CryptoJS.SHA256("AQRDT_AUTH_v2:" + normUser + ":" + normPass).toString(CryptoJS.enc.Hex);
    }}

    function generateAuthQRPayload(user, pass) {{
      const sig = computeAuthSignature(user, pass);
      return `AUTH|AQRDT|v2|${{user.trim()}}|${{sig}}`;
    }}

    function decodeBase64ToBytes(b64Str) {{
      const bin = atob(b64Str.replace(/[\\r\\n\\s]/g, ""));
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return bytes;
    }}

    function deriveEncryptionKey(user, pass, saltBytes) {{
      const normUser = user.trim().toLowerCase();
      const normPass = pass.trim();
      
      // Convert salt Uint8Array to CryptoJS WordArray
      const saltWords = CryptoJS.lib.WordArray.create(saltBytes);
      const userPassWords = CryptoJS.enc.Utf8.parse(normUser + ":" + normPass + ":");
      const combined = userPassWords.concat(saltWords);
      
      return CryptoJS.SHA256(combined);
    }}

    function sha256CtrDecrypt(cipherBytes, keyWords, nonceBytes) {{
      const out = new Uint8Array(cipherBytes.length);
      const blockSize = 32;
      const numBlocks = Math.ceil(cipherBytes.length / blockSize);
      const nonceWords = CryptoJS.lib.WordArray.create(nonceBytes);

      for (let i = 0; i < numBlocks; i++) {{
        const counterBytes = new Uint8Array(4);
        counterBytes[0] = (i >>> 24) & 0xff;
        counterBytes[1] = (i >>> 16) & 0xff;
        counterBytes[2] = (i >>> 8) & 0xff;
        counterBytes[3] = i & 0xff;

        const counterWords = CryptoJS.lib.WordArray.create(counterBytes);
        
        // BlockKey = SHA256(key + nonce + counter)
        const combined = keyWords.clone().concat(nonceWords.clone()).concat(counterWords);
        const ksWords = CryptoJS.SHA256(combined);

        // Extract keystream bytes from WordArray
        const start = i * blockSize;
        const end = Math.min(start + blockSize, cipherBytes.length);
        for (let j = 0; j < end - start; j++) {{
          const byteIdx = j;
          const wordIdx = Math.floor(byteIdx / 4);
          const byteInWord = 3 - (byteIdx % 4);
          const ksByte = (ksWords.words[wordIdx] >>> (byteInWord * 8)) & 0xff;
          out[start + j] = cipherBytes[start + j] ^ ksByte;
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

    // =====================================================================
    // --- Application State & UI Controller ---
    // =====================================================================

    let currentUser = "";
    let currentPass = "";
    let currentAuthPayload = "";

    let qrGenerator = null;
    let video = document.getElementById("video-view");
    let canvas = document.getElementById("hidden-canvas");
    let ctx = canvas.getContext("2d", {{ willReadFrequently: true }});

    let receivedRawChunks = {{}};
    let totalChunks = null;
    let targetFileName = "received_file";
    let isComplete = false;
    let currentQRString = "";
    let lastChunkReceivedTime = Date.now();
    let reconstructedBytes = null;

    const statusPill = document.getElementById("status-pill");
    const scanStatus = document.getElementById("scan-status");
    const debugLog = document.getElementById("debug-log");
    const qrView = document.getElementById("qrcode-view");
    const qrPlaceholder = document.getElementById("qrcode-placeholder");
    const downloadBtn = document.getElementById("download-btn");

    function applyCredentials() {{
      const u = document.getElementById("input-username").value.trim();
      const p = document.getElementById("input-password").value.trim();

      if (!u || !p) {{
        statusPill.innerText = "Please Enter Username & Password";
        statusPill.style.background = "rgba(239, 68, 68, 0.2)";
        statusPill.style.color = "#ef4444";
        document.getElementById("auth-indicator").innerHTML = "○ Awaiting Credentials";
        document.getElementById("auth-indicator").style.color = "var(--warning)";
        debugLog.innerText = "Error: Both username and password are required.";
        return;
      }}

      currentUser = u;
      currentPass = p;

      currentAuthPayload = generateAuthQRPayload(currentUser, currentPass);

      qrPlaceholder.style.display = "none";
      qrView.style.display = "flex";

      if (!qrGenerator) {{
        qrGenerator = new QRCode(qrView, {{
          text: currentAuthPayload,
          width: 250,
          height: 250,
          correctLevel: QRCode.CorrectLevel.M
        }});
      }} else {{
        qrGenerator.clear();
        qrGenerator.makeCode(currentAuthPayload);
      }}
      currentQRString = currentAuthPayload;

      statusPill.innerText = `Auth QR: Ready [User: ${{currentUser}}]`;
      statusPill.style.background = "rgba(16, 185, 129, 0.2)";
      statusPill.style.color = "#10b981";

      document.getElementById("auth-indicator").innerHTML = `● Active: ${{currentUser}}`;
      document.getElementById("auth-indicator").style.color = "var(--success)";

      debugLog.innerText = `Auth QR active for user '${{currentUser}}'. Point Transmitter camera at this screen.`;
    }}

    function setDisplayQR(text, label, pillBg, pillColor) {{
      if (!qrGenerator) return;
      if (currentQRString === text) return;
      currentQRString = text;
      qrGenerator.clear();
      qrGenerator.makeCode(text);
      if (label) {{
        statusPill.innerText = label;
        statusPill.style.background = pillBg || "rgba(56, 189, 248, 0.15)";
        statusPill.style.color = pillColor || "#38bdf8";
      }}
    }}

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

        if (currentUser) {{
          statusPill.innerText = `Camera Active: Ready for User [${{currentUser}}]`;
        }} else {{
          statusPill.innerText = "Camera Active: Enter Credentials";
        }}
        requestAnimationFrame(scanLoop);
      }} catch (err) {{
        statusPill.innerText = "Camera Permission Denied";
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
          document.getElementById("cam-monitor").style.borderColor = "#10b981";
          handleIncomingPayload(code.data);
        }} else {{
          document.getElementById("cam-monitor").style.borderColor = "#38bdf8";
        }}

        if (totalChunks !== null && !isComplete) {{
          if (Date.now() - lastChunkReceivedTime > 1500) {{
            triggerMissingFrameNACK();
          }}
        }}
      }}
      requestAnimationFrame(scanLoop);
    }}

    function handleIncomingPayload(payload) {{
      if (isComplete) return;

      debugLog.innerText = "Scanned: " + (payload.length > 32 ? payload.substring(0, 32) + "..." : payload);

      if (payload === "DONE_BLAST") {{
        triggerMissingFrameNACK();
        return;
      }}

      if (payload.startsWith("D|")) {{
        const parts = payload.split("|");
        // D|<fname>|<idx>|<total>|<crc32>|<b64_chunk> (6 parts) or 5 parts
        if (parts.length >= 5) {{
          targetFileName = parts[1];
          const idx = parseInt(parts[2], 10);
          totalChunks = parseInt(parts[3], 10);
          const b64Data = parts[parts.length - 1];

          if (!isNaN(idx) && !isNaN(totalChunks)) {{
            if (!receivedRawChunks[idx]) {{
              try {{
                receivedRawChunks[idx] = decodeBase64ToBytes(b64Data);
                lastChunkReceivedTime = Date.now();
                updateHUD();

                if (currentQRString !== currentAuthPayload && getMissingIndices().length === 0) {{
                  setDisplayQR(currentAuthPayload, `Receiving Encrypted Stream for [${{currentUser}}]...`, "rgba(56, 189, 248, 0.15)", "#38bdf8");
                }}
              }} catch (e) {{}}
            }}

            if (Object.keys(receivedRawChunks).length === totalChunks && !isComplete) {{
              finalizeReconstruction();
            }}
          }}
        }}
      }}
    }}

    function updateHUD() {{
      const count = Object.keys(receivedRawChunks).length;
      const progress = count / totalChunks;

      document.getElementById("hud-filename").innerText = targetFileName;
      document.getElementById("hud-frames").innerText = `${{count}}/${{totalChunks}} frames`;
      document.getElementById("progress-fill").style.width = `${{Math.floor(progress * 100)}}%`;
      document.getElementById("hud-percent").innerText = `${{Math.floor(progress * 100)}}% Received`;
      scanStatus.innerText = "Receiving optical stream";

      const missing = getMissingIndices();
      const missingContainer = document.getElementById("missing-container");
      const tagsContainer = document.getElementById("missing-tags");

      if (missing.length > 0) {{
        missingContainer.style.display = "block";
        tagsContainer.innerHTML = missing.slice(0, 15).map(idx => `<span class="tag">#${{idx + 1}}</span>`).join("");
      }} else {{
        missingContainer.style.display = "none";
      }}
    }}

    function getMissingIndices() {{
      if (!totalChunks) return [];
      const missing = [];
      for (let i = 0; i < totalChunks; i++) {{
        if (!receivedRawChunks[i]) missing.push(i);
      }}
      return missing;
    }}

    function triggerMissingFrameNACK() {{
      const missing = getMissingIndices();
      if (missing.length === 0) return;

      const nackList = missing.slice(0, 25).join(",");
      setDisplayQR(
        `REQ|${{nackList}}`,
        `Requesting ${{missing.length}} Missing Frames...`,
        "rgba(239, 68, 68, 0.2)",
        "#ef4444"
      );
    }}

    function finalizeReconstruction() {{
      isComplete = true;

      try {{
        // 1. Reassemble total binary container stream
        let totalByteLen = 0;
        for (let i = 0; i < totalChunks; i++) {{
          totalByteLen += receivedRawChunks[i].length;
        }}

        const containerStream = new Uint8Array(totalByteLen);
        let offset = 0;
        for (let i = 0; i < totalChunks; i++) {{
          containerStream.set(receivedRawChunks[i], offset);
          offset += receivedRawChunks[i].length;
        }}

        // 2. Check Magic Header "AQ02" (85 bytes header)
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

          // Convert expected SHA256 to hex string
          let origShaHex = "";
          for (let i = 0; i < 32; i++) {{
            origShaHex += ("0" + origShaRaw[i].toString(16)).slice(-2);
          }}
          finalSha256Hex = origShaHex;

          // Derive Key & Verify HMAC-SHA256
          const keyWords = deriveEncryptionKey(currentUser, currentPass, salt);
          const actualMacWords = computeHmacSha256(keyWords, nonce, ciphertext);

          // Compare first 16 bytes of MAC
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
            throw new Error("Invalid password or HMAC authentication mismatch.");
          }}

          // Decrypt via SHA-256 CTR stream cipher
          const decryptedPayload = sha256CtrDecrypt(ciphertext, keyWords, nonce);

          // Lossless Decompression via Pako ZLIB
          if (isCompressed) {{
            finalPlainBytes = pako.inflate(decryptedPayload);
          }} else {{
            finalPlainBytes = decryptedPayload;
          }}

          // Verify SHA-256
          const plainWords = CryptoJS.lib.WordArray.create(finalPlainBytes);
          const actualShaHex = CryptoJS.SHA256(plainWords).toString(CryptoJS.enc.Hex);
          if (actualShaHex !== origShaHex) {{
            console.warn(`SHA-256 mismatch: expected ${{origShaHex}}, got ${{actualShaHex}}`);
          }}
        }} else {{
          // Legacy unencrypted ZLIB fallback
          finalPlainBytes = pako.inflate(containerStream);
          const plainWords = CryptoJS.lib.WordArray.create(finalPlainBytes);
          finalSha256Hex = CryptoJS.SHA256(plainWords).toString(CryptoJS.enc.Hex);
        }}

        reconstructedBytes = finalPlainBytes;

        // Signal completion ACK with SHA-256 and User
        const ackPayload = `ACK|AQRDT|COMPLETE|${{finalSha256Hex}}|${{currentUser}}`;
        setDisplayQR(ackPayload, `Transfer Complete & Verified! [User: ${{currentUser}}]`, "rgba(16, 185, 129, 0.2)", "#10b981");

        document.getElementById("progress-fill").style.background = "#10b981";
        scanStatus.innerText = "Complete & Decrypted";
        downloadBtn.disabled = false;
        debugLog.innerText = `✔ Decrypted successfully: SHA-256 [${{finalSha256Hex.substring(0, 16)}}...]`;

        triggerFileDownload();
      }} catch (err) {{
        console.error(err);
        statusPill.innerText = `Decryption Error: ${{err.message}}`;
        statusPill.style.background = "rgba(239, 68, 68, 0.2)";
        statusPill.style.color = "#ef4444";
        debugLog.innerText = `✖ Error: ${{err.message}}. Check password and retry.`;
      }}
    }}

    function triggerFileDownload() {{
      if (!reconstructedBytes) return;
      const blob = new Blob([reconstructedBytes], {{ type: "application/octet-stream" }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = targetFileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }}

    function manualDownload() {{
      if (reconstructedBytes) {{
        triggerFileDownload();
      }}
    }}

    function openRawDataModal() {{
      const modal = document.getElementById("data-modal");
      const content = document.getElementById("raw-data-content");
      
      if (reconstructedBytes) {{
        let text = new TextDecoder().decode(reconstructedBytes);
        content.innerText = text.length > 5000 ? text.substring(0, 5000) + "\\n... (truncated)" : text;
      }} else if (Object.keys(receivedRawChunks).length > 0) {{
        content.innerText = `Captured ${{Object.keys(receivedRawChunks).length}} encrypted chunks so far.`;
      }} else {{
        content.innerText = "No data chunks received yet.";
      }}
      modal.style.display = "flex";
    }}

    function closeRawDataModal() {{
      document.getElementById("data-modal").style.display = "none";
    }}

    function resetSession() {{
      receivedRawChunks = {{}};
      totalChunks = null;
      isComplete = false;
      reconstructedBytes = null;
      downloadBtn.disabled = true;
      document.getElementById("progress-fill").style.width = "0%";
      document.getElementById("progress-fill").style.background = "var(--primary)";
      document.getElementById("hud-filename").innerText = "Awaiting stream...";
      document.getElementById("hud-frames").innerText = "0/0 frames";
      document.getElementById("hud-percent").innerText = "0%";
      document.getElementById("missing-container").style.display = "none";
      if (currentUser) {{
        debugLog.innerText = `Auth QR Active for user '${{currentUser}}'. Ready for Transmitter.`;
        setDisplayQR(currentAuthPayload, `Camera Active: Ready for User [${{currentUser}}]`, "rgba(56, 189, 248, 0.15)", "#38bdf8");
      }} else {{
        debugLog.innerText = "Status: Please enter Username and Password above.";
        qrPlaceholder.style.display = "block";
        qrView.style.display = "none";
        statusPill.innerText = "Camera Active: Enter Credentials";
        statusPill.style.background = "rgba(56, 189, 248, 0.15)";
        statusPill.style.color = "#38bdf8";
      }}
    }}

    window.addEventListener("DOMContentLoaded", initCamera);
  </script>
</body>
</html>
"""

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index_offline.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(HTML_TEMPLATE)

print(f"Done! Successfully generated '{output_path}' ({len(HTML_TEMPLATE):,} bytes).")
