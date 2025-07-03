from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Setup and run
# source .venv/bin/activate
# uv add "mcp[cli]" httpx

# Initialize server
mcp = FastMCP("weather")
print("Server initialized!")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


# Get data and format
async def request_url(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            print("Http Get request failed")
            return None
        

def alert_format(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


# Get MCP server endpoints

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await request_url(url)
    if not data or "features" not in data:
        return "Unable to fetch alerts or no alert found!"
    if not data["features"]:
        return "No current alerts for this state!"
    
    alerts = [alert_format(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get location
    points_url = f"{NWS_API_BASE}/pints/{latitude},{longitude}"
    points_data = await request_url(points_url)
    if not points_data:
        return "Unable to get forecast for this location!"
    
    # Get forecast for location
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await request_url(forecast_url)
    if not forecast_data:
        return "Unable to fetch forecast!"
    
    # Formate periods
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)



# Initialize and run server
if __name__ == "__main__":
    print("Starting server")
    mcp.run(transport='stdio')
    print("Server running")