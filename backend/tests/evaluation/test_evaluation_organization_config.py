import pytest

from app.core.config import (
    get_evaluation_organization_id,
    settings,
)


def test_evaluation_organization_id_is_required(monkeypatch):
    monkeypatch.setattr(settings, "evaluation_organization_id", None)

    with pytest.raises(RuntimeError, match="EVALUATION_ORGANIZATION_ID"):
        get_evaluation_organization_id()


@pytest.mark.parametrize("organization_id", [0, -1, True, "7"])
def test_evaluation_organization_id_must_be_a_positive_integer(
    monkeypatch,
    organization_id,
):
    monkeypatch.setattr(settings, "evaluation_organization_id", organization_id)

    with pytest.raises(RuntimeError, match="EVALUATION_ORGANIZATION_ID"):
        get_evaluation_organization_id()


def test_evaluation_organization_id_uses_configured_value(monkeypatch):
    monkeypatch.setattr(settings, "evaluation_organization_id", 7)

    assert get_evaluation_organization_id() == 7
