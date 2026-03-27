const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const resetBtn = document.getElementById('reset-btn');

let conversationId = 'conv_' + Math.random().toString(36).substr(2, 9);

function appendMessage(role, content, data = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    let innerHTML = `<div class="message-content">${content}</div>`;
    
    if (data) {
        if (data.results && data.results.length > 0) {
            innerHTML += buildTableView(data.results, data.pagination?.object_type);
        } else if (data.card) {
            innerHTML += buildCardView(data.card);
        }
    }
    
    messageDiv.innerHTML = innerHTML;
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function buildTableView(results, objectType) {
    if (!results || results.length === 0) return '';
    
    const headers = Object.keys(results[0]).filter(k => k !== 'id');
    let html = '<div class="table-container"><table class="agent-table"><thead><tr>';
    
    headers.forEach(h => {
        html += `<th>${h.replace('_', ' ').toUpperCase()}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    results.forEach(row => {
        html += '<tr>';
        headers.forEach(h => {
            html += `<td>${row[h] || ''}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    return html;
}

function buildCardView(card) {
    let html = `
        <div class="record-card">
            <div class="card-header">
                <div class="card-title">${card.title || 'Record Detail'}</div>
                <div class="card-subtitle" style="font-size: 0.8rem; color: #666;">${card.subtitle || ''}</div>
            </div>
            <div class="card-body">
    `;
    
    if (card.fields) {
        card.fields.forEach(f => {
            html += `
                <div class="card-field">
                    <div class="field-label">${f.label}</div>
                    <div class="field-value">${f.value || ''}</div>
                </div>
            `;
        });
    }
    
    html += '</div>';
    
    if (card.actions) {
        html += '<div class="card-actions">';
        card.actions.forEach(a => {
            html += `<button class="action-btn ${a.tone === 'primary' ? 'primary' : ''}" onclick="handleAction('${a.action}', '${card.record_id}', '${card.object_type}')">${a.label}</button>`;
        });
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

async function sendQuery(query) {
    if (!query) return;
    
    appendMessage('user', query);
    userInput.value = '';
    
    try {
        const response = await fetch('/agent-gem/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                conversation_id: conversationId
            })
        });
        
        const data = await response.json();
        appendMessage('agent', data.text || 'Done.', data);
    } catch (error) {
        appendMessage('agent', 'Error: ' + error.message);
    }
}

function handleAction(action, recordId, objectType) {
    if (action === 'open') {
        window.open(`/${objectType}s/${recordId}`, '_blank');
    } else if (action === 'edit') {
        sendQuery(`Edit ${objectType} ${recordId}`);
    } else if (action === 'delete') {
        sendQuery(`Delete ${objectType} ${recordId}`);
    }
}

sendBtn.addEventListener('click', () => sendQuery(userInput.value));
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendQuery(userInput.value);
});

resetBtn.addEventListener('click', () => {
    conversationId = 'conv_' + Math.random().toString(36).substr(2, 9);
    chatWindow.innerHTML = `
        <div class="message agent-message">
            <div class="message-content">
                Conversation reset. How can I help you now?
                <div class="quick-actions">
                    <button class="quick-btn" onclick="sendQuery('Show all leads')">All Leads</button>
                    <button class="quick-btn" onclick="sendQuery('Show all contacts')">All Contacts</button>
                    <button class="quick-btn" onclick="sendQuery('Show all opportunities')">All Opportunities</button>
                </div>
            </div>
        </div>
    `;
});
