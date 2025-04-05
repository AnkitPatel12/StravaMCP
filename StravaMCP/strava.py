#!/usr/bin/env python3
"""
Strava MCP Server with fixed tool naming that complies with MCP protocol requirements.
"""
from typing import Any, Dict, List, Optional
import httpx
from mcp.server.fastmcp import FastMCP
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("strava_mcp.log"),
    ]
)

load_dotenv()


mcp = FastMCP("strava")

STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

logging.info("Strava MCP server initialized")

async def refresh_access_token() -> bool:
    """Refresh the access token using the refresh token."""
    global STRAVA_ACCESS_TOKEN, STRAVA_REFRESH_TOKEN
    
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
            
            # Update tokens
            STRAVA_ACCESS_TOKEN = token_data["access_token"]
            STRAVA_REFRESH_TOKEN = token_data["refresh_token"]
            
            return True
        except Exception as e:
            logging.error(f"Error refreshing token: {str(e)}")
            return False

async def make_strava_request(endpoint: str, params: Optional[dict] = None) -> dict[str, Any] | None:
    """Make a request to the Strava API with proper error handling."""
    global STRAVA_ACCESS_TOKEN
    
    if not STRAVA_ACCESS_TOKEN:
        if not await refresh_access_token():
            return None
    
    if params is None:
        params = {}
    
    params['access_token'] = STRAVA_ACCESS_TOKEN
    
    url = f"{STRAVA_API_BASE_URL}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=30.0)
            
            # Check if token is expired (401 Unauthorized)
            if response.status_code == 401:
                if await refresh_access_token():
                    # Retry the request with the new token
                    params['access_token'] = STRAVA_ACCESS_TOKEN
                    response = await client.get(url, params=params, timeout=30.0)
                    response.raise_for_status()
                    return response.json()
                else:
                    return None
            
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_activity(activity: dict) -> Dict[str, Any]:
    """Format an activity into a structured dictionary."""
    start_date = activity.get('start_date', '')
    formatted_date = (
        datetime.fromisoformat(start_date.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
        if start_date else "Unknown"
    )
    
    return {
        "name": activity.get('name', 'Unknown'),
        "type": activity.get('type', 'Unknown'),
        "distance_km": round(activity.get('distance', 0) / 1000, 2),
        "moving_time_minutes": round(activity.get('moving_time', 0) / 60, 0),
        "elevation_gain_m": round(activity.get('total_elevation_gain', 0), 0),
        "average_speed_kph": round(activity.get('average_speed', 0) * 3.6, 1),
        "max_speed_kph": round(activity.get('max_speed', 0) * 3.6, 1),
        "date": formatted_date,
        "id": activity.get('id'),
        "athlete_id": activity.get('athlete', {}).get('id')
    }

def format_stats(stats: dict) -> Dict[str, Any]:
    """Format athlete stats into a structured dictionary."""
    if not stats:
        return {"error": "No stats available"}
    
    return {
        "recent_ride_totals": {
            "count": stats.get("recent_ride_totals", {}).get("count", 0),
            "distance_km": round(stats.get("recent_ride_totals", {}).get("distance", 0) / 1000, 2),
            "moving_time_hours": round(stats.get("recent_ride_totals", {}).get("moving_time", 0) / 3600, 2),
            "elevation_gain_m": round(stats.get("recent_ride_totals", {}).get("elevation_gain", 0), 0)
        },
        "recent_run_totals": {
            "count": stats.get("recent_run_totals", {}).get("count", 0),
            "distance_km": round(stats.get("recent_run_totals", {}).get("distance", 0) / 1000, 2),
            "moving_time_hours": round(stats.get("recent_run_totals", {}).get("moving_time", 0) / 3600, 2),
            "elevation_gain_m": round(stats.get("recent_run_totals", {}).get("elevation_gain", 0), 0)
        },
        "ytd_ride_totals": {
            "count": stats.get("ytd_ride_totals", {}).get("count", 0),
            "distance_km": round(stats.get("ytd_ride_totals", {}).get("distance", 0) / 1000, 2),
            "moving_time_hours": round(stats.get("ytd_ride_totals", {}).get("moving_time", 0) / 3600, 2),
            "elevation_gain_m": round(stats.get("ytd_ride_totals", {}).get("elevation_gain", 0), 0)
        },
        "ytd_run_totals": {
            "count": stats.get("ytd_run_totals", {}).get("count", 0),
            "distance_km": round(stats.get("ytd_run_totals", {}).get("distance", 0) / 1000, 2),
            "moving_time_hours": round(stats.get("ytd_run_totals", {}).get("moving_time", 0) / 3600, 2),
            "elevation_gain_m": round(stats.get("ytd_run_totals", {}).get("elevation_gain", 0), 0)
        },
        "all_ride_totals": {
            "count": stats.get("all_ride_totals", {}).get("count", 0),
            "distance_km": round(stats.get("all_ride_totals", {}).get("distance", 0) / 1000, 2),
            "moving_time_hours": round(stats.get("all_ride_totals", {}).get("moving_time", 0) / 3600, 2),
            "elevation_gain_m": round(stats.get("all_ride_totals", {}).get("elevation_gain", 0), 0)
        },
        "all_run_totals": {
            "count": stats.get("all_run_totals", {}).get("count", 0),
            "distance_km": round(stats.get("all_run_totals", {}).get("distance", 0) / 1000, 2),
            "moving_time_hours": round(stats.get("all_run_totals", {}).get("moving_time", 0) / 3600, 2),
            "elevation_gain_m": round(stats.get("all_run_totals", {}).get("elevation_gain", 0), 0)
        }
    }

async def get_activity_details(activity_id: int) -> Dict[str, Any] | None:
    endpoint = f"activities/{activity_id}"
    return await make_strava_request(endpoint)

async def get_athlete_activities(per_page: int = 30, page: int = 1) -> List[Dict[str, Any]] | None:
    endpoint = "athlete/activities"
    params = {
        "per_page": per_page,
        "page": page
    }
    return await make_strava_request(endpoint, params)

async def get_athlete_stats(athlete_id: int) -> Dict[str, Any] | None:
    endpoint = f"athletes/{athlete_id}/stats"
    return await make_strava_request(endpoint)

@mcp.tool("ping")
async def ping() -> Dict[str, Any]:
    """Simple ping endpoint to test server connectivity."""
    return {"status": "ok", "message": "Strava MCP server is running!"}

@mcp.tool("activities")
async def get_activities(per_page: int = 30, page: int = 1) -> Dict[str, Any]:
    """Get the authenticated athlete's activities."""
    activities = await get_athlete_activities(per_page, page)
    
    if not activities:
        return {"success": False, "error": "Failed to fetch activities", "data": []}
    
    formatted_activities = [format_activity(activity) for activity in activities]
    return {
        "success": True,
        "count": len(formatted_activities),
        "data": formatted_activities
    }

@mcp.tool("stats")
async def get_stats(athlete_id: int) -> Dict[str, Any]:
    """Get the authenticated athlete's stats."""
    stats = await get_athlete_stats(athlete_id)
    
    if not stats:
        return {"success": False, "error": "Failed to fetch athlete stats", "data": {}}
    
    formatted_stats = format_stats(stats)
    return {
        "success": True,
        "data": formatted_stats
    }

@mcp.tool("activity")
async def get_activity(activity_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific activity."""
    activity = await get_activity_details(activity_id)
    
    if not activity:
        return {"success": False, "error": f"Failed to fetch activity {activity_id}", "data": {}}
    
    formatted_activity = format_activity(activity)
    
    # Add additional activity details
    formatted_activity["description"] = activity.get("description", "")
    formatted_activity["kudos_count"] = activity.get("kudos_count", 0)
    formatted_activity["comment_count"] = activity.get("comment_count", 0)
    formatted_activity["achievement_count"] = activity.get("achievement_count", 0)
    formatted_activity["gear_id"] = activity.get("gear_id", "")
    
    # Add splits if available
    if "splits_metric" in activity:
        # Make sure splits are JSON serializable
        splits = []
        for split in activity.get("splits_metric", []):
            # Convert all values to simple types
            clean_split = {k: (float(v) if isinstance(v, (int, float)) else str(v)) for k, v in split.items()}
            splits.append(clean_split)
        
        formatted_activity["splits"] = splits
    
    return {
        "success": True,
        "data": formatted_activity
    }

@mcp.tool("athlete")
async def get_athlete() -> Dict[str, Any]:
    """Get authenticated athlete's profile information."""
    athlete = await make_strava_request("athlete")
    
    if not athlete:
        return {"success": False, "error": "Failed to fetch athlete profile", "data": {}}
    
    # Create a clean, serializable dictionary
    formatted_athlete = {
        "id": athlete.get("id"),
        "username": athlete.get("username", ""),
        "firstname": athlete.get("firstname", ""),
        "lastname": athlete.get("lastname", ""),
        "city": athlete.get("city", ""),
        "state": athlete.get("state", ""),
        "country": athlete.get("country", ""),
        "profile": athlete.get("profile", ""),
        "follower_count": athlete.get("follower_count", 0),
        "friend_count": athlete.get("friend_count", 0),
        "measurement_preference": athlete.get("measurement_preference", ""),
        "ftp": athlete.get("ftp", 0)
    }
    
    return {
        "success": True,
        "data": formatted_athlete
    }

@mcp.tool("routes")
async def get_routes(per_page: int = 30, page: int = 1) -> Dict[str, Any]:
    """Get routes created by the authenticated athlete."""
    endpoint = "athletes/routes"
    params = {
        "per_page": per_page,
        "page": page
    }
    
    routes = await make_strava_request(endpoint, params)
    
    if not routes:
        return {"success": False, "error": "Failed to fetch routes", "data": []}
    
    formatted_routes = []
    for route in routes:
        formatted_routes.append({
            "id": route.get("id"),
            "name": route.get("name", ""),
            "description": route.get("description", ""),
            "distance_km": round(route.get("distance", 0) / 1000, 2),
            "elevation_gain_m": round(route.get("elevation_gain", 0), 0),
            "map_url": route.get("map_urls", {}).get("url", "")
        })
    
    return {
        "success": True,
        "count": len(formatted_routes),
        "data": formatted_routes
    }


if __name__ == "__main__":
    mcp.run(transport='stdio')