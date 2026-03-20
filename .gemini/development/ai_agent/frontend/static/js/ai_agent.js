function toggleAiAgent() {
    const win = document.getElementById('ai-agent-window');
    win.style.display = (win.style.display === 'none' || win.style.display === '') ? 'flex' : 'none';
}

function minimizeAiAgent() {
    const win = document.getElementById('ai-agent-window');
    const container = document.querySelector('.ai-agent-main-container');
    const footer = document.getElementById('ai-agent-footer');
    if (container.style.display === 'none') {
        container.style.display = 'flex';
        footer.style.display = 'flex';
        win.style.height = '600px';
    } else {
        container.style.display = 'none';
        footer.style.display = 'none';
        win.style.height = 'auto';
    }
}

function maximizeAiAgent() {
    const win = document.getElementById('ai-agent-window');
    if (win.style.width === '100%') {
        win.style.width = '800px';
        win.style.height = '600px';
        win.style.bottom = '20px';
        win.style.right = '20px';
        win.style.borderRadius = '12px';
    } else {
        win.style.width = '100%';
        win.style.height = '100%';
        win.style.bottom = '0';
        win.style.right = '0';
        win.style.borderRadius = '0';
    }
}

async function sendAiMessage() {
    const input = document.getElementById('ai-agent-input');
    const query = input.value.trim();
    if (!query) return;

    appendChatMessage('user', query);
    input.value = '';

    const loadingId = 'loading-' + Date.now();
    appendChatMessage('agent', '<span class="loading-dots">Thinking</span>', loadingId);

    try {
        const response = await fetch('/ai-agent/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await response.json();
        
        const loadingIndicator = document.getElementById(loadingId);
        if (loadingIndicator) {
            loadingIndicator.remove();
        }

        if (data.text) {
            // Apply newline-to-BR only to the AI text part
            let htmlResponse = data.text.replace(/\n/g, '<br>');
            if (data.results && data.results.length > 0) {
                htmlResponse += renderResultsTable(data.results, data.object_type);
            }
            appendChatMessage('agent', htmlResponse);
        } else {
            appendChatMessage('agent', "I'm sorry, I couldn't process that request.");
        }
    } catch (error) {
        console.error("AI Agent Error:", error);
        const loadingIndicator = document.getElementById(loadingId);
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
        appendChatMessage('agent', "Sorry, I encountered an error connecting to the AI service.");
    }
}

function appendChatMessage(role, content, id = null) {
    const body = document.getElementById('ai-agent-body');
    if (!body) return;
    
    // Convert [Action Name] into clickable buttons if it's from the agent
    if (role === 'agent') {
        content = content.replace(/\[([^\]]+)\]/g, (match, p1) => {
            return `<button class="btn" style="padding: 4px 12px; margin: 4px; font-size: 0.75rem; border-radius: 12px; background: white; border: 1px solid #0176d3; color: #0176d3; cursor: pointer;" onclick="sendQuickMessage('${p1}')">${p1}</button>`;
        });
    }

    const msgDiv = document.createElement('div');
    msgDiv.style.display = 'flex';
    msgDiv.style.gap = '10px';
    msgDiv.style.alignSelf = role === 'user' ? 'flex-end' : 'flex-start';
    msgDiv.style.marginBottom = '10px';
    if (id) msgDiv.id = id;

    if (role === 'agent') {
        msgDiv.innerHTML = `
            <div style="width: 28px; height: 28px; background: #0176d3; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; font-size: 0.8rem;">🤖</div>
            <div style="background: white; padding: 12px; border-radius: 0 12px 12px 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); font-size: 0.9rem; line-height: 1.4; max-width: 85%;">
                ${content}
            </div>
        `;
    } else {
        msgDiv.innerHTML = `
            <div style="background: #eef4ff; color: #16325c; padding: 12px; border-radius: 12px 12px 0 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); font-size: 0.9rem; line-height: 1.4; max-width: 85%;">
                ${content}
            </div>
        `;
    }
    body.appendChild(msgDiv);
    
    // Improved auto-scroll
    setTimeout(() => {
        msgDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 100);
}

function sendQuickMessage(text) {
    const input = document.getElementById('ai-agent-input');
    if (!input) return;
    input.value = text;
    sendAiMessage();
}

function renderResultsTable(results, objectType) {
    if (!results || results.length === 0) return "";
    
    let html = '<div style="margin-top: 10px; overflow-x: auto; border: 1px solid #ddd; border-radius: 4px; background: white;">';
    html += '<table style="width: 100%; border-collapse: collapse; font-size: 0.8rem;">';
    
    const keys = Object.keys(results[0]).filter(k => !['id', 'created_at', 'updated_at', 'deleted_at', 'record_id'].includes(k));
    html += '<tr style="background: #f8f9fb; border-bottom: 1px solid #ddd;">';
    keys.forEach(k => html += `<th style="padding: 6px; text-align: left; color: #555; white-space: nowrap;">${k.replace('_', ' ').toUpperCase()}</th>`);
    html += '</tr>';

    results.forEach(row => {
        const rowId = row.id || row.ID || "";
        html += `<tr style="border-bottom: 1px solid #eee; cursor: pointer; transition: background 0.2s;" 
                    onclick="selectAgentRecord('${rowId}', '${objectType}')"
                    onmouseover="this.style.background='#f0f7ff'" 
                    onmouseout="this.style.background='transparent'">`;
        keys.forEach(k => {
            let val = row[k] || "-";
            if (k === 'name' || k === 'first_name') {
                html += `<td style="padding: 6px;"><strong style="color: #0176d3;">${val}</strong></td>`;
            } else {
                html += `<td style="padding: 6px;">${val}</td>`;
            }
        });
        html += '</tr>';
    });
    
    html += '</table></div>';
    return html;
}

function selectAgentRecord(recordId, objectType) {
    if (!recordId) return;
    const input = document.getElementById('ai-agent-input');
    input.value = `Manage ${objectType} ${recordId}`;
    sendAiMessage();
}

async function startAiRecommend(btn) {
    const originalText = btn.innerText;
    btn.innerText = "Processing...";
    btn.disabled = true;
    const container = document.getElementById('ai-recommendation-results');
    
    try {
        const response = await fetch('/api/recommendations');
        if (response.ok) {
            const html = await response.text();
            if (html.includes('sidebar-column')) {
                console.error("Received full page instead of fragment. Redirection detected.");
                container.innerHTML = '<div class="sf-card" style="padding:1rem;color:var(--error);text-align:center;">Error: Received invalid recommendation data.</div>';
            } else {
                container.innerHTML = html;
            }
            container.style.display = 'block';
            if (typeof showToast === 'function') showToast("AI Recommendations updated successfully!");
        } else {
            if (typeof showToast === 'function') showToast("Server error loading recommendations.", true);
        }
    } catch (error) { 
        console.error(error); 
        if (typeof showToast === 'function') showToast("Network error loading recommendations.", true);
    }
    finally { btn.innerText = originalText; btn.disabled = false; }
}
