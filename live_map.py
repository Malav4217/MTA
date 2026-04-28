import json

def get_live_map_html(api_key, selected_routes, buses):
    bus_json = json.dumps(buses)
    route_colors_json = json.dumps({
        'M15': '#FF4444',
        'BX12': '#4444FF',
        'B46': '#44BB44',
        'Q58': '#FF8800'
    })
    selected_routes_json = json.dumps(selected_routes)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background: #f0f2f6; }}
            #map {{ height: 550px; width: 100%; border-radius: 10px; }}
            .bus-label {{
                background: transparent;
                border: none;
                font-size: 20px;
            }}
            .legend {{
                background: rgba(255,255,255,0.9);
                padding: 10px 14px;
                border-radius: 8px;
                color: black;
                font-family: monospace;
                font-size: 13px;
                line-height: 1.8;
                border: 1px solid #ccc;
            }}
            #refreshBtn {{
                margin-bottom: 10px;
                padding: 8px 16px;
                background: #ff4b4b;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <button id="refreshBtn" onclick="(async () => updateBuses(await fetchBuses()))()"> Refresh Now</button><br>
        <div id="map"></div>
        <script>
            var apiKey = '{api_key}';
            var selectedRoutes = {selected_routes_json};
            var routeColors = {route_colors_json};
            var markers = {{}};

            // Initialize map centered on NYC
            var map = L.map('map').setView([40.7549, -73.9840], 12);

            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }}).addTo(map);

            function getBusIcon(color) {{
                return L.divIcon({{
                    className: 'bus-label',
                    html: `<div style="
                        background: ${{color}};
                        color: white;
                        border-radius: 50%;
                        width: 28px;
                        height: 28px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 14px;
                        font-weight: bold;
                        border: 2px solid white;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.5);
                    ">B</div>`,
                    iconSize: [28, 28],
                    iconAnchor: [14, 14]
                }});
            }}

            function updateBuses(buses) {{
                var seen = {{}};
                buses.forEach(function(bus) {{
                    var id = bus.vehicle_id;
                    var color = routeColors[bus.route] || '#888888';
                    var popup = `
                        <div style="font-family:monospace;min-width:180px">
                            <b style="color:${{color}}">Route ${{bus.route}}</b><br>
                            Vehicle: ${{bus.vehicle_id}}<br>
                            Stop: ${{bus.stop_name}}<br>
                            Distance: ${{bus.distance}}<br>
                            Scheduled: ${{bus.aimed.substring(11,16) || 'N/A'}}<br>
                            Expected: ${{bus.expected.substring(11,16) || 'N/A'}}
                        </div>`;

                    if (markers[id]) {{
                        markers[id].setLatLng([bus.latitude, bus.longitude]);
                        markers[id].setPopupContent(popup);
                    }} else {{
                        markers[id] = L.marker([bus.latitude, bus.longitude], {{
                            icon: getBusIcon(color)
                        }}).bindPopup(popup).addTo(map);
                    }}
                    seen[id] = true;
                }});

                // Remove buses no longer in feed
                Object.keys(markers).forEach(function(id) {{
                    if (!seen[id]) {{
                        map.removeLayer(markers[id]);
                        delete markers[id];
                    }}
                }});
            }}

            async function fetchBuses() {{
                const allBuses = [];
                for (const route of selectedRoutes) {{
                    try {{
                        const params = new URLSearchParams({{
                            key: apiKey,
                            LineRef: `MTA NYCT_${{route}}`,
                            VehicleMonitoringDetailLevel: 'calls'
                        }});
                        const response = await fetch(`http://bustime.mta.info/api/siri/vehicle-monitoring.json?${{params}}`);
                        const data = await response.json();
                        const vehicles = data.Siri.ServiceDelivery.VehicleMonitoringDelivery[0].VehicleActivity || [];
                        for (const v of vehicles) {{
                            const mvj = v.MonitoredVehicleJourney;
                            const mc = mvj.MonitoredCall || {{}};
                            allBuses.push({{
                                route: route,
                                vehicle_id: mvj.VehicleRef || '',
                                latitude: parseFloat(mvj.VehicleLocation.Latitude),
                                longitude: parseFloat(mvj.VehicleLocation.Longitude),
                                stop_name: mc.StopPointName || 'Unknown',
                                distance: (mc.Extensions?.Distances?.PresentableDistance) || 'N/A',
                                aimed: mc.AimedArrivalTime || 'N/A',
                                expected: mc.ExpectedArrivalTime || mc.AimedArrivalTime || 'N/A'
                            }});
                        }}
                    }} catch (e) {{
                        console.error(`Error fetching ${{route}}:`, e);
                    }}
                }}
                return allBuses;
            }}

            // Add legend
            var legend = L.control({{position: 'bottomright'}});
            legend.onAdd = function() {{
                var div = L.DomUtil.create('div', 'legend');
                div.innerHTML = Object.entries(routeColors)
                    .map(([r,c]) => `<span style="color:${{c}}">●</span> ${{r}}`)
                    .join('<br>');
                return div;
            }};
            legend.addTo(map);

            // Auto refresh every 30 seconds
            setInterval(async () => {{
                const newBuses = await fetchBuses();
                updateBuses(newBuses);
            }}, 30000);

            // Load initial buses
            var busData = {bus_json};
            updateBuses(busData);

        </script>
    </body>
    </html>
    """
