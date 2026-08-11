from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_runtime_dashboard_renders_all_six_contract_panels() -> None:
    dashboard = AppTest.from_file(str(REPO_ROOT / "dashboard.py"))
    dashboard.run(timeout=20)

    assert not dashboard.exception

    titles = {heading.value for heading in dashboard.subheader}
    assert titles == {
        "1. Latency percentiles",
        "2. Request traffic",
        "3. Error rate and breakdown",
        "4. Cost over time",
        "5. Input and output tokens",
        "6. Quality proxy",
    }
