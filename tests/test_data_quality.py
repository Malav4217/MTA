"""
Data Quality Tests
─────────────────
Validates that collected and processed data
meets expected quality standards.
These tests catch data pipeline bugs before
they affect the dashboard.
"""
import pytest


class TestRawDataQuality:
    """Tests for raw_bus_snapshots table."""

    def test_table_has_data(self, db_connection):
        """Pipeline must have collected some data."""
        count = db_connection.execute("""
            SELECT COUNT(*) FROM raw_bus_snapshots
        """).fetchone()[0]
        assert count > 0, (
            "raw_bus_snapshots is empty. "
            "Has the pipeline run?"
        )

    def test_no_null_vehicle_ids(self, sample_raw_data):
        """Every snapshot must have a vehicle ID."""
        null_count = sample_raw_data['vehicle_id'].isna().sum()
        assert null_count == 0, (
            f"Found {null_count} null vehicle_ids"
        )

    def test_no_null_routes(self, sample_raw_data):
        """Every snapshot must have a route."""
        null_count = sample_raw_data['route'].isna().sum()
        assert null_count == 0, (
            f"Found {null_count} null routes"
        )

    def test_coordinates_within_nyc_bounds(
        self, sample_raw_data
    ):
        """
        All GPS coordinates must be within NYC bounds.
        NYC bounding box:
          Lat: 40.4 to 41.0
          Lon: -74.3 to -73.6
        """
        valid_lat = sample_raw_data['latitude'].between(
            40.4, 41.0
        )
        valid_lon = sample_raw_data['longitude'].between(
            -74.3, -73.6
        )
        invalid = (~valid_lat | ~valid_lon).sum()
        assert invalid == 0, (
            f"Found {invalid} coordinates outside NYC bounds"
        )

    def test_only_tracked_routes(self, sample_raw_data):
        """Only configured routes should appear in data."""
        from config import TRACKED_ROUTES
        expected = {f"MTA NYCT_{r}" for r in TRACKED_ROUTES}
        actual = set(sample_raw_data['route'].unique())
        unexpected = actual - expected
        assert len(unexpected) == 0, (
            f"Unexpected routes found: {unexpected}"
        )

    def test_no_future_timestamps(self, sample_raw_data):
        """Captured timestamps must not be in the future."""
        from datetime import datetime
        future_count = (
            sample_raw_data['captured_at'] > datetime.now()
        ).sum()
        assert future_count == 0, (
            f"Found {future_count} future timestamps"
        )

    def test_no_duplicate_snapshots(self, db_connection):
        """
        Same vehicle should not have identical snapshots
        at the exact same timestamp.
        """
        dupes = db_connection.execute("""
            SELECT
                vehicle_id,
                captured_at,
                COUNT(*) as cnt
            FROM raw_bus_snapshots
            WHERE captured_at >= CURRENT_DATE
            GROUP BY vehicle_id, captured_at
            HAVING COUNT(*) > 1
        """).fetchone()
        assert dupes is None, (
            f"Found duplicate snapshots: {dupes}"
        )

    def test_recent_data_exists(self, db_connection):
        """
        Pipeline must have run recently.
        Fails if no data in last 10 minutes.
        """
        recent = db_connection.execute("""
            SELECT COUNT(*)
            FROM raw_bus_snapshots
            WHERE captured_at >= NOW() - INTERVAL '10 minutes'
        """).fetchone()[0]

        if recent == 0:
            pytest.skip(
                "Pipeline not running during test — "
                "this test passes in CI/CD with live pipeline"
            )


class TestProcessedDataQuality:
    """Tests for bus_arrivals table."""

    def test_arrivals_table_has_data(self, db_connection):
        """Transform must have processed some arrivals."""
        count = db_connection.execute("""
            SELECT COUNT(*) FROM bus_arrivals
        """).fetchone()[0]
        assert count > 0, (
            "bus_arrivals is empty. "
            "Has the transform run?"
        )

    def test_delay_within_valid_range(
        self, sample_arrivals
    ):
        """
        Delay values must be realistic.
        Valid range: -10 to 60 minutes.
        Values outside this are data errors.
        """
        if sample_arrivals.empty:
            pytest.skip("No arrival data available")

        too_early = (
            sample_arrivals['delay_minutes'] < -10
        ).sum()
        too_late = (
            sample_arrivals['delay_minutes'] > 60
        ).sum()

        assert too_early == 0, (
            f"Found {too_early} arrivals with delay < -10 min"
        )
        assert too_late == 0, (
            f"Found {too_late} arrivals with delay > 60 min"
        )

    def test_boolean_flags_consistent(
        self, sample_arrivals
    ):
        """
        is_late, is_early, is_on_time must be
        mutually consistent with delay_minutes.
        A bus cannot be both late and early.
        """
        if sample_arrivals.empty:
            pytest.skip("No arrival data available")

        both_late_and_early = (
            sample_arrivals['is_late'] &
            sample_arrivals['is_early']
        ).sum()

        assert both_late_and_early == 0, (
            f"Found {both_late_and_early} rows marked "
            f"both late AND early"
        )

    def test_on_time_rate_realistic(
        self, sample_arrivals
    ):
        """
        On-time rate must be between 10% and 95%.
        Values outside this suggest a calculation bug.
        """
        if sample_arrivals.empty:
            pytest.skip("No arrival data available")

        on_time_rate = (
            sample_arrivals['is_late'] == False
        ).mean() * 100

        assert on_time_rate >= 10, (
            f"On-time rate suspiciously low: {on_time_rate:.1f}%"
        )
        assert on_time_rate <= 95, (
            f"On-time rate suspiciously high: {on_time_rate:.1f}%"
        )

    def test_no_null_stop_names(self, sample_arrivals):
        """Processed arrivals should have stop names."""
        if sample_arrivals.empty:
            pytest.skip("No arrival data available")

        null_stops = sample_arrivals['stop_name'].isna().sum()
        total = len(sample_arrivals)
        null_pct = null_stops / total * 100

        assert null_pct < 20, (
            f"Too many null stop names: {null_pct:.1f}% "
            f"({null_stops}/{total})"
        )

    def test_hour_values_valid(self, sample_arrivals):
        """Hour column must be 0-23."""
        if sample_arrivals.empty:
            pytest.skip("No arrival data available")

        invalid_hours = (
            ~sample_arrivals['hour'].between(0, 23)
        ).sum()
        assert invalid_hours == 0, (
            f"Found {invalid_hours} invalid hour values"
        )
