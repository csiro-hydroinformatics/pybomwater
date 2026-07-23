import os

import pytest


LIVE_BOM_TESTS = {
    'test_bom_service',
    'test_get_capabilities',
    'test_get_feature_of_interest',
    'test_get_data_availability',
    'test_get_observation',
    'test_get_observation_check_daily',
    'test_create_feature_geojson_list',
    'test_get_features_of_interest',
    'test_check_what_available',
    'test_duplicate_dates',
    'test_single_feature_obs',
    'test_filtered_get_observations',
}


def pytest_collection_modifyitems(config, items):
    run_live = os.environ.get('PYBOMWATER_RUN_LIVE') == '1'
    skip_live = pytest.mark.skip(
        reason='live BoM integration test; set PYBOMWATER_RUN_LIVE=1 to run'
    )
    for item in items:
        if item.name in LIVE_BOM_TESTS:
            item.add_marker(pytest.mark.live_bom)
            if not run_live:
                item.add_marker(skip_live)
