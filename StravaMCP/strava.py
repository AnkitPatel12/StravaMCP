from typing import Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP
import os
from datetime import datetime

# Initialize FastMCP server
mcp = FastMCP("strava")

# Strava API configuration
STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")

async def make_strava_request(endpoint: str, params: Optional[dict] = None) -> dict[str, Any] | None:
    """Make a request to the Strava API with proper error handling."""
    headers = {
        "Authorization": f"Bearer {STRAVA_ACCESS_TOKEN}",
        "Accept": "application/json"
    }
    
    url = f"{STRAVA_API_BASE_URL}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

def format_activity(activity: dict) -> str:
    """Format an activity into a readable string."""
    return f"""
        Activity: {activity.get('name', 'Unknown')}
        Type: {activity.get('type', 'Unknown')}
        Distance: {activity.get('distance', 0) / 1000:.2f} km
        Moving Time: {activity.get('moving_time', 0) / 60:.0f} minutes
        Elevation Gain: {activity.get('total_elevation_gain', 0):.0f} m
        Average Speed: {activity.get('average_speed', 0) * 3.6:.1f} km/h
        Max Speed: {activity.get('max_speed', 0) * 3.6:.1f} km/h
        Date: {datetime.fromisoformat(activity.get('start_date', '').replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}
        """

async def get_athlete_activities(per_page: int = 30, page: int = 1) -> list[dict] | None:
    """Get the authenticated athlete's activities."""
    endpoint = "athlete/activities"
    params = {
        "per_page": per_page,
        "page": page
    }
    return await make_strava_request(endpoint, params)

async def get_athlete_stats(athlete_id: int) -> dict[str, Any] | None:
    """Get the authenticated athlete's stats."""
    endpoint = f"athletes/{athlete_id}/stats"
    return await make_strava_request(endpoint)

async def get_activity_details(activity_id: int) -> dict[str, Any] | None:
    """Get detailed information about a specific activity."""
    endpoint = f"activities/{activity_id}"
    return await make_strava_request(endpoint) 


