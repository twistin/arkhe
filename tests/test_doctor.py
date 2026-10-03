import httpx
import pytest

from docente_ai.doctor import check_ollama, diagnose, local_url, positive_timeout


@pytest.mark.parametrize("url", [
    "https://example.org", "http://example.org", "http://192.168.1.10:11434",
    "http://127.0.0.1.evil.test", "http://user:secret@127.0.0.1",
    "http://127.0.0.1/api", "http://127.0.0.1?url=external",
    "http://127.0.0.1#x", "http://127.0.0.1:99999", "http://127.0.0.1:0",
    "http://[::1%en0]", "http://[::ffff:192.168.1.1]", "http://[broken",
    "file:///tmp/test", "127.0.0.1:11434",
])
def test_external_or_ambiguous_host_rejected(url):
    with pytest.raises(ValueError):
        local_url(url)


@pytest.mark.parametrize(("url", "expected"), [
    ("http://localhost:11434/", "http://127.0.0.1:11434"),
    ("http://127.0.0.1:11434", "http://127.0.0.1:11434"),
    ("http://[::1]:11434", "http://[::1]:11434"),
])
def test_loopback_normalization(url, expected):
    assert local_url(url) == expected


@pytest.mark.parametrize("value", ["nan", "inf", "-1", "0", "31", "invalid"])
def test_invalid_timeout(value):
    with pytest.raises(ValueError):
        positive_timeout(value)


def test_metadata_only_and_proxy_environment_ignored(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://external.invalid:8888")
    monkeypatch.setenv("ALL_PROXY", "http://external.invalid:8888")
    paths = []

    def respond(request):
        assert request.url.host == "127.0.0.1"
        assert request.method == "GET"
        assert request.content == b""
        paths.append(request.url.path)
        payload = {"version": "test-version"} if request.url.path == "/api/version" else {
            "models": [{"name": "example-model"}]
        }
        return httpx.Response(200, json=payload)

    checks = check_ollama("http://localhost:11434", 1, transport=httpx.MockTransport(respond))
    assert paths == ["/api/version", "/api/tags"]
    assert [check.status for check in checks] == ["ok", "ok", "warning"]
    assert "example-model" in checks[1].detail


def test_redirect_never_followed():
    paths = []

    def respond(request):
        paths.append(str(request.url))
        return httpx.Response(302, headers={"Location": "https://external.invalid/"})

    checks = check_ollama("http://127.0.0.1:11434", 1, transport=httpx.MockTransport(respond))
    assert len(paths) == 2
    assert all(url.startswith("http://127.0.0.1:11434/") for url in paths)
    assert all(check.status == "error" for check in checks[:2])


@pytest.mark.parametrize("error", [httpx.ConnectError, httpx.ReadTimeout])
def test_transport_failure_is_reported(error):
    def respond(request):
        raise error("simulated", request=request)

    checks = check_ollama("http://127.0.0.1", 1, transport=httpx.MockTransport(respond))
    assert [check.status for check in checks[:2]] == ["error", "error"]


@pytest.mark.parametrize("payload", [None, [], {}, {"version": 12, "models": "oops"},
    {"version": "", "models": [{}]}, {"models": [None]}, {"models": [{"name": ""}]}])
def test_bad_schema_is_reported(payload):
    checks = check_ollama("http://127.0.0.1", 1, transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=payload)
    ))
    assert all(check.status == "error" for check in checks[:2])


def test_invalid_json_is_reported():
    checks = check_ollama("http://127.0.0.1", 1, transport=httpx.MockTransport(
        lambda request: httpx.Response(200, text="not JSON")
    ))
    assert all(check.status == "error" for check in checks[:2])


def test_empty_model_list_is_warning():
    checks = check_ollama("http://127.0.0.1", 1, transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={"version": "test", "models": []})
    ))
    assert checks[0].status == "ok"
    assert checks[1].status == "warning"


def test_offline_never_calls_transport_and_creates_no_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def forbidden(request):
        pytest.fail("El modo offline no debe consultar Ollama")

    checks = diagnose(offline=True, transport=httpx.MockTransport(forbidden))
    assert checks[-1].status == "skipped"
    assert any(check.name == "sqlite" and check.status == "ok" for check in checks)
    assert not list(tmp_path.iterdir())
