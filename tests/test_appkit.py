"""appkit 基础设施测试（ConfigManager / secrets / paths / providers）。"""

import os

import pytest

from appkit.config import ConfigManager
from appkit.paths import (
    get_config_path,
    get_logs_dir,
    get_memory_db_path,
    get_resource_dir,
    get_secrets_path,
    get_user_data_dir,
)
from appkit.providers import AIProvider, AIProviderConfig
from appkit.secrets import SecretStore


# ---------------------------------------------------------
# paths
# ---------------------------------------------------------


def test_user_data_dir_is_under_appdata(monkeypatch):
    import tempfile

    fake = tempfile.mkdtemp(prefix="xiaoqi-appdata-")
    monkeypatch.setenv("APPDATA", fake)

    path = get_user_data_dir()

    assert str(path).startswith(fake)
    assert path.exists()


def test_paths_are_inside_user_data(monkeypatch):
    import tempfile

    fake = tempfile.mkdtemp(prefix="xiaoqi-appdata-")
    monkeypatch.setenv("APPDATA", fake)

    assert str(get_memory_db_path()).startswith(fake)
    assert str(get_secrets_path()).startswith(fake)
    assert str(get_config_path()).startswith(fake)
    assert str(get_logs_dir()).startswith(fake)


def test_resource_dir_points_to_web():
    # 开发模式：web/ 存在于项目内
    web = get_resource_dir() / "index.html"
    assert web.exists() or web.parent.name == "web"


# ---------------------------------------------------------
# ConfigManager
# ---------------------------------------------------------


def test_config_defaults_and_save(tmp_path):
    cfg = ConfigManager(tmp_path / "config.json")

    assert cfg.get("ai", "provider") == "deepseek"
    assert cfg.get("tts", "provider") == "alibaba"
    assert cfg.setup_complete is False

    cfg.set("ui", "night_mode", True)
    cfg.mark_setup_complete()

    cfg2 = ConfigManager(tmp_path / "config.json")
    assert cfg2.get("ui", "night_mode") is True
    assert cfg2.setup_complete is True


def test_config_never_contains_api_key(tmp_path):
    cfg = ConfigManager(tmp_path / "config.json")
    raw = cfg.all()
    text = str(raw).lower()
    assert "sk-" not in text
    assert "api_key" not in text


# ---------------------------------------------------------
# SecretStore
# ---------------------------------------------------------


def test_secret_set_get_delete(tmp_path):
    store = SecretStore(tmp_path / "secrets.json")

    store.set("deepseek", "sk-test-123")
    assert store.has("deepseek") is True
    assert store.get("deepseek") == "sk-test-123"

    store2 = SecretStore(tmp_path / "secrets.json")
    assert store2.get("deepseek") == "sk-test-123"

    store2.delete("deepseek")
    assert store2.has("deepseek") is False


def test_secret_obfuscated_on_disk(tmp_path):
    store = SecretStore(tmp_path / "secrets.json")
    store.set("deepseek", "sk-secret-value")

    disk = tmp_path / "secrets.json"
    raw = disk.read_text(encoding="utf-8")

    # 磁盘上是混淆值，不是明文（防误读/日志扫描）
    assert "sk-secret-value" not in raw


def test_secret_env_overrides(tmp_path):
    store = SecretStore(tmp_path / "secrets.json")
    store.set("deepseek", "sk-deepseek")
    store.set("alibaba", "sk-alibaba")

    overrides = store.env_overrides()

    assert overrides["XIAOQI_LLM_API_KEY"] == "sk-deepseek"
    assert overrides["XIAOQI_ALIBABA_API_KEY"] == "sk-alibaba"


def test_secret_not_in_configured_providers_after_delete(tmp_path):
    store = SecretStore(tmp_path / "secrets.json")
    store.set("deepseek", "sk-x")
    store.set("openai", "sk-y")

    assert set(store.configured_providers()) == {"deepseek", "openai"}

    store.delete("openai")
    assert store.configured_providers() == ["deepseek"]


# ---------------------------------------------------------
# AIProvider
# ---------------------------------------------------------


def test_ai_provider_requires_key():
    p = AIProvider(AIProviderConfig(api_key=""))
    assert p.available is False

    with pytest.raises(RuntimeError):
        p.chat([{"role": "user", "content": "hi"}])


def test_ai_provider_status():
    p = AIProvider(AIProviderConfig(api_key="sk-x", model="m"))
    st = p.status()
    assert st["available"] is True
    assert st["has_api_key"] is True
    assert st["model"] == "m"


def test_ai_provider_chat_success(monkeypatch):
    sent = {}

    def fake_urlopen(request, timeout=None):
        import json as j

        sent["url"] = request.full_url
        sent["body"] = j.loads(request.data.decode("utf-8"))
        sent["auth"] = request.headers.get("Authorization")

        class _Resp:
            def read(self):
                return j.dumps(
                    {"choices": [{"message": {"content": "你好"}}]}
                ).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return _Resp()

    monkeypatch.setattr(
        "appkit.providers.urllib.request.urlopen",
        fake_urlopen,
    )

    p = AIProvider(
        AIProviderConfig(
            api_key="sk-x",
            base_url="https://api.example.com",
            model="test-model",
        )
    )

    reply = p.chat([{"role": "user", "content": "hi"}])

    assert reply == "你好"
    assert "/chat/completions" in sent["url"]
    assert sent["body"]["model"] == "test-model"
    assert sent["auth"] == "Bearer sk-x"


def test_ai_provider_http_error(monkeypatch):
    import urllib.error

    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 401, "x", None, None)

    monkeypatch.setattr(
        "appkit.providers.urllib.request.urlopen",
        fake_urlopen,
    )

    p = AIProvider(AIProviderConfig(api_key="sk-x"))

    with pytest.raises(RuntimeError) as exc:
        p.chat([{"role": "user", "content": "hi"}])
    assert "401" in str(exc.value)


def test_ai_test_connection_no_key():
    p = AIProvider(AIProviderConfig(api_key=""))
    result = p.test_connection()
    assert result["ok"] is False
