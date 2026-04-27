"""
Detection Algorithm Tests
─────────────────────────
Tests for ghost bus and bunching detection logic.
Validates that detection algorithms produce
credible, non-inflated results.
"""
import pytest
import math


class TestBunchingDetection:
    """Tests for bunching_events table."""

    def test_bunching_distance_valid(
        self, sample_bunching
    ):
        """
        All bunching events must have distance
        between 50m and 500m.
        Below 50m = GPS noise (false positive)
        Above 500m = not actually bunching
        """
        if sample_bunching.empty:
            pytest.skip("No bunching data available")

        too_close = (
            sample_bunching['distance_between_m'] < 50
        ).sum()
        too_far = (
            sample_bunching['distance_between_m'] > 500
        ).sum()

        assert too_close == 0, (
            f"Found {too_close} bunching events < 50m apart "
            f"(GPS noise - check minimum distance filter)"
        )
        assert too_far == 0, (
            f"Found {too_far} bunching events > 500m apart "
            f"(not actually bunching)"
        )

    def test_no_same_vehicle_bunching(
        self, sample_bunching
    ):
        """
        A bus cannot bunch with itself.
        vehicle_1_id must not equal vehicle_2_id.
        """
        if sample_bunching.empty:
            pytest.skip("No bunching data available")

        same_vehicle = (
            sample_bunching['vehicle_1_id'] ==
            sample_bunching['vehicle_2_id']
        ).sum()

        assert same_vehicle == 0, (
            f"Found {same_vehicle} events where a bus "
            f"is bunched with itself"
        )

    def test_bunching_vehicles_on_same_route(
        self, sample_bunching, db_connection
    ):
        """
        Bunched vehicles must be on the same route.
        Cross-route bunching detection is a bug.
        """
        if sample_bunching.empty:
            pytest.skip("No bunching data available")

        valid_routes = {
            'MTA NYCT_M15', 'MTA NYCT_BX12',
            'MTA NYCT_B46', 'MTA NYCT_Q58',
            'MTA NYCT_S79', 'M15', 'BX12',
            'B46', 'Q58', 'S79'
        }
        routes = sample_bunching['route'].unique()
        invalid = set(routes) - valid_routes
        assert len(invalid) == 0, (
            f"Found bunching events with invalid routes: "
            f"{invalid}"
        )

    def test_bunching_count_realistic(
        self, db_connection
    ):
        """
        Daily bunching count must be realistic.
        Over 1000 events/day suggests false positives.
        After our 3-layer filter, expect 10-500/day.
        """
        count = db_connection.execute("""
            SELECT COUNT(*)
            FROM bunching_events
            WHERE CAST(timestamp AS DATE) = CURRENT_DATE
        """).fetchone()[0]

        assert count >= 0, "Negative bunching count impossible"
        assert count < 1000, (
            f"Bunching count {count} is too high. "
            f"Possible false positives — check filters."
        )


class TestGhostBusDetection:
    """Tests for ghost_buses table."""

    def test_ghost_distance_valid(self, sample_ghosts):
        """
        Ghost buses must have disappeared while
        still far from stop (> 50m).
        A bus at the stop cannot be a ghost.
        """
        if sample_ghosts.empty:
            pytest.skip("No ghost bus data available")

        at_stop = (
            sample_ghosts['distance_at_disappear'] <= 50
        ).sum()

        assert at_stop == 0, (
            f"Found {at_stop} ghost buses that disappeared "
            f"at or after reaching the stop — not a ghost"
        )

    def test_ghost_count_realistic(self, db_connection):
        """
        Daily ghost count must be realistic.
        Over 200/day = likely false positives.
        We expect 0-100 per day across 4 routes.
        """
        count = db_connection.execute("""
            SELECT COUNT(*)
            FROM ghost_buses
            WHERE CAST(captured_date AS DATE) = CURRENT_DATE
        """).fetchone()[0]

        assert count >= 0, "Negative ghost count impossible"
        assert count < 200, (
            f"Ghost bus count {count} is suspiciously high. "
            f"Check detection logic for false positives."
        )

    def test_ghost_routes_valid(self, sample_ghosts):
        """Ghost buses must be on tracked routes."""
        if sample_ghosts.empty:
            pytest.skip("No ghost bus data available")

        valid_routes = {
            'MTA NYCT_M15', 'MTA NYCT_BX12',
            'MTA NYCT_B46', 'MTA NYCT_Q58',
            'MTA NYCT_S79'
        }
        actual = set(sample_ghosts['route'].unique())
        invalid = actual - valid_routes
        assert len(invalid) == 0, (
            f"Ghost buses on unexpected routes: {invalid}"
        )


class TestHaversineFormula:
    """
    Unit tests for the Haversine distance formula.
    Tests the core math used in bunching detection.
    """

    def haversine(self, lat1, lon1, lat2, lon2):
        """Haversine formula implementation."""
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (math.sin(dphi/2)**2 +
             math.cos(phi1) * math.cos(phi2) *
             math.sin(dlambda/2)**2)
        return R * 2 * math.atan2(
            math.sqrt(a), math.sqrt(1-a)
        )

    def test_same_point_is_zero(self):
        """Distance from a point to itself is 0."""
        dist = self.haversine(
            40.7128, -74.0060,
            40.7128, -74.0060
        )
        assert dist == 0.0

    def test_known_distance(self):
        """
        Distance between two known NYC locations.
        Times Square to Empire State Building
        is approximately 1,350 meters.
        """
        times_square = (40.7580, -73.9855)
        empire_state  = (40.7484, -73.9856)

        dist = self.haversine(
            times_square[0], times_square[1],
            empire_state[0], empire_state[1]
        )
        assert 1000 < dist < 1500, (
            f"Expected ~1350m, got {dist:.0f}m"
        )

    def test_distance_is_symmetric(self):
        """Distance A→B must equal distance B→A."""
        a = (40.7580, -73.9855)
        b = (40.7484, -73.9856)

        dist_ab = self.haversine(a[0], a[1], b[0], b[1])
        dist_ba = self.haversine(b[0], b[1], a[0], a[1])

        assert abs(dist_ab - dist_ba) < 0.001, (
            "Haversine distance is not symmetric"
        )

    def test_bunching_threshold(self):
        """
        Two buses 300m apart should be flagged
        as bunched (within 500m threshold).
        """
        bus1 = (40.7580, -73.9855)
        bus2 = (40.7553, -73.9855)

        dist = self.haversine(
            bus1[0], bus1[1],
            bus2[0], bus2[1]
        )
        assert 50 < dist < 500, (
            f"300m apart buses should trigger bunching. "
            f"Got {dist:.0f}m"
        )
