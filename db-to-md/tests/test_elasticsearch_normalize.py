from __future__ import annotations

from md_generator.db.core.elasticsearch_normalize import (
    filter_snapshot_repositories_by_type,
    normalize_search_template,
    normalize_snapshot_repository,
    security_placeholder_sections,
)


def test_normalize_snapshot_repository_operational_and_slm_notes() -> None:
    repo = normalize_snapshot_repository(
        "backup",
        {
            "type": "s3",
            "settings": {
                "bucket": "es-snaps",
                "readonly": True,
                "compress": True,
                "custom_plugin_flag": "on",
            },
        },
        slm_policies={
            "daily": {"policy": {"repository": "backup", "schedule": "0 0 * * *"}},
        },
    )
    assert repo.repository_type == "s3"
    assert repo.operational["bucket"] == "es-snaps"
    assert repo.operational["readonly"] is True
    assert repo.settings["custom_plugin_flag"] == "on"
    assert repo.notes is not None
    assert "daily" in repo.notes


def test_filter_snapshot_repositories_by_type() -> None:
    body = {
        "fs-repo": {"type": "fs", "settings": {"location": "/tmp"}},
        "s3-repo": {"type": "s3", "settings": {"bucket": "b"}},
    }
    filtered = filter_snapshot_repositories_by_type(body, {"snapshot_repository_types": "s3"})
    assert list(filtered) == ["s3-repo"]


def test_normalize_search_template_source_variants_and_truncation() -> None:
    tpl = normalize_search_template(
        "nested-source",
        {"lang": "mustache", "script": {"source": {"query": {"match_all": {}}}}},
        {"max_template_source_chars": 20},
    )
    assert tpl is not None
    assert tpl.lang == "mustache"
    assert tpl.source_truncated is True
    assert tpl.source_preview is not None
    assert "truncated" in tpl.source_preview


def test_normalize_slm_policy() -> None:
    from md_generator.db.core.elasticsearch_normalize import normalize_slm_policy

    pol = normalize_slm_policy(
        "daily",
        {
            "policy": {
                "schedule": "0 0 * * *",
                "repository": "backup",
                "config": {"indices": ["logs-*"]},
            }
        },
    )
    assert pol.name == "daily"
    assert pol.repository == "backup"
    assert pol.schedule == "0 0 * * *"
    assert pol.indices_pattern == "logs-*"


def test_normalize_search_template_lang_filter() -> None:
    tpl = normalize_search_template(
        "p1",
        {"lang": "painless", "source": "return 1"},
        {"search_templates_langs": "mustache"},
    )
    assert tpl is None


def test_normalize_search_template_param_keys() -> None:
    tpl = normalize_search_template(
        "q",
        {
            "lang": "mustache",
            "source": '{"query": {}}',
            "params": {"from": 0, "size": 10},
        },
        {},
    )
    assert tpl is not None
    assert tpl.param_keys == ("from", "size")


def test_security_placeholder_sections_stable() -> None:
    sections = security_placeholder_sections()
    assert len(sections) == 3
    assert sections[0][0] == "elasticsearch_security_roles"
