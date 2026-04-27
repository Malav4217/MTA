"""
Pipeline Integration Tests
──────────────────────────
Tests that validate the overall pipeline
is working correctly end to end.
"""
import pytest
import os
import sys

sys.path.append(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))


class TestDatabaseSchema:
    """Tests that all required tables exist."""

    def test_raw_snapshots_table_exists(
        self, db_connection
    ):
        """raw_bus_snapshots table must exist."""
        result = db_connection.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'raw_bus_snapshots'
        """).fetchone()[0]
        assert result == 1, (
            "raw_bus_snapshots table does not exist"
        )

    def test_bus_arrivals_table_exists(
        self, db_connection
    ):
        """bus_arrivals table must exist."""
        result = db_connection.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'bus_arrivals'
        """).fetchone()[0]
        assert result == 1, (
            "bus_arrivals table does not exist"
        )

    def test_ghost_buses_table_exists(
        self, db_connection
    ):
        """ghost_buses table must exist."""
        result = db_connection.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'ghost_buses'
        """).fetchone()[0]
        assert result == 1, (
            "ghost_buses table does not exist"
        )

    def test_bunching_events_table_exists(
        self, db_connection
    ):
        """bunching_events table must exist."""
        result = db_connection.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'bunching_events'
        """).fetchone()[0]
        assert result == 1, (
            "bunching_events table does not exist"
        )

    def test_all_required_columns_in_raw(
        self, db_connection
    ):
        """raw_bus_snapshots must have all required columns."""
        cols = db_connection.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'raw_bus_snapshots'
        """).df()['column_name'].tolist()

        required = [
            'vehicle_id', 'route', 'direction',
            'latitude', 'longitude', 'captured_at',
            'aimed_arrival', 'expected_arrival',
            'next_stop_name', 'distance_to_stop'
        ]
        for col in required:
            assert col in cols, (
                f"Missing required column: {col}"
            )


class TestReadReplica:
    """Tests for the read replica pattern."""

    def test_reader_db_exists(self):
        """
        Read replica database file must exist
        after pipeline has run at least once.
        """
        from config import DB_FILE
        reader_db = DB_FILE.replace('.db', '_reader.db')

        if not os.path.exists(reader_db):
            pytest.skip(
                "Reader DB not found — "
                "run pipeline once first"
            )

        assert os.path.exists(reader_db), (
            f"Reader DB not found: {reader_db}"
        )

    def test_reader_db_not_empty(self):
        """Read replica must have data."""
        from config import DB_FILE
        reader_db = DB_FILE.replace('.db', '_reader.db')

        if not os.path.exists(reader_db):
            pytest.skip("Reader DB not found")

        size = os.path.getsize(reader_db)
        assert size > 1024, (
            f"Reader DB is too small ({size} bytes) — "
            f"may be empty or corrupted"
        )

    def test_replica_is_readable(self):
        """Dashboard must be able to read from replica."""
        import duckdb
        from config import DB_FILE
        reader_db = DB_FILE.replace('.db', '_reader.db')

        if not os.path.exists(reader_db):
            pytest.skip("Reader DB not found")

        con = None
        try:
            con = duckdb.connect(
                reader_db, read_only=True
            )
            count = con.execute("""
                SELECT COUNT(*) FROM raw_bus_snapshots
            """).fetchone()[0]
            assert count > 0
        finally:
            if con:
                con.close()


class TestConfiguration:
    """Tests for project configuration."""

    def test_api_key_configured(self):
        """MTA API key must be set."""
        from config import MTA_API_KEY
        assert MTA_API_KEY is not None, (
            "MTA_API_KEY not set in .env file"
        )
        assert len(MTA_API_KEY) > 10, (
            "MTA_API_KEY looks too short — check .env"
        )

    def test_tracked_routes_configured(self):
        """At least one route must be configured."""
        from config import TRACKED_ROUTES
        assert len(TRACKED_ROUTES) > 0, (
            "No routes configured in TRACKED_ROUTES"
        )

    def test_db_file_configured(self):
        """Database file path must be configured."""
        from config import DB_FILE
        assert DB_FILE is not None
        assert DB_FILE.endswith('.db'), (
            f"DB_FILE should end with .db: {DB_FILE}"
        )
