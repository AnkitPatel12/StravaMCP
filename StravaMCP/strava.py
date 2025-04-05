from typing import Any, Optional, Dict, List
import httpx
from mcp.server.fastmcp import FastMCP
import os
from datetime import datetime
from dotenv import load_dotenv
import time
import asyncio
import logging
import sys
import json

# Configure logging
def setup_logging(log_level=logging.INFO):
    """Set up logging configuration with both file and console handlers."""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/strava_mcp_{timestamp}.log"
    
    # Configure logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(log_level)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logging.info(f"Logging initialized. Log file: {log_filename}")
    return logger

# Set up logging
logger = setup_logging()

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded from .env file")

# Initialize FastMCP server
mcp = FastMCP("strava")
logger.info("FastMCP server initialized with name 'strava'")

# Strava API configuration
STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")

# Log configuration status (without sensitive data)
if STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET and STRAVA_REFRESH_TOKEN:
    logger.info("Strava API credentials loaded successfully")
    logger.info(f"Using Client ID: {STRAVA_CLIENT_ID}")
    token_status = "Available" if STRAVA_ACCESS_TOKEN else "Not available (will be refreshed)"
    logger.info(f"Access token status: {token_status}")
else:
    logger.error("Some Strava API credentials are missing!")
    missing = []
    if not STRAVA_CLIENT_ID: missing.append("STRAVA_CLIENT_ID")
    if not STRAVA_CLIENT_SECRET: missing.append("STRAVA_CLIENT_SECRET")
    if not STRAVA_REFRESH_TOKEN: missing.append("STRAVA_REFRESH_TOKEN")
    logger.error(f"Missing credentials: {', '.join(missing)}")

async def refresh_access_token() -> bool:
    """Refresh the access token using the refresh token."""
    global STRAVA_ACCESS_TOKEN, STRAVA_REFRESH_TOKEN
    
    logger.info("Attempting to refresh access token...")
    
    url = "https://www.strava.com/oauth/token"
    data = {
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "refresh_token": STRAVA_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"Making refresh token request to {url}")
            response = await client.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            # Update tokens
            STRAVA_ACCESS_TOKEN = token_data["access_token"]
            STRAVA_REFRESH_TOKEN = token_data["refresh_token"]
            
            expires_at = datetime.fromtimestamp(token_data["expires_at"]).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"Token refreshed successfully. Expires at {expires_at}")
            logger.debug(f"New refresh token obtained. Access token: {STRAVA_ACCESS_TOKEN[:5]}...")
            
            return True
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return False

