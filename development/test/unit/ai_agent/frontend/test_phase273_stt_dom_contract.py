import subprocess
import textwrap
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[4]
JS_PATH = BASE_DIR / "ai_agent" / "ui" / "frontend" / "static" / "js" / "ai_agent.js"
TEMPLATE_PATH = BASE_DIR / "ai_agent" / "ui" / "frontend" / "templates" / "ai_agent_panel.html"


def _run_node_dom_test(test_body: str) -> None:
    script = textwrap.dedent(
        f"""
        const fs = require('fs');
        const vm = require('vm');

        const source = fs.readFileSync({str(JS_PATH)!r}, 'utf8');

        function createHarness() {{
            const elements = new Map();

            class FakeClassList {{
                constructor(owner) {{
                    this.owner = owner;
                    this.tokens = new Set();
                }}
                _sync() {{
                    this.owner.className = Array.from(this.tokens).join(' ');
                }}
                add(...names) {{
                    names.forEach(name => this.tokens.add(name));
                    this._sync();
                }}
                remove(...names) {{
                    names.forEach(name => this.tokens.delete(name));
                    this._sync();
                }}
                contains(name) {{
                    return this.tokens.has(name);
                }}
                toggle(name, force) {{
                    if (force === true) this.tokens.add(name);
                    else if (force === false) this.tokens.delete(name);
                    else if (this.tokens.has(name)) this.tokens.delete(name);
                    else this.tokens.add(name);
                    this._sync();
                    return this.tokens.has(name);
                }}
            }}

            class FakeElement {{
                constructor(tagName = 'div', id = '') {{
                    this.tagName = tagName.toUpperCase();
                    this.children = [];
                    this.parentNode = null;
                    this.dataset = {{}};
                    this.style = {{}};
                    this.attributes = {{}};
                    this.className = '';
                    this.classList = new FakeClassList(this);
                    this.value = '';
                    this.innerHTML = '';
                    this.textContent = '';
                    this.disabled = false;
                    this.id = id;
                    this.focusCalls = 0;
                }}
                appendChild(child) {{
                    child.parentNode = this;
                    this.children.push(child);
                    if (child.id) elements.set(child.id, child);
                    return child;
                }}
                remove() {{
                    if (!this.parentNode) return;
                    this.parentNode.children = this.parentNode.children.filter(child => child !== this);
                    if (this.id) elements.delete(this.id);
                }}
                querySelector(selector) {{
                    if (selector.startsWith('#')) return elements.get(selector.slice(1)) || null;
                    return null;
                }}
                querySelectorAll() {{
                    return [];
                }}
                setAttribute(name, value) {{
                    this.attributes[name] = value;
                    if (name === 'id') this.id = value;
                }}
                getAttribute(name) {{
                    return this.attributes[name] || null;
                }}
                addEventListener() {{}}
                focus() {{
                    this.focusCalls += 1;
                }}
            }}

            const document = {{
                createElement: (tagName) => new FakeElement(tagName),
                getElementById: (id) => elements.get(id) || null,
                querySelector: (selector) => selector.startsWith('#') ? (elements.get(selector.slice(1)) || null) : null,
                querySelectorAll: () => [],
                addEventListener: () => {{}},
                body: new FakeElement('body', 'document-body'),
            }};

            const localStorage = {{ getItem: () => null, setItem: () => {{}}, removeItem: () => {{}} }};
            const sessionStorage = {{ getItem: () => null, setItem: () => {{}}, removeItem: () => {{}} }};

            class FakeFormData {{
                constructor() {{
                    this.entries = [];
                }}
                append(name, value, filename) {{
                    this.entries.push({{ name, value, filename }});
                }}
            }}

            const context = {{
                console,
                document,
                localStorage,
                sessionStorage,
                navigator: {{ mediaDevices: {{ getUserMedia: async () => ({{ getTracks: () => [{{ stop() {{}} }}] }}) }} }},
                window: {{
                    document,
                    navigator: {{ mediaDevices: {{ getUserMedia: async () => ({{ getTracks: () => [{{ stop() {{}} }}] }}) }} }},
                    crypto: {{ randomUUID: () => 'conv-fixed' }},
                    location: {{ origin: 'http://localhost' }},
                }},
                MediaRecorder: function () {{}},
                Blob: class {{
                    constructor(parts, options = {{}}) {{
                        this.parts = parts;
                        this.type = options.type || 'audio/webm';
                        this.size = parts.reduce((sum, part) => sum + (part.size || part.length || 0), 0);
                    }}
                }},
                FormData: FakeFormData,
                fetch: async () => ({{ ok: true, status: 200, json: async () => ({{ status: 'ok', text: 'show all leads', provider: 'groq', validator: 'cerebras' }}) }}),
                requestAnimationFrame: (fn) => fn(),
                setTimeout: (fn) => {{ fn(); return 1; }},
                clearTimeout: () => {{}},
                DOMParser: class {{ parseFromString() {{ return {{ querySelector: () => null, body: {{ innerHTML: '' }} }}; }} }},
                URL,
                Date,
                Math,
                JSON,
                Promise,
            }};

            context.global = context;
            context.globalThis = context;

            const register = (id, tag = 'div', value = '') => {{
                const element = new FakeElement(tag, id);
                element.value = value;
                elements.set(id, element);
                return element;
            }};

            register('ai-agent-body');
            register('ai-agent-input', 'input');
            register('ai-agent-input-clear', 'button');
            register('ai-agent-mic-btn', 'button');
            register('ai-agent-send-btn', 'button');

            return context;
        }}

        async function main() {{
            const context = createHarness();
            vm.createContext(context);
            vm.runInContext(source, context);
            {test_body}
        }}

        main().catch((error) => {{
            console.error(error && error.stack ? error.stack : error);
            process.exit(1);
        }});
        """
    )
    completed = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_template_exposes_clear_and_mic_buttons():
    markup = TEMPLATE_PATH.read_text()

    assert 'id="ai-agent-input-clear"' in markup
    assert 'id="ai-agent-mic-btn"' in markup
    assert 'onclick="toggleAiAgentVoiceRecording()"' in markup


