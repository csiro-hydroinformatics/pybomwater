"""Opt-in progressive load test for the live BoM SOS observation endpoint."""

from datetime import datetime, timedelta, timezone
import time

import pytest
import requests

import pybomwater.bom_water as bm


pytestmark = pytest.mark.load_bom


# These gauges are already exercised as daily-discharge gauges by test_core.
GAUGES = [
    "http://bom.gov.au/waterdata/services/stations/410061",
    "http://bom.gov.au/waterdata/services/stations/410733",
    "http://bom.gov.au/waterdata/services/stations/410071",
    "http://bom.gov.au/waterdata/services/stations/410700",
    "http://bom.gov.au/waterdata/services/stations/410747",
    "http://bom.gov.au/waterdata/services/stations/410752",
    "http://bom.gov.au/waterdata/services/stations/410070",
    "http://bom.gov.au/waterdata/services/stations/410750",
    "http://bom.gov.au/waterdata/services/stations/410719",
    "http://bom.gov.au/waterdata/services/stations/410038",
]

# Each stage is a strict superset of the preceding request along both load axes:
# more gauges and a longer period for every gauge.
LOAD_STAGES = [
    (1, timedelta(days=7)),
    (2, timedelta(days=30)),
    (4, timedelta(days=180)),
    (8, timedelta(days=5 * 365)),
    (10, timedelta(days=20 * 365)),
]

END = datetime(2025, 1, 1, tzinfo=timezone(timedelta(hours=10)))
RATE_LIMIT_HEADERS = {
    "retry-after",
    "ratelimit-limit",
    "ratelimit-remaining",
    "ratelimit-reset",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
}


def _rate_limit_headers(response):
    return {
        name: value
        for name, value in response.headers.items()
        if name.lower() in RATE_LIMIT_HEADERS
    }


def _format_headers(headers):
    if not headers:
        return "none"
    return ", ".join(f"{name}={value}" for name, value in sorted(headers.items()))


@pytest.fixture
def load_client():
    client = bm.BomWater(
        request_interval=0,
        request_timeout=180,
        max_retries=0,
    )
    yield client
    client.session.close()


def test_progressive_observation_load(load_client):
    """Increase gauge count and history until the documented test ceiling."""
    client = load_client
    property_id = client.properties.Water_Course_Discharge
    procedure_id = client.procedures.Pat4_C_B_1_DailyMean
    previous_value_count = 0

    print(
        "\nstage gauges history_days status seconds response_bytes "
        "observations rate_limit_headers"
    )

    for stage_number, (gauge_count, history) in enumerate(LOAD_STAGES, start=1):
        gauges = GAUGES[:gauge_count]
        begin = END - history
        started = time.perf_counter()

        try:
            response = client.request(
                client.actions.GetObservation,
                gauges,
                property_id,
                procedure_id,
                begin.isoformat(timespec="seconds"),
                END.isoformat(timespec="seconds"),
            )
        except requests.HTTPError as error:
            response = error.response
            if response is not None and response.status_code == 429:
                pytest.fail(
                    "BoM rate limited the progressive load test at "
                    f"stage {stage_number} ({gauge_count} gauges, "
                    f"{history.days} days per gauge); headers: "
                    f"{_format_headers(_rate_limit_headers(response))}"
                )
            raise

        duration = time.perf_counter() - started
        value_count = client.values_count(response)
        headers = _rate_limit_headers(response)
        print(
            f"{stage_number:>5} {gauge_count:>6} {history.days:>12} "
            f"{response.status_code:>6} {duration:>7.2f} "
            f"{len(response.content):>14} {value_count:>12} "
            f"{_format_headers(headers)}"
        )

        assert value_count > 0, (
            f"stage {stage_number} returned no observations for "
            f"{gauge_count} gauges over {history.days} days"
        )
        assert value_count >= previous_value_count, (
            f"stage {stage_number} returned fewer observations than the "
            "smaller preceding stage"
        )
        previous_value_count = value_count

    print(
        f"No HTTP 429 through {len(GAUGES)} gauges and "
        f"{LOAD_STAGES[-1][1].days} days per gauge."
    )
