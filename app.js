/* app.js - Logic for Slice & Rise Simulator */

// State Management
const STATE = {
  activeTab: 'chat', // 'chat' or 'analytics'
  selectedPizza: 'perfect', // 'perfect', 'underbaked', 'burnt'
  isScanning: false,
  scansHistory: [
    { id: "1001", time: "11:24 AM", date: "2026-06-17", grade: "PASS", edgeHeight: 0.9, edgeWidth: 1.1, centerVolume: 0.45, topColor: 8, bottomColor: 8, failReason: "", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1001.jpg", userCorrected: false, verified: true, userMetrics: null },
    { id: "1002", time: "12:15 PM", date: "2026-06-17", grade: "PASS", edgeHeight: 0.95, edgeWidth: 1.2, centerVolume: 0.40, topColor: 9, bottomColor: 7, failReason: "", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1002.jpg", userCorrected: false, verified: true, userMetrics: null },
    { id: "1003", time: "01:05 PM", date: "2026-06-18", grade: "FAIL", edgeHeight: 0.6, edgeWidth: 1.4, centerVolume: 0.30, topColor: 4, bottomColor: 5, failReason: "Underbaked", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1003.jpg", userCorrected: false, verified: false, userMetrics: null },
    { id: "1004", time: "02:30 PM", date: "2026-06-18", grade: "PASS", edgeHeight: 0.88, edgeWidth: 1.15, centerVolume: 0.42, topColor: 8, bottomColor: 9, failReason: "", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1004.jpg", userCorrected: false, verified: true, userMetrics: null },
    { id: "1005", time: "05:10 PM", date: "2026-06-19", grade: "FAIL", edgeHeight: 0.9, edgeWidth: 1.1, centerVolume: 0.48, topColor: 12, bottomColor: 11, failReason: "Overbaked", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1005.jpg", userCorrected: false, verified: false, userMetrics: null },
    { id: "1006", time: "07:45 PM", date: "2026-06-19", grade: "PASS", edgeHeight: 0.92, edgeWidth: 1.1, centerVolume: 0.45, topColor: 10, bottomColor: 8, failReason: "", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1006.jpg", userCorrected: false, verified: true, userMetrics: null },
    { id: "1007", time: "11:15 AM", date: "2026-06-20", grade: "PASS", edgeHeight: 0.9, edgeWidth: 1.15, centerVolume: 0.40, topColor: 8, bottomColor: 8, failReason: "", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1007.jpg", userCorrected: false, verified: true, userMetrics: null },
    { id: "1008", time: "12:50 PM", date: "2026-06-20", grade: "PASS", edgeHeight: 0.95, edgeWidth: 1.1, centerVolume: 0.44, topColor: 9, bottomColor: 9, failReason: "", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1008.jpg", userCorrected: false, verified: true, userMetrics: null },
    { id: "1009", time: "03:15 PM", date: "2026-06-21", grade: "FAIL", edgeHeight: 0.5, edgeWidth: 1.35, centerVolume: 0.28, topColor: 5, bottomColor: 4, failReason: "Underbaked", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1009.jpg", userCorrected: false, verified: false, userMetrics: null },
    { id: "1010", time: "06:05 PM", date: "2026-06-21", grade: "PASS", edgeHeight: 0.88, edgeWidth: 1.1, centerVolume: 0.46, topColor: 8, bottomColor: 8, failReason: "", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1010.jpg", userCorrected: false, verified: true, userMetrics: null },
    { id: "1011", time: "11:40 AM", date: "2026-06-22", grade: "PASS", edgeHeight: 0.9, edgeWidth: 1.12, centerVolume: 0.42, topColor: 9, bottomColor: 8, failReason: "", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1011.jpg", userCorrected: false, verified: true, userMetrics: null },
    { id: "1012", time: "01:10 PM", date: "2026-06-22", grade: "PASS", edgeHeight: 0.92, edgeWidth: 1.15, centerVolume: 0.40, topColor: 8, bottomColor: 7, failReason: "", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1012.jpg", userCorrected: false, verified: true, userMetrics: null },
    { id: "1013", time: "04:30 PM", date: "2026-06-22", grade: "FAIL", edgeHeight: 0.9, edgeWidth: 1.25, centerVolume: 0.35, topColor: 12, bottomColor: 11, failReason: "Overbaked", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1013.jpg", userCorrected: false, verified: false, userMetrics: null },
    { id: "1014", time: "07:15 PM", date: "2026-06-22", grade: "PASS", edgeHeight: 0.94, edgeWidth: 1.1, centerVolume: 0.45, topColor: 9, bottomColor: 9, failReason: "", gcsUri: "gs://slice_n_rise_scans/pizza_scan_1014.jpg", userCorrected: false, verified: true, userMetrics: null }
  ]
};

// Pizza Profiles Configurations
const PIZZA_PROFILES = {
  perfect: {
    title: "Perfect Neapolitan",
    image: "assets/perfect.png",
    desc: "Slice & Rise Ideal Spec",
    grade: "PASS",
    metrics: {
      edgeHeight: { name: "Edge Height", value: 0.94, unit: "\"", min: 0.875, max: 1.0, progressVal: 94, status: "pass", display: "15/16\" (0.94\")" },
      edgeWidth: { name: "Edge Width", value: 1.12, unit: "\"", min: 1.0, max: 1.25, progressVal: 50, status: "pass", display: "1 1/8\" (1.12\")" },
      centerVolume: { name: "Center Volume", value: 0.44, unit: "\"", min: 0.375, max: 0.5, progressVal: 55, status: "pass", display: "7/16\" (0.44\")" },
      topColor: { name: "Top Crust Color", value: 9, unit: "/11", min: 7, max: 11, progressVal: 80, status: "pass", display: "9 (Golden leopard spots)" },
      bottomColor: { name: "Bottom Crust Color", value: 8, unit: "/10", min: 6, max: 10, progressVal: 75, status: "pass", display: "8 (Mottled golden-brown)" }
    },
    fix: "None! This pizza perfectly aligns with the Slice & Rise standard. Excellent stretching, proofing, and bake calibration."
  },
  underbaked: {
    title: "Underbaked / Pale",
    image: "assets/underbaked.png",
    desc: "Pale, Doughy Crust",
    grade: "FAIL",
    metrics: {
      edgeHeight: { name: "Edge Height", value: 0.52, unit: "\"", min: 0.875, max: 1.0, progressVal: 20, status: "fail", display: "1/2\" (0.52\")" },
      edgeWidth: { name: "Edge Width", value: 1.45, unit: "\"", min: 1.0, max: 1.25, progressVal: 95, status: "fail", display: "1 7/16\" (1.45\")" },
      centerVolume: { name: "Center Volume", value: 0.25, unit: "\"", min: 0.375, max: 0.5, progressVal: 10, status: "fail", display: "1/4\" (0.25\")" },
      topColor: { name: "Top Crust Color", value: 4, unit: "/11", min: 7, max: 11, progressVal: 30, status: "fail", display: "4 (Pale ivory)" },
      bottomColor: { name: "Bottom Crust Color", value: 3, unit: "/10", min: 6, max: 10, progressVal: 20, status: "fail", display: "3 (Doughy white)" }
    },
    fix: "Symptom: Pale crust, flat edge, and low center volume. Operational Root Cause: The dough was likely too cold when stretched (taken straight from walk-in, leading to poor spring) or the oven belt speed is too fast. **Remediation**: Let dough proofs at room temp for at least 15 minutes before stretching. Check that the oven belt speed is calibrated to a 420-second cycle at 485°F."
  },
  burnt: {
    title: "Burnt / Overcooked",
    image: "assets/burnt.png",
    desc: "Excessive Char, Dry Cheese",
    grade: "FAIL",
    metrics: {
      edgeHeight: { name: "Edge Height", value: 0.82, unit: "\"", min: 0.875, max: 1.0, progressVal: 65, status: "warning", display: "13/16\" (0.82\")" },
      edgeWidth: { name: "Edge Width", value: 1.05, unit: "\"", min: 1.0, max: 1.25, progressVal: 20, status: "pass", display: "1 1/16\" (1.05\")" },
      centerVolume: { name: "Center Volume", value: 0.38, unit: "\"", min: 0.375, max: 0.5, progressVal: 40, status: "pass", display: "3/8\" (0.38\")" },
      topColor: { name: "Top Crust Color", value: 12, unit: "/11", min: 7, max: 11, progressVal: 100, status: "fail", display: "12 (Severely blackened)" },
      bottomColor: { name: "Bottom Crust Color", value: 11, unit: "/10", min: 6, max: 10, progressVal: 100, status: "fail", display: "11 (Burnt bitter crust)" }
    },
    fix: "Symptom: Heavily charred crust, dried cheese, and slightly collapsed edge. Operational Root Cause: The oven conveyor belt is moving too slow, or the oven chamber temperature has spiked above standard range. **Remediation**: Verify oven temperature is set to 485°F (not exceeding 490°F). Increase conveyor belt speed by 15-20 seconds to reduce residence time in the baking chamber."
  }
};

// UI Elements Selection
const elements = {
  tabButtons: document.querySelectorAll('.nav-tab'),
  views: document.querySelectorAll('.tab-view'),
  chatMessages: document.getElementById('chatMessages'),
  chatInput: document.getElementById('chatInput'),
  sendBtn: document.getElementById('sendBtn'),
  scanBtn: document.getElementById('scanBtn'),
  cameraViewport: document.getElementById('cameraViewport'),
  cameraFeed: document.getElementById('cameraFeed'),
  pizzaCards: document.querySelectorAll('.pizza-card'),
  suggestionChips: document.querySelectorAll('.suggestion-chip'),
  
  // Dashboard Metrics
  kpiPassRate: document.getElementById('kpiPassRate'),
  kpiTotalScans: document.getElementById('kpiTotalScans'),
  kpiAlerts: document.getElementById('kpiAlerts'),
  
  // Table Body
  logsTableBody: document.getElementById('logsTableBody'),
  
  // SVG Containers
  trendChartWrapper: document.getElementById('trendChartWrapper'),
  defectChartWrapper: document.getElementById('defectChartWrapper')
};

// App Initialization
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  setupInitialChat();
  renderAnalytics();
});

// Event Listeners Registration
function setupEventListeners() {
  // Tab Switching
  elements.tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });

  // Pizza Preset Selection
  elements.pizzaCards.forEach(card => {
    btnFeedback(card);
    card.addEventListener('click', () => {
      elements.pizzaCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      const pizzaType = card.getAttribute('data-pizza');
      selectPizza(pizzaType);
    });
  });

  // Chat sending
  elements.sendBtn.addEventListener('click', handleUserMessage);
  elements.chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      handleUserMessage();
    }
  });

  // Suggestion Chips
  elements.suggestionChips.forEach(chip => {
    chip.addEventListener('click', () => {
      elements.chatInput.value = chip.textContent;
      elements.chatInput.focus();
    });
  });

  // Scan Button Trigger
  elements.scanBtn.addEventListener('click', runPizzaScanAnimation);
}

// Micro-vibration / Feedback
function btnFeedback(el) {
  el.addEventListener('mousedown', () => {
    el.style.transform = 'scale(0.98)';
  });
  el.addEventListener('mouseup', () => {
    el.style.transform = '';
  });
}

// Switch between Simulator & Analytics Views
function switchTab(tabId) {
  STATE.activeTab = tabId;
  
  elements.tabButtons.forEach(btn => {
    if (btn.getAttribute('data-tab') === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  elements.views.forEach(view => {
    if (view.id === `${tabId}View`) {
      view.classList.add('active');
    } else {
      view.classList.remove('active');
    }
  });

  if (tabId === 'analytics') {
    renderAnalytics();
  }
}

// Handle Image Preset Selection
function selectPizza(type) {
  STATE.selectedPizza = type;
  const profile = PIZZA_PROFILES[type];
  
  // Smooth opacity fade on feed image
  elements.cameraFeed.style.opacity = '0';
  setTimeout(() => {
    elements.cameraFeed.src = profile.image;
    elements.cameraFeed.style.opacity = '1';
  }, 200);

  // Update scanner overlay coordinates or metrics
  const statusBadge = document.querySelector('.scanner-stats-overlay .scanner-badge');
  if (statusBadge) {
    statusBadge.innerHTML = `<span class="status-dot" style="background-color: ${type === 'perfect' ? 'var(--color-success)' : 'var(--color-danger)'}; box-shadow: 0 0 8px ${type === 'perfect' ? 'var(--color-success)' : 'var(--color-danger)'}"></span> PRESET: ${profile.title}`;
  }
}

// Render the initial Greeting from the Agent
function setupInitialChat() {
  const welcomeText = `Hello! I am the **Slice & Rise Pizza Quality Agent**. 

I can instantly evaluate pizza quality against our brand standard rules. Please select a preset pizza on the right camera pane and click **"Scan Pizza"** to start the evaluation, or upload your own photo.

*Standards under evaluation:*
* **Edge Height**: 7/8" – 1" (Ideal thickness)
* **Edge Width**: 1" – 1 1/4" (Even stretching)
* **Center Volume**: 3/8" – 1/2" (Proper thickness)
* **Top Crust Color**: Scale of 7–11 (Perfect baking leopard spotting)
* **Bottom Crust Color**: Scale of 6–10 (Proper crisp browning)`;

  appendMessage('agent', welcomeText);
}

// Append a Message to Chat log
function appendMessage(sender, text, htmlContent = null) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${sender}`;
  
  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  if (sender === 'user') {
    avatar.textContent = 'OP';
  } else {
    avatar.innerHTML = `<svg viewBox="0 0 24 24"><path d="M12 2A10 10 0 0 0 2 12a10 10 0 0 0 10 10a10 10 0 0 0 10-10A10 10 0 0 0 12 2m0 2a8 8 0 0 1 8 8c0 1.25-.3 2.45-.81 3.5H16.5v-1.5a1.5 1.5 0 0 0-1.5-1.5h-3v-1.5a1.5 1.5 0 0 0-1.5-1.5H8.5V9.5A1.5 1.5 0 0 0 7 8H6c0-1.74 1.13-3.23 2.72-3.78L9 4.5A1.5 1.5 0 0 0 10.5 6h1.5M6.22 15.62l1.28-1.28c.31.25.71.41 1.15.41h1.85v1.5a1.5 1.5 0 0 0 1.5 1.5h1.5v1.84c-3.11-.27-5.75-2.22-6.78-4.97z"/></svg>`;
  }

  const wrapper = document.createElement('div');
  wrapper.style.display = 'flex';
  wrapper.style.flexDirection = 'col';
  
  const content = document.createElement('div');
  content.className = 'message-content';
  
  // Format basic markdown style bolding
  let formattedText = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
    
  content.innerHTML = formattedText;

  if (htmlContent) {
    content.appendChild(htmlContent);
  }

  const timeSpan = document.createElement('span');
  timeSpan.className = 'message-time';
  timeSpan.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  wrapper.appendChild(content);
  wrapper.appendChild(timeSpan);
  
  msgDiv.appendChild(avatar);
  msgDiv.appendChild(wrapper);
  
  elements.chatMessages.appendChild(msgDiv);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// Render Type-effect for Agent responses
function appendTypingIndicator() {
  const indicator = document.createElement('div');
  indicator.className = 'message agent temp-typing';
  indicator.innerHTML = `
    <div class="message-avatar">
      <svg viewBox="0 0 24 24"><path d="M12 2A10 10 0 0 0 2 12a10 10 0 0 0 10 10a10 10 0 0 0 10-10A10 10 0 0 0 12 2m0 2a8 8 0 0 1 8 8c0 1.25-.3 2.45-.81 3.5H16.5v-1.5a1.5 1.5 0 0 0-1.5-1.5h-3v-1.5a1.5 1.5 0 0 0-1.5-1.5H8.5V9.5A1.5 1.5 0 0 0 7 8H6c0-1.74 1.13-3.23 2.72-3.78L9 4.5A1.5 1.5 0 0 0 10.5 6h1.5M6.22 15.62l1.28-1.28c.31.25.71.41 1.15.41h1.85v1.5a1.5 1.5 0 0 0 1.5 1.5h1.5v1.84c-3.11-.27-5.75-2.22-6.78-4.97z"/></svg>
    </div>
    <div class="message-content typing-indicator">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>
  `;
  elements.chatMessages.appendChild(indicator);
  elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function removeTypingIndicator() {
  const indicator = document.querySelector('.temp-typing');
  if (indicator) {
    indicator.remove();
  }
}

// Run the Pizza Scan laser effect and triggers agent pipeline
function runPizzaScanAnimation() {
  if (STATE.isScanning) return;
  STATE.isScanning = true;
  
  elements.cameraViewport.classList.add('scanning');
  elements.scanBtn.disabled = true;
  elements.scanBtn.textContent = "Scanning Pizza...";

  // User says something in the chat simulating the upload
  const profile = PIZZA_PROFILES[STATE.selectedPizza];
  appendMessage('user', `Uploaded top-down pizza image. Running Quality Audit standard scan on [Preset: ${profile.title}].`);

  setTimeout(() => {
    // End scanning animation
    elements.cameraViewport.classList.remove('scanning');
    STATE.isScanning = false;
    elements.scanBtn.disabled = false;
    elements.scanBtn.textContent = "Scan Pizza";

    // Play visual feedback success sound/flash
    elements.cameraViewport.style.boxShadow = profile.grade === 'PASS' 
      ? 'var(--shadow-glow-success)' 
      : 'var(--shadow-glow-danger)';
    
    setTimeout(() => {
      elements.cameraViewport.style.boxShadow = '';
    }, 1000);

    // Feed to chat response
    appendTypingIndicator();
    
    setTimeout(() => {
      removeTypingIndicator();
      triggerA2UIResponse(STATE.selectedPizza);
    }, 1500);

  }, 2500); // 2.5s scan cycle
}

// Build and inject A2UI Scorecard into Chat
function triggerA2UIResponse(pizzaType) {
  const profile = PIZZA_PROFILES[pizzaType];
  
  // Save scan result to history (simulates BigQuery logging)
  const isPass = profile.grade === 'PASS';
  const newScan = {
    id: (1000 + STATE.scansHistory.length + 1).toString(),
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    date: new Date().toISOString().split('T')[0],
    grade: profile.grade,
    edgeHeight: profile.metrics.edgeHeight.value,
    edgeWidth: profile.metrics.edgeWidth.value,
    centerVolume: profile.metrics.centerVolume.value,
    topColor: profile.metrics.topColor.value,
    bottomColor: profile.metrics.bottomColor.value,
    failReason: isPass ? "" : (pizzaType === 'underbaked' ? "Underbaked" : "Overbaked"),
    gcsUri: `gs://slice_n_rise_scans/pizza_scan_${1000 + STATE.scansHistory.length + 1}.jpg`,
    userCorrected: false,
    verified: false,
    userMetrics: null
  };
  STATE.scansHistory.push(newScan);

  // Generate text explanation
  const textMsg = `Here are the results of the **Slice & Rise Standard Evaluation** for the analyzed pizza.

The visual analysis of the top-down pizza photo completed in **2.1s**. Our Multimodal Vision model has measured the physical geometry and crust color spectrum against your brand reference guide.

Overall Quality Grade: ${isPass ? '🟢 **PASS**' : '🔴 **FAIL**'}`;

  // Create A2UI Component HTML Structure
  const a2uiCard = document.createElement('div');
  a2uiCard.className = 'a2ui-component';
  
  // Header
  a2uiCard.innerHTML = `
    <div class="a2ui-header">
      <div class="a2ui-title">
        <svg style="width: 14px; height: 14px; fill: var(--text-secondary);" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2m-2 10H7v-2h10v2m0-4H7V7h10v2m0 8H7v-2h10v2z"/></svg>
        Live Standard Audit Scorecard
      </div>
      <span class="a2ui-protocol-tag" style="border-color: rgba(0, 122, 83, 0.3); color: var(--color-success); background: rgba(0, 122, 83, 0.1)">Gemini Integrated</span>
    </div>
  `;

  const body = document.createElement('div');
  body.className = 'a2ui-body';

  // Summary Row
  const summary = document.createElement('div');
  summary.className = 'scorecard-summary';
  summary.innerHTML = `
    <div class="scorecard-grade-badge ${isPass ? 'pass' : 'fail'}">
      ${isPass ? '✓ PASS' : '✗ FAIL'}
    </div>
    <div class="scorecard-store">
      Store ID <strong>#4021 (Vegas West)</strong>
      <div style="font-size: 11px; opacity: 0.8; margin-top: 2px;">
        QA Scan ID: #${newScan.id} | <span style="font-family: var(--font-mono); color: var(--color-primary-light);">gs://slice_n_rise_scans/pizza_scan_${newScan.id}.jpg</span>
      </div>
    </div>
  `;
  body.appendChild(summary);

  // Build metric rows
  Object.keys(profile.metrics).forEach(key => {
    const m = profile.metrics[key];
    const row = document.createElement('div');
    row.className = 'metric-row';
    
    // Status Badge
    let badgeClass = 'pass';
    let badgeLabel = 'PASS';
    if (m.status === 'warning') {
      badgeClass = 'warning';
      badgeLabel = 'WARN';
    } else if (m.status === 'fail') {
      badgeClass = 'fail';
      badgeLabel = 'FAIL';
    }

    row.innerHTML = `
      <div class="metric-info">
        <span class="metric-name">${m.name}</span>
        <span class="metric-badge ${badgeClass}">${m.display} - ${badgeLabel}</span>
      </div>
      <div class="metric-progress-wrapper">
        <div class="metric-progress-bar ${badgeClass}" style="width: ${m.progressVal}%"></div>
        <div class="metric-target-markers">
          <div class="target-zone" style="left: 30%; width: 45%;"></div>
        </div>
      </div>
      <div class="metric-values">
        <span>Min Standard: ${m.min}${m.unit}</span>
        <span>Max Standard: ${m.max}${m.unit}</span>
      </div>
    `;
    body.appendChild(row);
  });

  // Adding coaching tips inside scorecard if failed
  if (!isPass) {
    const coachDiv = document.createElement('div');
    coachDiv.className = 'coaching-card';
    coachDiv.innerHTML = `
      <div class="coaching-icon">
        <svg style="width: 16px; height: 16px; fill: currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
      </div>
      <div class="coaching-content">
        <h4>Operational Remediation Action</h4>
        <p>${profile.fix}</p>
      </div>
    `;
    body.appendChild(coachDiv);
  }

  // Create HITL Section inside the Card
  const hitlSection = document.createElement('div');
  hitlSection.className = 'hitl-section';
  hitlSection.innerHTML = `
    <div class="hitl-title">
      <svg style="width: 14px; height: 14px; fill: currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-4h-2V7h2v4z"/></svg>
      Human-in-the-Loop Validation (HITL)
    </div>
    <div class="hitl-prompt">Do you agree with the agent's evaluation and metric measurements?</div>
    <div class="hitl-buttons">
      <button class="hitl-btn agree">✓ Yes, Agree</button>
      <button class="hitl-btn disagree">✏️ No, Disagree</button>
    </div>
    <div class="hitl-correction-panel" style="display: none;">
      <div style="font-size: 11px; font-weight: bold; color: var(--text-secondary); margin-bottom: 5px;">ENTER CORRECTED OBSERVATIONS:</div>
      
      <div class="hitl-form-group">
        <div class="hitl-label-wrapper">
          <span class="hitl-label">Edge Height (standard: 0.875" - 1")</span>
          <span class="hitl-value" id="val_height">${newScan.edgeHeight.toFixed(2)}"</span>
        </div>
        <input type="range" class="hitl-slider" id="slider_height" min="0.4" max="1.2" step="0.01" value="${newScan.edgeHeight}">
      </div>

      <div class="hitl-form-group">
        <div class="hitl-label-wrapper">
          <span class="hitl-label">Edge Width (standard: 1" - 1.25")</span>
          <span class="hitl-value" id="val_width">${newScan.edgeWidth.toFixed(2)}"</span>
        </div>
        <input type="range" class="hitl-slider" id="slider_width" min="0.8" max="1.6" step="0.01" value="${newScan.edgeWidth}">
      </div>

      <div class="hitl-form-group">
        <div class="hitl-label-wrapper">
          <span class="hitl-label">Center Volume (standard: 0.375" - 0.5")</span>
          <span class="hitl-value" id="val_volume">${newScan.centerVolume.toFixed(2)}"</span>
        </div>
        <input type="range" class="hitl-slider" id="slider_volume" min="0.2" max="0.6" step="0.01" value="${newScan.centerVolume}">
      </div>

      <div class="hitl-form-group">
        <div class="hitl-label-wrapper">
          <span class="hitl-label">Top Crust Color (standard: 7 - 11)</span>
          <span class="hitl-value" id="val_topColor">${newScan.topColor}/11</span>
        </div>
        <input type="range" class="hitl-slider" id="slider_topColor" min="1" max="11" step="1" value="${newScan.topColor}">
      </div>

      <div class="hitl-form-group">
        <div class="hitl-label-wrapper">
          <span class="hitl-label">Bottom Crust Color (standard: 6 - 10)</span>
          <span class="hitl-value" id="val_bottomColor">${newScan.bottomColor}/10</span>
        </div>
        <input type="range" class="hitl-slider" id="slider_bottomColor" min="1" max="10" step="1" value="${newScan.bottomColor}">
      </div>

      <button class="hitl-submit-btn">Submit Corrective Rating & Update BigQuery</button>
    </div>
  `;
  body.appendChild(hitlSection);

  a2uiCard.appendChild(body);
  appendMessage('agent', textMsg, a2uiCard);

  // Setup HITL event handlers
  const btnAgree = hitlSection.querySelector('.hitl-btn.agree');
  const btnDisagree = hitlSection.querySelector('.hitl-btn.disagree');
  const correctionPanel = hitlSection.querySelector('.hitl-correction-panel');
  const submitBtn = hitlSection.querySelector('.hitl-submit-btn');

  const sliderHeight = hitlSection.querySelector('#slider_height');
  const sliderWidth = hitlSection.querySelector('#slider_width');
  const sliderVolume = hitlSection.querySelector('#slider_volume');
  const sliderTopColor = hitlSection.querySelector('#slider_topColor');
  const sliderBottomColor = hitlSection.querySelector('#slider_bottomColor');

  const valHeight = hitlSection.querySelector('#val_height');
  const valWidth = hitlSection.querySelector('#val_width');
  const valVolume = hitlSection.querySelector('#val_volume');
  const valTopColor = hitlSection.querySelector('#val_topColor');
  const valBottomColor = hitlSection.querySelector('#val_bottomColor');

  sliderHeight.addEventListener('input', (e) => { valHeight.textContent = parseFloat(e.target.value).toFixed(2) + '"'; });
  sliderWidth.addEventListener('input', (e) => { valWidth.textContent = parseFloat(e.target.value).toFixed(2) + '"'; });
  sliderVolume.addEventListener('input', (e) => { valVolume.textContent = parseFloat(e.target.value).toFixed(2) + '"'; });
  sliderTopColor.addEventListener('input', (e) => { valTopColor.textContent = e.target.value + '/11'; });
  sliderBottomColor.addEventListener('input', (e) => { valBottomColor.textContent = e.target.value + '/10'; });

  btnAgree.addEventListener('click', () => {
    btnAgree.disabled = true;
    btnDisagree.disabled = true;
    newScan.verified = true;
    newScan.userCorrected = false;
    
    const msg = document.createElement('div');
    msg.className = 'hitl-status-msg success';
    msg.innerHTML = `
      <svg style="width:16px; height:16px; fill:currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>
      Evaluation Verified! Record permanently stored as verified in BigQuery table.
    `;
    hitlSection.appendChild(msg);

    setTimeout(() => {
      appendMessage('agent', `Excellent! I have marked QA Scan ID **#${newScan.id}** as verified in BigQuery. The regional supervisor dashboard has been updated.`);
    }, 600);

    renderAnalytics();
  });

  btnDisagree.addEventListener('click', () => {
    correctionPanel.style.display = 'flex';
    btnDisagree.disabled = true;
  });

  submitBtn.addEventListener('click', () => {
    correctionPanel.style.display = 'none';
    btnAgree.disabled = true;
    btnDisagree.disabled = true;

    const h = parseFloat(sliderHeight.value);
    const w = parseFloat(sliderWidth.value);
    const v = parseFloat(sliderVolume.value);
    const tc = parseInt(sliderTopColor.value);
    const bc = parseInt(sliderBottomColor.value);

    // Calculate pass/fail status based on standards
    const passH = h >= 0.875 && h <= 1.0;
    const passW = w >= 1.0 && w <= 1.25;
    const passV = v >= 0.375 && v <= 0.5;
    const passTC = tc >= 7 && tc <= 11;
    const passBC = bc >= 6 && bc <= 10;

    const correctedIsPass = passH && passW && passV && passTC && passBC;

    // Record original machine metrics for reference
    newScan.machineMetrics = {
      edgeHeight: newScan.edgeHeight,
      edgeWidth: newScan.edgeWidth,
      centerVolume: newScan.centerVolume,
      topColor: newScan.topColor,
      bottomColor: newScan.bottomColor,
      grade: newScan.grade
    };

    // Update newScan metrics with human corrected ones
    newScan.edgeHeight = h;
    newScan.edgeWidth = w;
    newScan.centerVolume = v;
    newScan.topColor = tc;
    newScan.bottomColor = bc;
    newScan.grade = correctedIsPass ? 'PASS' : 'FAIL';
    newScan.userCorrected = true;
    newScan.verified = false;

    if (!correctedIsPass) {
      let reasons = [];
      if (!passH) reasons.push("Edge Height");
      if (!passW) reasons.push("Edge Width");
      if (!passV) reasons.push("Center Volume");
      if (!passTC) reasons.push("Top Crust Color");
      if (!passBC) reasons.push("Bottom Crust Color");
      newScan.failReason = reasons.join(" / ");
    } else {
      newScan.failReason = "";
    }

    const msg = document.createElement('div');
    msg.className = 'hitl-status-msg success';
    msg.style.borderColor = 'rgba(243, 208, 62, 0.3)';
    msg.style.background = 'rgba(243, 208, 62, 0.05)';
    msg.style.color = 'var(--color-warning)';
    msg.innerHTML = `
      <svg style="width:16px; height:16px; fill:currentColor" viewBox="0 0 24 24"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>
      Corrective Feedback Submitted! BigQuery record updated.
    `;
    hitlSection.appendChild(msg);

    // Let the agent speak conversational feedback
    setTimeout(() => {
      appendMessage('agent', `Got it! I have updated the telemetry in BigQuery for QA Scan ID **#${newScan.id}**.
      
An SQL \`UPDATE pizza_evaluations\` query was run to store your corrective human labels alongside the machine labels:
* **Human Rating**: Edge Height ${h.toFixed(2)}", Edge Width ${w.toFixed(2)}", Top Color ${tc}, Bottom Color ${bc} (${newScan.grade})
* **Machine Rating**: Edge Height ${newScan.machineMetrics.edgeHeight.toFixed(2)}", Edge Width ${newScan.machineMetrics.edgeWidth.toFixed(2)}", Top Color ${newScan.machineMetrics.topColor}, Bottom Color ${newScan.machineMetrics.bottomColor} (${newScan.machineMetrics.grade})

This unified record serves as training pair telemetry for model retraining.`);
    }, 600);

    renderAnalytics();
  });

  // If failed, add a short conversational prompt helping the user
  if (!isPass) {
    setTimeout(() => {
      appendMessage('agent', `Store Associate, please implement the **operational fix** detailed in the scorecard. I've automatically logged this fail-state to BigQuery and alerted the Shift Manager.`);
    }, 1000);
  } else {
    setTimeout(() => {
      appendMessage('agent', `Great job! This pizza is logged to BigQuery. Keep up this consistency for the lunch rush!`);
    }, 1000);
  }

  // Refresh dashboard behind the scenes!
  renderAnalytics();
}

// User text commands logic
function handleUserMessage() {
  const query = elements.chatInput.value.trim();
  if (!query) return;

  appendMessage('user', query);
  elements.chatInput.value = '';

  appendTypingIndicator();

  setTimeout(() => {
    removeTypingIndicator();
    processNaturalLanguageCommand(query);
  }, 1200);
}

// Process textual queries and commands from User
function processNaturalLanguageCommand(query) {
  const q = query.toLowerCase();

  if (q.includes('how are we doing') || q.includes('trends') || q.includes('bigquery') || q.includes('chart') || q.includes('performance')) {
    // Generate beautiful interactive trends dashboard chart inside chat!
    const textMsg = `Certainly! I've queried Google BigQuery on the fly for our last 7 days of performance trends for Store #4021. 

Here is our **Weekly Pass-Rate Dashboard** rendered natively using the **Interactive Dashboard Chart**:`;

    const chartCard = document.createElement('div');
    chartCard.className = 'a2ui-component';
    chartCard.innerHTML = `
      <div class="a2ui-header">
        <div class="a2ui-title">
          <svg style="width: 14px; height: 14px; fill: var(--text-secondary);" viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2m-2 10H7v-2h10v2m0-4H7V7h10v2m0 8H7v-2h10v2z"/></svg>
          Live Weekly Trends (BigQuery)
        </div>
        <span class="a2ui-protocol-tag" style="border-color: rgba(218, 41, 28, 0.3); color: var(--color-primary); background: rgba(218, 41, 28, 0.1)">Gemini Integrated</span>
      </div>
      <div class="a2ui-body" style="padding: 15px;">
        <div style="font-family: var(--font-display); font-size: 15px; font-weight:700; margin-bottom: 10px;">Store #4021 - Weekly Pass Rate Trends</div>
        <div style="height: 180px; width: 100%; position: relative;" id="chatTrendChartContainer"></div>
        <div style="font-size: 11px; color: var(--text-muted); text-align: center; margin-top: 5px;">
          Line: Store Pass Rate (%) • Dashed Line: Regional Target (85%)
        </div>
      </div>
    `;

    appendMessage('agent', textMsg, chartCard);
    
    // Dynamically draw the mini trends chart in the chat pane
    setTimeout(() => {
      drawTrendChartSVG('chatTrendChartContainer', 180, 480);
    }, 100);

  } else if (q.includes('standards') || q.includes('rules')) {
    appendMessage('agent', `Here is our exact **Slice & Rise Standard Guide** for corporate QA auditing:
    
1. **Edge Height**: Must measure between **7/8" (0.875") and 1"**. Over-proofed dough bubbles too high; under-proofed dough stays flat.
2. **Edge Width**: Must measure between **1" and 1.25"**. Too wide limits ingredient surface area; too narrow causes toppings to overflow.
3. **Center Volume**: Must measure between **3/8" (0.375") and 1/2" (0.5")** under cheese load.
4. **Top Crust Color**: Measured on a visual standard color-chart scale of **7 to 11** (vibrant golden brown with spotted black charring).
5. **Bottom Crust Color**: Measured on a visual scale of **6 to 10** (well cooked, crisp, not pale or ash black).`);
  } else if (q.includes('bottom') || q.includes('crust color') || q.includes('how did you get') || q.includes('check')) {
    appendMessage('agent', `Certainly! The **Bottom Crust Color** is evaluated by analyzing a photo of the pizza's underside (captured either by lifting the pizza or via our bottom-angle tray cameras) against the brand's standard visual reference spectrum of **Scale 6 to 10**. 

Our multimodal AI models process these images in real-time, checking for the ideal well-cooked, crisp, and mottled golden-brown appearance to ensure perfect baking consistency without charring.`);
  } else if (q.includes('help') || q.includes('what can I do')) {
    appendMessage('agent', `I can assist you with:
* Scanning a pizza's photo using the camera simulator on the right.
* Looking up real-time analytics from BigQuery. Ask me **"How are we doing this week?"** to see trend charts.
* Reviewing our corporate baked pizza specifications. Type **"Show standards"** for a full list of metrics.`);
  } else {
    // Default reply
    appendMessage('agent', `I've received your request! I'm listening. If you'd like to check our store quality performance trends, just ask **"How are we doing this week?"** or select one of the pizza presets on the right to perform a visual quality audit scan.`);
  }
}

// -----------------------------------------------------------------
// ANALYTICS & DASHBOARD ENGINE
// -----------------------------------------------------------------

function renderAnalytics() {
  const history = STATE.scansHistory;
  const total = history.length;
  
  // Calculate aggregate metrics
  const passes = history.filter(s => s.grade === 'PASS').length;
  const passRate = ((passes / total) * 100).toFixed(1);
  
  // Count defects
  const underbaked = history.filter(s => s.failReason === 'Underbaked').length;
  const overbaked = history.filter(s => s.failReason === 'Overbaked').length;
  
  // Update KPI cards
  elements.kpiTotalScans.textContent = total;
  elements.kpiPassRate.textContent = `${passRate}%`;
  elements.kpiAlerts.textContent = (underbaked + overbaked);

  // Redraw SVG charts
  drawTrendChartSVG('trendChartWrapper', 250, 600);
  drawDefectsChartSVG('defectChartWrapper', 250, 400);

  // Render logs table
  renderLogsTable();
}

// Render dynamic interactive Vega-Lite charts for Weekly Trends Chart
function drawTrendChartSVG(containerId, height, width) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const history = STATE.scansHistory;
  
  // Group history by date
  const dates = [...new Set(history.map(s => s.date))].sort().slice(-7);
  const data = dates.map(d => {
    const dayScans = history.filter(s => s.date === d);
    const dayPasses = dayScans.filter(s => s.grade === 'PASS').length;
    const rate = dayScans.length > 0 ? (dayPasses / dayScans.length) * 100 : 85;
    
    // Label format
    const parts = d.split('-');
    const label = `${parts[1]}/${parts[2]}`;
    return { date: label, pass_rate: Math.round(rate) };
  });

  const spec = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "background": "transparent",
    "width": "container",
    "height": height - 60,
    "padding": {"top": 10, "right": 10, "bottom": 10, "left": 10},
    "data": { "values": data },
    "encoding": {
      "x": {
        "field": "date",
        "type": "nominal",
        "axis": {
          "title": "Date",
          "titleColor": "#9ca3af",
          "labelColor": "#9ca3af",
          "gridColor": "rgba(255,255,255,0.05)",
          "labelAngle": 0,
          "labelFontSize": 9,
          "titleFontSize": 10,
          "tickColor": "rgba(255,255,255,0.1)",
          "domainColor": "rgba(255,255,255,0.1)"
        }
      }
    },
    "layer": [
      {
        "mark": {
          "type": "rule",
          "color": "#f59e0b",
          "strokeDash": [4, 4],
          "size": 1.5
        },
        "encoding": {
          "y": {
            "datum": 85,
            "type": "quantitative"
          }
        }
      },
      {
        "mark": {
          "type": "text",
          "text": "Target (85%)",
          "color": "#f59e0b",
          "fontSize": 9,
          "align": "right",
          "dx": -5,
          "dy": -6
        },
        "encoding": {
          "x": { "value": width - 60 },
          "y": { "datum": 85, "type": "quantitative" }
        }
      },
      {
        "mark": {
          "type": "line",
          "color": "#3b82f6",
          "strokeWidth": 3,
          "interpolate": "monotone"
        },
        "encoding": {
          "y": {
            "field": "pass_rate",
            "type": "quantitative",
            "scale": { "domain": [0, 100] },
            "axis": {
              "title": "Pass Rate (%)",
              "titleColor": "#9ca3af",
              "labelColor": "#9ca3af",
              "gridColor": "rgba(255,255,255,0.05)",
              "labelFontSize": 9,
              "titleFontSize": 10,
              "tickColor": "rgba(255,255,255,0.1)",
              "domainColor": "rgba(255,255,255,0.1)"
            }
          }
        }
      },
      {
        "mark": {
          "type": "circle",
          "color": "#00f0ff",
          "size": 60,
          "tooltip": true
        },
        "encoding": {
          "y": {
            "field": "pass_rate",
            "type": "quantitative"
          }
        }
      },
      {
        "mark": {
          "type": "text",
          "align": "center",
          "dy": -10,
          "color": "#fff",
          "fontWeight": "600",
          "fontSize": 9
        },
        "encoding": {
          "y": {
            "field": "pass_rate",
            "type": "quantitative"
          },
          "text": {
            "field": "pass_rate",
            "type": "quantitative"
          }
        }
      }
    ],
    "config": {
      "font": "Inter",
      "view": { "stroke": "transparent" }
    }
  };

  const embedOpts = {
    "actions": false,
    "theme": "dark",
    "renderer": "svg"
  };

  if (typeof vegaEmbed !== 'undefined') {
    vegaEmbed(`#${containerId}`, spec, embedOpts).catch(err => {
      console.error("Vega-Lite error:", err);
    });
  } else {
    container.innerHTML = `<div style="color:var(--text-muted); font-size:11px; padding:10px;">Loading Vega-Lite Chart...</div>`;
  }
}

// Render dynamic interactive Vega-Lite Failures Breakdown Chart (Bar Chart)
function drawDefectsChartSVG(containerId, height, width) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const history = STATE.scansHistory;
  
  // Counts
  const metricsFails = {
    "Edge Height": history.filter(s => s.edgeHeight < 0.875 || s.edgeHeight > 1.0).length,
    "Edge Width": history.filter(s => s.edgeWidth < 1.0 || s.edgeWidth > 1.25).length,
    "Center Vol": history.filter(s => s.centerVolume < 0.375 || s.centerVolume > 0.5).length,
    "Top Color": history.filter(s => s.topColor < 7 || s.topColor > 11).length,
    "Bottom Color": history.filter(s => s.bottomColor < 6 || s.bottomColor > 10).length
  };

  const data = Object.keys(metricsFails).map(key => {
    return { category: key, count: metricsFails[key] };
  });

  const spec = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "background": "transparent",
    "width": "container",
    "height": height - 60,
    "padding": {"top": 10, "right": 10, "bottom": 10, "left": 10},
    "data": { "values": data },
    "layer": [
      {
        "mark": {
          "type": "bar",
          "color": {
            "x1": 1, "y1": 1, "x2": 1, "y2": 0,
            "gradient": "linear",
            "stops": [
              { "offset": 0, "color": "#3b82f6" },
              { "offset": 1, "color": "#ef4444" }
            ]
          },
          "cornerRadiusEnd": 4
        },
        "encoding": {
          "x": {
            "field": "category",
            "type": "nominal",
            "axis": {
              "title": "Defect Category",
              "titleColor": "#9ca3af",
              "labelColor": "#9ca3af",
              "labelAngle": -15,
              "labelFontSize": 9,
              "titleFontSize": 10,
              "tickColor": "rgba(255,255,255,0.1)",
              "domainColor": "rgba(255,255,255,0.1)",
              "grid": false
            }
          },
          "y": {
            "field": "count",
            "type": "quantitative",
            "axis": {
              "title": "Occurrences",
              "titleColor": "#9ca3af",
              "labelColor": "#9ca3af",
              "gridColor": "rgba(255,255,255,0.05)",
              "labelFontSize": 9,
              "titleFontSize": 10,
              "tickColor": "rgba(255,255,255,0.1)",
              "domainColor": "rgba(255,255,255,0.1)",
              "tickMinStep": 1
            }
          }
        }
      },
      {
        "mark": {
          "type": "text",
          "align": "center",
          "baseline": "bottom",
          "dy": -5,
          "color": "#fff",
          "fontWeight": "600",
          "fontSize": 9
        },
        "encoding": {
          "x": { "field": "category", "type": "nominal" },
          "y": { "field": "count", "type": "quantitative" },
          "text": { "field": "count", "type": "quantitative" }
        }
      }
    ],
    "config": {
      "font": "Inter",
      "view": { "stroke": "transparent" }
    }
  };

  const embedOpts = {
    "actions": false,
    "theme": "dark",
    "renderer": "svg"
  };

  if (typeof vegaEmbed !== 'undefined') {
    vegaEmbed(`#${containerId}`, spec, embedOpts).catch(err => {
      console.error("Vega-Lite error:", err);
    });
  } else {
    container.innerHTML = `<div style="color:var(--text-muted); font-size:11px; padding:10px;">Loading Vega-Lite Chart...</div>`;
  }
}

// Render dynamic Log Tables for previous evaluations
function renderLogsTable() {
  const history = [...STATE.scansHistory].reverse(); // latest first
  elements.logsTableBody.innerHTML = '';

  history.forEach(log => {
    const tr = document.createElement('tr');
    
    // Status Badge & HITL status badge
    let statusHTML = `<span class="metric-badge ${log.grade === 'PASS' ? 'pass' : 'fail'}">${log.grade}</span>`;
    if (log.userCorrected) {
      statusHTML += `<div style="font-size: 10px; color: var(--color-warning); margin-top: 4px; font-weight: 600; display: flex; align-items: center; gap: 3px;">✏️ HITL Corrected</div>`;
    } else if (log.verified) {
      statusHTML += `<div style="font-size: 10px; color: var(--color-success); margin-top: 4px; font-weight: 600; display: flex; align-items: center; gap: 3px;">🟢 HITL Verified</div>`;
    } else {
      statusHTML += `<div style="font-size: 10px; color: var(--text-muted); margin-top: 4px; display: flex; align-items: center; gap: 3px;">🤖 AI Rated</div>`;
    }

    // Measurements detail (Original AI and Corrected Human if modified)
    let measurementsHTML = ``;
    if (log.userCorrected && log.machineMetrics) {
      measurementsHTML = `
        <div style="font-size: 11px; opacity: 0.7; text-decoration: line-through; color: var(--text-muted);">
          AI: ${log.machineMetrics.edgeHeight.toFixed(2)}", ${log.machineMetrics.edgeWidth.toFixed(2)}", T:${log.machineMetrics.topColor}/B:${log.machineMetrics.bottomColor}
        </div>
        <div style="font-size: 11px; color: var(--color-warning); font-weight: 600; margin-top: 2px;">
          Human: ${log.edgeHeight.toFixed(2)}", ${log.edgeWidth.toFixed(2)}", T:${log.topColor}/B:${log.bottomColor}
        </div>
      `;
    } else {
      measurementsHTML = `
        <span style="color: var(--text-secondary)">
          ${log.edgeHeight.toFixed(2)}", ${log.edgeWidth.toFixed(2)}", T:${log.topColor}/B:${log.bottomColor}
        </span>
      `;
    }

    tr.innerHTML = `
      <td>
        <strong>#${log.id}</strong>
        <div style="font-family: var(--font-mono); font-size: 9px; color: var(--text-muted); margin-top: 3px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${log.gcsUri}">
          ${log.gcsUri}
        </div>
      </td>
      <td style="font-family: var(--font-mono); font-size: 11px;">${log.date} ${log.time}</td>
      <td>${statusHTML}</td>
      <td>
        ${log.grade === 'PASS' ? '<span style="color: var(--text-muted)">-</span>' : `<span style="color: var(--color-warning)">${log.failReason} defect</span>`}
      </td>
      <td>${measurementsHTML}</td>
    `;
    elements.logsTableBody.appendChild(tr);
  });
}