async def make_strava_request(endpoint: str, params: Optional[dict] = None) -> dict[str, Any] | None:
    """Make a request to the Strava API with proper error handling."""
    global STRAVA_ACCESS_TOKEN
    
    if not STRAVA_ACCESS_TOKEN:
        logger.error("STRAVA_ACCESS_TOKEN not found in environment variables")
        if not await refresh_access_token():
            logger.error("Failed to obtain access token")
            return None
    
    # Initialize params if None
    if params is None:
        params = {}
    
    # Add access_token to params
    params['access_token'] = STRAVA_ACCESS_TOKEN
    
    url = f"{STRAVA_API_BASE_URL}/{endpoint}"
    logger.info(f"Making Strava API request to endpoint: {endpoint}")
    logger.debug(f"Request URL: {url}")
    logger.debug(f"Request params: {json.dumps({k: v for k, v in params.items() if k != 'access_token'})}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=30.0)
            
            # Check if token is expired (401 Unauthorized)
            if response.status_code == 401:
                logger.warning("Token expired (401 Unauthorized), refreshing...")
                if await refresh_access_token():
                    # Retry the request with the new token
                    params['access_token'] = STRAVA_ACCESS_TOKEN
                    logger.info("Retrying request with new token")
                    response = await client.get(url, params=params, timeout=30.0)
                    response.raise_for_status()
                    logger.debug(f"Response status: {response.status_code}")
                    return response.json()
                else:
                    logger.error("Failed to refresh token")
                    return None
            
            response.raise_for_status()
            logger.debug(f"Response status: {response.status_code}")
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            logger.error(f"Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            return None
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return None

def format_activity(activity: dict) -> Dict[str, Any]:
    """Format an activity into a structured dictionary."""
    logger.debug(f"Formatting activity: {activity.get('id', 'unknown_id')}")
    
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
    logger.debug("Formatting athlete stats")
    
    if not stats:
        logger.warning("Empty stats data received")
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

@mcp.tool("/activities")
async def get_activities(per_page: int = 30, page: int = 1) -> Dict[str, Any]:
    """Get the authenticated athlete's activities."""
    logger.info(f"Fetching activities (page {page}, per_page {per_page})")
    
    activities = await get_athlete_activities(per_page, page)
    
    if not activities:
        logger.error("Failed to fetch activities")
        return {"error": "Failed to fetch activities", "data": []}
    
    logger.info(f"Successfully fetched {len(activities)} activities")
    formatted_activities = [format_activity(activity) for activity in activities]
    
    return {
        "success": True,
        "count": len(formatted_activities),
        "data": formatted_activities
    }

@mcp.tool("/stats/{athlete_id}")
async def get_stats(athlete_id: int) -> Dict[str, Any]:
    """Get the authenticated athlete's stats."""
    logger.info(f"Fetching stats for athlete_id: {athlete_id}")
    
    stats = await get_athlete_stats(athlete_id)
    
    if not stats:
        logger.error(f"Failed to fetch stats for athlete_id: {athlete_id}")
        return {"error": "Failed to fetch athlete stats", "data": {}}
    
    logger.info("Successfully fetched athlete stats")
    formatted_stats = format_stats(stats)
    
    return {
        "success": True,
        "data": formatted_stats
    }

@mcp.tool("/activity/{activity_id}")
async def get_activity(activity_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific activity."""
    logger.info(f"Fetching details for activity_id: {activity_id}")
    
    activity = await get_activity_details(activity_id)
    
    if not activity:
        logger.error(f"Failed to fetch activity {activity_id}")
        return {"error": f"Failed to fetch activity {activity_id}", "data": {}}
    
    logger.info(f"Successfully fetched details for activity: {activity.get('name', 'unnamed')}")
    formatted_activity = format_activity(activity)
    
    # Add additional activity details
    formatted_activity["description"] = activity.get("description", "")
    formatted_activity["kudos_count"] = activity.get("kudos_count", 0)
    formatted_activity["comment_count"] = activity.get("comment_count", 0)
    formatted_activity["achievement_count"] = activity.get("achievement_count", 0)
    formatted_activity["gear_id"] = activity.get("gear_id", "")
    
    # Add splits if available
    if "splits_metric" in activity:
        logger.debug(f"Activity has {len(activity.get('splits_metric', []))} splits")
        formatted_activity["splits"] = activity.get("splits_metric", [])
    
    return {
        "success": True,
        "data": formatted_activity
    }

@mcp.tool("/athlete")
async def get_athlete() -> Dict[str, Any]:
    """Get authenticated athlete's profile information."""
    logger.info("Fetching athlete profile")
    
    athlete = await make_strava_request("athlete")
    
    if not athlete:
        logger.error("Failed to fetch athlete profile")
        return {"error": "Failed to fetch athlete profile", "data": {}}
    
    logger.info(f"Successfully fetched profile for {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
    
    formatted_athlete = {
        "id": athlete.get("id"),
        "username": athlete.get("username"),
        "firstname": athlete.get("firstname"),
        "lastname": athlete.get("lastname"),
        "city": athlete.get("city"),
        "state": athlete.get("state"),
        "country": athlete.get("country"),
        "profile": athlete.get("profile"),
        "follower_count": athlete.get("follower_count"),
        "friend_count": athlete.get("friend_count"),
        "measurement_preference": athlete.get("measurement_preference"),
        "ftp": athlete.get("ftp")
    }
    
    return {
        "success": True,
        "data": formatted_athlete
    }

@mcp.tool("/routes")
async def get_routes(per_page: int = 30, page: int = 1) -> Dict[str, Any]:
    """Get routes created by the authenticated athlete."""
    logger.info(f"Fetching routes (page {page}, per_page {per_page})")
    
    endpoint = "athletes/routes"
    params = {
        "per_page": per_page,
        "page": page
    }
    
    routes = await make_strava_request(endpoint, params)
    
    if not routes:
        logger.error("Failed to fetch routes")
        return {"error": "Failed to fetch routes", "data": []}
    
    logger.info(f"Successfully fetched {len(routes)} routes")
    
    formatted_routes = []
    for route in routes:
        formatted_routes.append({
            "id": route.get("id"),
            "name": route.get("name"),
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

async def get_activity_details(activity_id: int) -> Dict[str, Any] | None:
    """Get detailed information about a specific activity."""
    logger.debug(f"Calling get_activity_details for activity_id: {activity_id}")
    endpoint = f"activities/{activity_id}"
    return await make_strava_request(endpoint)

async def get_athlete_activities(per_page: int = 30, page: int = 1) -> List[Dict[str, Any]] | None:
    """Get the authenticated athlete's activities."""
    logger.debug(f"Calling get_athlete_activities with per_page={per_page}, page={page}")
    endpoint = "athlete/activities"
    params = {
        "per_page": per_page,
        "page": page
    }
    return await make_strava_request(endpoint, params)

async def get_athlete_stats(athlete_id: int) -> Dict[str, Any] | None:
    """Get the authenticated athlete's stats."""
    logger.debug(f"Calling get_athlete_stats for athlete_id: {athlete_id}")
    endpoint = f"athletes/{athlete_id}/stats"
    return await make_strava_request(endpoint)

async def test_strava_connection():
    """Test function to verify Strava API connectivity and print sample data."""
    logger.info("=== STARTING STRAVA API CONNECTION TEST ===")
    
    # Step 1: Test token refresh
    logger.info("Testing token refresh...")
    refresh_success = await refresh_access_token()
    logger.info(f"Token refresh {'succeeded' if refresh_success else 'failed'}")
    
    if not refresh_success:
        logger.error("Cannot continue tests without valid token")
        return
    
    # Step 2: Get athlete info
    logger.info("Fetching athlete profile...")
    athlete = await make_strava_request("athlete")
    if athlete:
        athlete_id = athlete.get('id', '')
        logger.info(f"Connected to Strava as: {athlete.get('firstname', '')} {athlete.get('lastname', '')}")
        logger.info(f"Athlete ID: {athlete_id}")
        logger.info(f"Location: {athlete.get('city', '')}, {athlete.get('state', '')}, {athlete.get('country', '')}")
    else:
        logger.error("Failed to fetch athlete information")
        return
    
    # Step 3: Get recent activities
    logger.info("Fetching 5 most recent activities...")
    activities = await get_athlete_activities(per_page=5, page=1)
    if activities and len(activities) > 0:
        logger.info(f"Found {len(activities)} recent activities:")
        for idx, activity in enumerate(activities):
            formatted = format_activity(activity)
            logger.info(f"Activity {idx+1}: {formatted['name']} ({formatted['type']}) - {formatted['date']}")
            logger.info(f"  Distance: {formatted['distance_km']} km, ID: {formatted['id']}")
    else:
        logger.warning("No recent activities found or failed to fetch activities")
    
    # Step 4: Get athlete stats
    if athlete_id:
        logger.info("Fetching athlete stats...")
        stats = await get_athlete_stats(athlete_id)
        if stats:
            formatted_stats = format_stats(stats)
            
            run_stats = formatted_stats.get('recent_run_totals', {})
            logger.info(f"Recent running: {run_stats.get('count', 0)} runs, {run_stats.get('distance_km', 0)} km")
            
            ride_stats = formatted_stats.get('recent_ride_totals', {})
            logger.info(f"Recent cycling: {ride_stats.get('count', 0)} rides, {ride_stats.get('distance_km', 0)} km")
        else:
            logger.warning("Failed to fetch athlete stats")

    logger.info("=== STRAVA API TEST COMPLETE ===")

# # MCP protocol message handler
# @mcp.on_message
# async def handle_message(message):
#     """Log incoming MCP messages"""
#     logger.debug(f"Received MCP message: {message}")

# # MCP server lifecycle events
# @mcp.on_startup
# async def startup():
#     logger.info("MCP server starting up")
#     # Initialize any resources if needed
#     try:
#         refresh_success = await refresh_access_token()
#         if refresh_success:
#             logger.info("Initial token refresh successful")
#         else:
#             logger.warning("Initial token refresh failed")
#     except Exception as e:
#         logger.error(f"Error during startup: {e}")

# @mcp.on_shutdown
# async def shutdown():
#     logger.info("MCP server shutting down")
#     # Clean up any resources if needed

# Allow either testing or starting the server
if __name__ == "__main__":
    # import sys
    
    # if len(sys.argv) > 1 and sys.argv[1] == "--test":
    #     logger.info("Running in TEST mode")
    #     asyncio.run(test_strava_connection())
    # elif len(sys.argv) > 1 and sys.argv[1] == "--debug":
    #     # Set logging to DEBUG level for more verbose output
    #     logger.setLevel(logging.DEBUG)
    #     for handler in logger.handlers:
    #         handler.setLevel(logging.DEBUG)
    #     logger.info("Running in DEBUG mode with stdio transport")
    #     mcp.run(transport='stdio')
    # else:
    logger.info("Starting MCP server with stdio transport")
    mcp.run(transport='stdio')