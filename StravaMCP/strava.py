from typing import Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP
import os
from datetime import datetime
from dotenv import load_dotenv
import time

#load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("strava")

# Strava API configuration
STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")
TOKEN_EXPIRY = 0  # Track when the token expires

async def refresh_access_token() -> bool:
    """Refresh the access token using the refresh token."""
    global STRAVA_ACCESS_TOKEN, TOKEN_EXPIRY
    
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "refresh_token": STRAVA_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            STRAVA_ACCESS_TOKEN = token_data["access_token"]
            expiry_datetime = datetime.fromisoformat(token_data["expires_at"].replace('Z', '+00:00'))
            TOKEN_EXPIRY = expiry_datetime.timestamp()
            TOKEN_EXPIRY = time.time() + token_data["expires_at"]
            return True
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return False

async def make_strava_request(endpoint: str, params: Optional[dict] = None) -> dict[str, Any] | None:
    """Make a request to the Strava API with proper error handling."""
    global STRAVA_ACCESS_TOKEN
        
    if not STRAVA_ACCESS_TOKEN:
        print("Error: STRAVA_ACCESS_TOKEN not found in environment variables")
        return None
        
    # Check if token needs refresh
    if time.time() >= TOKEN_EXPIRY:
        success = await refresh_access_token()
        if not success:
            print("Failed to refresh token")
            return None
        
    # Initialize params if None
    if params is None:
        params = {}
    
    # Add access_token to params
    params['access_token'] = STRAVA_ACCESS_TOKEN
    
    url = f"{STRAVA_API_BASE_URL}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=30.0)
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


