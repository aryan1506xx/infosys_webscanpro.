from scanners import active
import pytest

def test_safe_build_form_action():
    base = "http://example.com/path/"
    assert active.safe_build_form_action(base, "") == base
    assert active.safe_build_form_action(base, "/a") == "http://example.com/a"
    assert active.safe_build_form_action(base, "page") == "http://example.com/path/page"

def test_fill_form_defaults_and_payload():
    form = {"inputs":[{"name":"username","type":"text"},{"name":"pwd","type":"password"}]}
    data = active.fill_form_defaults(form)
    assert data["username"] == "test"
    assert data["pwd"] == "test"
    data2 = active.fill_form_defaults(form, payload_for_field={"username":"<scX>p</scX>"})
    assert data2["username"] == "<scX>p</scX>"