def test_js_source_wires_stt_fetch_and_composer_state():
    source = JS_PATH.read_text()

    assert "fetch('/ai-agent/api/stt'" in source
    assert "function clearAiAgentInput()" in source
    assert "function toggleAiAgentVoiceRecording()" in source
    assert "function updateAiAgentComposerState()" in source


def test_composer_clear_button_tracks_input_value():
    _run_node_dom_test(
        """
        const input = context.document.getElementById('ai-agent-input');
        const clearBtn = context.document.getElementById('ai-agent-input-clear');

        input.value = 'l';
        context.updateAiAgentComposerState();
        if (!clearBtn.classList.contains('is-visible')) {
            throw new Error('expected clear button to be visible when input has text');
        }

        context.clearAiAgentInput();
        if (input.value !== '') {
            throw new Error('expected clear button to empty the input');
        }
        if (clearBtn.classList.contains('is-visible')) {
            throw new Error('expected clear button to hide after clearing input');
        }
        """
    )


def test_transcribe_audio_blob_applies_transcript_to_input():
    _run_node_dom_test(
        """
        const input = context.document.getElementById('ai-agent-input');
        const micBtn = context.document.getElementById('ai-agent-mic-btn');

        await context.transcribeAiAgentAudioBlob({ size: 12, type: 'audio/webm', name: 'voice.webm' });

        if (input.value !== 'show all leads') {
            throw new Error(`expected transcript to populate input, got ${input.value}`);
        }
        if (micBtn.classList.contains('is-busy')) {
            throw new Error('expected mic button busy state to clear after transcription');
        }
        """
    )
