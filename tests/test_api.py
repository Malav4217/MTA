"""
MTA API Tests
─────────────
Tests that validate the MTA Bus Time API
is accessible and returning expected data.
"""
import pytest
import requests
import sys
import os

sys.path.append(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))


class TestMTAAPI:
    """Tests for MTA Bus Time API connectivity."""

    def test_api_returns_200(self):
        """API must return HTTP 200 status."""
        from config import MTA_API_KEY, VEHICLE_MONITORING_URL

        response = requests.get(
            VEHICLE_MONITORING_URL,
            params={
                'key': MTA_API_KEY,
                'LineRef': 'MTA NYCT_M15',
                'VehicleMonitoringDetailLevel': 'calls'
            },
            timeout=10
        )
        assert response.status_code == 200, (
            f"API returned {response.status_code}"
        )

    def test_api_returns_valid_json(self):
        """API response must be valid JSON."""
        from config import MTA_API_KEY, VEHICLE_MONITORING_URL

        response = requests.get(
            VEHICLE_MONITORING_URL,
            params={
                'key': MTA_API_KEY,
                'LineRef': 'MTA NYCT_M15',
                'VehicleMonitoringDetailLevel': 'calls'
            },
            timeout=10
        )
        data = response.json()
        assert 'Siri' in data, (
            "API response missing 'Siri' key"
        )

    def test_api_returns_vehicle_data(self):
        """API must return vehicle activity data."""
        from config import MTA_API_KEY, VEHICLE_MONITORING_URL

        response = requests.get(
            VEHICLE_MONITORING_URL,
            params={
                'key': MTA_API_KEY,
                'LineRef': 'MTA NYCT_M15',
                'VehicleMonitoringDetailLevel': 'calls'
            },
            timeout=10
        )
        data = response.json()
        vehicles = (
            data['Siri']['ServiceDelivery']
            ['VehicleMonitoringDelivery'][0]
            .get('VehicleActivity', [])
        )
        assert len(vehicles) > 0, (
            "No vehicles returned for M15 — "
            "check API key or route name"
        )

    def test_api_vehicle_has_required_fields(self):
        """Each vehicle must have GPS and route data."""
        from config import MTA_API_KEY, VEHICLE_MONITORING_URL

        response = requests.get(
            VEHICLE_MONITORING_URL,
            params={
                'key': MTA_API_KEY,
                'LineRef': 'MTA NYCT_M15',
                'VehicleMonitoringDetailLevel': 'calls'
            },
            timeout=10
        )
        data = response.json()
        vehicles = (
            data['Siri']['ServiceDelivery']
            ['VehicleMonitoringDelivery'][0]
            .get('VehicleActivity', [])
        )

        if not vehicles:
            pytest.skip("No vehicles returned from API")

        vehicle = vehicles[0]['MonitoredVehicleJourney']

        assert 'VehicleRef' in vehicle, (
            "Missing VehicleRef in API response"
        )
        assert 'VehicleLocation' in vehicle, (
            "Missing VehicleLocation in API response"
        )
        assert 'LineRef' in vehicle, (
            "Missing LineRef in API response"
        )
        assert 'MonitoredCall' in vehicle, (
            "Missing MonitoredCall — add "
            "VehicleMonitoringDetailLevel=calls to request"
        )

    def test_monitored_call_has_arrival_time(self):
        """MonitoredCall must include arrival time."""
        from config import MTA_API_KEY, VEHICLE_MONITORING_URL

        response = requests.get(
            VEHICLE_MONITORING_URL,
            params={
                'key': MTA_API_KEY,
                'LineRef': 'MTA NYCT_M15',
                'VehicleMonitoringDetailLevel': 'calls'
            },
            timeout=10
        )
        data = response.json()
        vehicles = (
            data['Siri']['ServiceDelivery']
            ['VehicleMonitoringDelivery'][0]
            .get('VehicleActivity', [])
        )

        if not vehicles:
            pytest.skip("No vehicles returned from API")

        mc = vehicles[0]['MonitoredVehicleJourney'].get(
            'MonitoredCall', {}
        )
        assert 'AimedArrivalTime' in mc, (
            "Missing AimedArrivalTime in MonitoredCall"
        )
