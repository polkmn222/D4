let opsPilotOpen = false;
let opsPilotBootstrapped = false;
let opsPilotBootstrap = null;

async function toggleOpsPilot() {
    if (opsPilotOpen) {
        closeOpsPilot();
        return;
    }
    await openOpsPilot();
}

async function openOpsPilot() {
    const root = document.getElementById('ops-pilot-root');
    if (!root) {
        return;
    }

    root.innerHTML = '';
    const panelResponse = await fetch('/agent-panel');
    root.innerHTML = await panelResponse.text();
    root.classList.remove('ops-pilot-hidden');
    opsPilotOpen = true;
    await bootstrapOpsPilot();
}

function closeOpsPilot() {
    const root = document.getElementById('ops-pilot-root');
    if (!root) {
        return;
    }
    root.innerHTML = '';
    opsPilotOpen = false;
    opsPilotBootstrapped = false;
    opsPilotBootstrap = null;
}

async function bootstrapOpsPilot() {
    if (opsPilotBootstrapped) {
        return;
    }

    const response = await fetch('/agent/api/bootstrap');
    opsPilotBootstrap = await response.json();
    opsPilotBootstrapped = true;

    const title = document.getElementById('ops-pilot-shell-title');
    const commandInput = document.getElementById('ops-pilot-command');
    const promptList = document.getElementById('ops-pilot-prompt-list');
    const objectButtons = document.getElementById('ops-pilot-object-buttons');

    if (title) {
        title.textContent = opsPilotBootstrap.brand_name;
    }
    if (commandInput) {
        commandInput.value = opsPilotBootstrap.default_command;
        commandInput.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                submitOpsPilotCommand();
            }
        });
    }
    if (promptList) {
        promptList.innerHTML = opsPilotBootstrap.starter_prompts
            .map(function (prompt) {
                return '<button type="button" class="ops-pilot-chip" onclick="runOpsPilotPrompt(\'' + escapeOpsPilotHtml(prompt) + '\')">' + escapeOpsPilotHtml(prompt) + '</button>';
            })
            .join('');
    }
    if (objectButtons) {
        objectButtons.innerHTML = opsPilotBootstrap.supported_objects
            .map(function (item) {
                return '<button type="button" class="ops-pilot-object-btn" onclick="runOpsPilotPrompt(\'all ' + escapeOpsPilotHtml(item.plural_label.toLowerCase()) + '\')">' + escapeOpsPilotHtml(item.label) + '</button>';
            })
            .join('');
    }

    appendOpsPilotCard('assistant', opsPilotBootstrap.welcome_message);
    await submitOpsPilotCommand();
}

function runOpsPilotPrompt(prompt) {
    const commandInput = document.getElementById('ops-pilot-command');
    if (!commandInput) {
        return;
    }
    commandInput.value = prompt;
    submitOpsPilotCommand();
}

async function submitOpsPilotCommand() {
    const commandInput = document.getElementById('ops-pilot-command');
    if (!commandInput) {
        return;
    }

    const command = commandInput.value.trim();
    if (!command) {
        return;
    }

    setOpsPilotStatus('Running command...');
    appendOpsPilotCard('user', command);

    const response = await fetch('/agent/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: command }),
    });
    const payload = await response.json();
    appendOpsPilotCard('assistant', payload.message, payload.examples || []);

    if (payload.status === 'success' && payload.workspace_url) {
        const frame = document.getElementById('ops-pilot-frame');
        if (frame) {
            frame.src = payload.workspace_url;
        }
    }

    setOpsPilotStatus(payload.message || 'Ready.');
}

function setOpsPilotStatus(message) {
    const status = document.getElementById('ops-pilot-status');
    if (status) {
        status.textContent = message;
    }
}

function appendOpsPilotCard(role, message, examples = []) {
    const transcript = document.getElementById('ops-pilot-transcript');
    if (!transcript) {
        return;
    }

    const exampleMarkup = examples.length
        ? '<div class="agent-example-list">' + examples.map(function (example) {
            return '<button type="button" class="ops-pilot-chip" onclick="runOpsPilotPrompt(\'' + escapeOpsPilotHtml(example) + '\')">' + escapeOpsPilotHtml(example) + '</button>';
        }).join('') + '</div>'
        : '';

    const card = document.createElement('article');
    card.className = role === 'user' ? 'agent-paste-card agent-paste-card-user' : 'agent-paste-card';
    card.innerHTML = '<p class="agent-paste-eyebrow">' + (role === 'user' ? 'You' : 'Agent') + '</p><p>' + escapeOpsPilotHtml(message) + '</p>' + exampleMarkup;
    transcript.appendChild(card);
    transcript.scrollTop = transcript.scrollHeight;
}

function escapeOpsPilotHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

window.toggleOpsPilot = toggleOpsPilot;
window.closeOpsPilot = closeOpsPilot;
window.submitOpsPilotCommand = submitOpsPilotCommand;
window.runOpsPilotPrompt = runOpsPilotPrompt;
