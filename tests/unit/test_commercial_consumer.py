
import consumers.commercial.commercial_consumer as commercial


def test_com001_uses_configured_warning_threshold(monkeypatch):
    monkeypatch.setattr(
        commercial,
        "get_config",
        lambda: {
            "commercial": {
                "COM-001": {
                    "warning": 0.01,
                    "critical": 1.00,
                },
                "COM-003": {
                    "warning": 0.01,
                    "critical": 1.00,
                },
            }
        },
    )

    assert commercial.commercial_severity("COM-001", 0.10) == "warning"


def test_com001_becomes_critical_at_configured_threshold(monkeypatch):
    monkeypatch.setattr(
        commercial,
        "get_config",
        lambda: {
            "commercial": {
                "COM-001": {
                    "warning": 0.01,
                    "critical": 1.00,
                },
                "COM-003": {
                    "warning": 0.01,
                    "critical": 1.00,
                },
            }
        },
    )

    assert commercial.commercial_severity("COM-001", 1.00) == "critical"


def test_com003_uses_configured_threshold(monkeypatch):
    monkeypatch.setattr(
        commercial,
        "get_config",
        lambda: {
            "commercial": {
                "COM-001": {
                    "warning": 0.01,
                    "critical": 1.00,
                },
                "COM-003": {
                    "warning": 0.01,
                    "critical": 1.00,
                },
            }
        },
    )

    assert commercial.commercial_severity("COM-003", 0.10) == "warning"


def test_com003_below_warning_is_none(monkeypatch):
    monkeypatch.setattr(
        commercial,
        "get_config",
        lambda: {
            "commercial": {
                "COM-001": {
                    "warning": 0.01,
                    "critical": 1.00,
                },
                "COM-003": {
                    "warning": 0.01,
                    "critical": 1.00,
                },
            }
        },
    )

    assert commercial.commercial_severity("COM-003", 0.005) == "none"
