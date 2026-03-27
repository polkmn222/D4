from pathlib import Path


def test_new_template_modal_router_still_supports_template_form_surface():
    source = Path("development/web/backend/app/api/form_router.py").read_text(encoding="utf-8")

    assert '@router.get("/message_templates/new-modal")' in source
    assert '@router.get("/message_templates/new")' in source
    assert '"templates/sf_form_modal.html"' in source
    assert '"object_type": "MessageTemplate"' in source


def test_shared_modal_template_uses_exact_create_route_pattern():
    source = Path("development/web/frontend/templates/templates/sf_form_modal.html").read_text(encoding="utf-8")

    assert 'action="/{{ p_type }}{% if initial_values and initial_values.id %}/{{ initial_values.id }}{% else %}/{% endif %}"' in source
    assert 'enctype="multipart/form-data"' in source
    assert 'name="image"' in source
    assert 'accept="image/jpeg,image/jpg"' in source


def test_lead_modal_embedded_mode_contract_keeps_lookup_inputs_and_removes_modal_close():
    router_source = Path("development/web/backend/app/api/form_router.py").read_text(encoding="utf-8")
    template_source = Path("development/web/frontend/templates/templates/sf_form_modal.html").read_text(encoding="utf-8")
    embedded_page_source = Path("development/web/frontend/templates/leads/embedded_form_page.html").read_text(encoding="utf-8")

    assert "embedded: int = 0" in router_source
    assert '"embedded": bool(embedded)' in router_source
    assert "fields = [\"first_name\", \"last_name\", \"email\", \"phone\", \"status\", \"gender\", \"brand\", \"model\", \"product\", \"description\"]" in router_source
    assert '@router.get("/leads/embedded-form")' in router_source
    assert '"leads/embedded_form_page.html"' in router_source
    assert "{% if not embedded %}" in template_source
    assert "onclick=\"closeModal()\"" in template_source
    assert "cancelOpsPilotEmbeddedForm" in template_source
    assert "Save & New" in template_source
    assert "{% if embedded %}max-height: none; overflow: visible;{% else %}max-height: 80vh; overflow-y: auto;{% endif %}" in template_source
    assert "lookup-container-{{ field }}" in template_source
    assert "initLookup('lookup-container-{{ field }}'" in template_source
    assert '<script src="/static/js/lookup.js"></script>' in embedded_page_source
    assert '{% include "templates/sf_form_modal.html" %}' in embedded_page_source
