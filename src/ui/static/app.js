// HR Agentic System - Chat UI Logic

const sessionId = 'session_' + Math.random().toString(36).substring(2, 9);
const messagesList = document.getElementById('messagesList');
const messageInput = document.getElementById('messageInput');
const chatForm = document.getElementById('chatForm');
const healthBadge = document.getElementById('healthBadge');
const healthText = document.getElementById('healthText');
const toggleTraceBtn = document.getElementById('toggleTraceBtn');
const closeTraceBtn = document.getElementById('closeTraceBtn');
const tracePanel = document.getElementById('tracePanel');
const traceEntries = document.getElementById('traceEntries');
const traceEmptyState = document.getElementById('traceEmptyState');
const citationsList = document.getElementById('citationsList');
const traceCounterBadge = document.getElementById('traceCounterBadge');

// Health Check Polling
async function checkHealth() {
  try {
    const res = await fetch('/health');
    const data = await res.json();
    if (data.mcp_connected && data.status === 'healthy') {
      healthBadge.className = 'status-badge healthy';
      healthText.textContent = `MCP Connected • ${data.tools_discovered} Tools (${data.response_time_ms}ms)`;
    } else {
      healthBadge.className = 'status-badge degraded';
      healthText.textContent = 'MCP Degraded';
    }
  } catch (err) {
    healthBadge.className = 'status-badge degraded';
    healthText.textContent = 'Server Offline';
  }
}

checkHealth();
setInterval(checkHealth, 15000);

// Trace Panel Toggle
toggleTraceBtn.addEventListener('click', () => {
  tracePanel.classList.toggle('collapsed');
});

closeTraceBtn.addEventListener('click', () => {
  tracePanel.classList.add('collapsed');
});

// Quick Prompts
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    messageInput.value = chip.dataset.prompt;
    chatForm.dispatchEvent(new Event('submit'));
  });
});

// Auto-expand textarea
messageInput.addEventListener('input', () => {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
});

messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event('submit'));
  }
});

// Basic Markdown Formatter
function renderMarkdown(text) {
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3 style="color:#38bdf8;margin:8px 0 4px 0;font-size:1rem;">$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2 style="color:#818cf8;margin:10px 0 4px 0;font-size:1.1rem;">$1</h2>');
  // Checkbox / list items
  html = html.replace(/^- \[x\] (.*$)/gim, '<li style="list-style:none;">✅ $1</li>');
  html = html.replace(/^- \[ \] (.*$)/gim, '<li style="list-style:none;">❌ $1</li>');
  html = html.replace(/^- \[\!\] (.*$)/gim, '<li style="list-style:none;">⚠️ $1</li>');
  html = html.replace(/^- (.*$)/gim, '<li>$1</li>');
  // Numbered list
  html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>');
  // Paragraphs
  html = html.replace(/\n\n/g, '</p><p>');

  return `<p>${html}</p>`;
}

// Append Message to UI
function appendMessage(sender, text, isUser = false) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;

  const avatarDiv = document.createElement('div');
  avatarDiv.className = `avatar ${isUser ? 'user-avatar' : 'assistant-avatar'}`;
  avatarDiv.textContent = isUser ? 'You' : 'HR';

  const bubbleDiv = document.createElement('div');
  bubbleDiv.className = 'message-bubble';

  const headerDiv = document.createElement('div');
  headerDiv.className = 'bubble-header';
  const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  headerDiv.innerHTML = `<span class="sender-name">${isUser ? 'You' : 'HR Agentic Assistant'}</span><span class="time-label">${timeStr}</span>`;

  const bodyDiv = document.createElement('div');
  bodyDiv.className = 'bubble-body';
  bodyDiv.innerHTML = isUser ? `<p>${text}</p>` : renderMarkdown(text);

  // If action confirmation is in text, render action buttons
  if (!isUser && text.includes('[ACTION CONFIRMATION REQUIRED]')) {
    const actionsDiv = document.createElement('div');
    actionsDiv.style.marginTop = '12px';
    actionsDiv.style.display = 'flex';
    actionsDiv.style.gap = '10px';
    actionsDiv.innerHTML = `
      <button onclick="sendQuickReply('Confirm')" style="background:#10b981;border:none;color:#fff;padding:6px 16px;border-radius:6px;font-weight:600;cursor:pointer;">Confirm Action</button>
      <button onclick="sendQuickReply('Cancel')" style="background:#ef4444;border:none;color:#fff;padding:6px 16px;border-radius:6px;font-weight:600;cursor:pointer;">Cancel</button>
    `;
    bodyDiv.appendChild(actionsDiv);
  }

  bubbleDiv.appendChild(headerDiv);
  bubbleDiv.appendChild(bodyDiv);
  msgDiv.appendChild(avatarDiv);
  msgDiv.appendChild(bubbleDiv);

  messagesList.appendChild(msgDiv);
  messagesList.scrollTop = messagesList.scrollHeight;
  return msgDiv;
}

window.sendQuickReply = function(replyText) {
  messageInput.value = replyText;
  chatForm.dispatchEvent(new Event('submit'));
};

// Update Operational Trace & Citations
function updateTracePanel(trace, citations, snippets) {
  traceCounterBadge.textContent = trace.length;
  traceEntries.innerHTML = '';
  citationsList.innerHTML = '';

  if (trace.length === 0) {
    traceEmptyState.style.display = 'block';
  } else {
    traceEmptyState.style.display = 'none';
    trace.forEach((step, idx) => {
      const card = document.createElement('div');
      card.className = 'trace-card';
      card.innerHTML = `
        <div class="trace-card-header">
          <span class="tool-badge">Step ${step.step}: ${step.tool_name}</span>
          <span class="duration-tag">${step.duration_ms || 0}ms</span>
        </div>
        <div class="trace-details">
          <p style="font-size:0.74rem;color:#94a3b8;margin-bottom:2px;">Arguments:</p>
          <pre>${JSON.stringify(step.arguments, null, 2)}</pre>
          <p style="font-size:0.74rem;color:#94a3b8;margin:4px 0 2px 0;">Output:</p>
          <pre>${JSON.stringify(step.output, null, 2)}</pre>
        </div>
      `;
      traceEntries.appendChild(card);
    });
  }

  if (citations.length === 0) {
    citationsList.innerHTML = '<p class="empty-note">No specific policy citations retrieved for this response.</p>';
  } else {
    citations.forEach(c => {
      const citCard = document.createElement('div');
      citCard.className = 'citation-card';
      citCard.innerHTML = `
        <div class="citation-title">[${c.document_id || 'DOC'}] ${c.document_title}</div>
        <div class="citation-section">Section: ${c.section}</div>
        <div class="citation-snippet">"${c.snippet}"</div>
      `;
      citationsList.appendChild(citCard);
    });
  }
}

// Form Submission
chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;

  // Append user message
  appendMessage('You', text, true);
  messageInput.value = '';
  messageInput.style.height = 'auto';

  // Loading state
  const loadingIndicator = appendMessage('HR', '<em>Thinking, searching policy index & orchestrating tools...</em>', false);

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: sessionId })
    });

    const data = await res.json();
    loadingIndicator.remove();

    if (!res.ok) {
      appendMessage('HR', `**Error (${res.status}):** ${data.detail || 'Failed to complete request.'}`);
      return;
    }

    appendMessage('HR', data.answer, false);
    updateTracePanel(data.tool_call_trace, data.citations, data.snippets);

  } catch (err) {
    loadingIndicator.remove();
    appendMessage('HR', `**Network Error:** Could not connect to HR backend: ${err.message}`);
  }
});
