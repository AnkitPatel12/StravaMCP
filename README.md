# Strava Model Context Protocol (MCP)

This is a Python-based Model Context Protocol for Strava data that allows you to fetch and analyze your Strava activities.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Get your Strava Access Token:
   - Go to https://www.strava.com/settings/api
   - Create an application if you haven't already
   - Get your access token
   - Copy your access token to the `.env` file:
     ```
     STRAVA_ACCESS_TOKEN=your_access_token_here
     ```

## Usage

Run the MCP script:
```bash
python strava_mcp.py
```

The script will:
1. Connect to your Strava account
2. Display your recent activities
3. Show weekly statistics including:
   - Total distance
   - Total time
   - Total elevation gain
   - Number of activities

## Features

- Fetch athlete information
- Get recent activities with detailed metrics
- Calculate weekly statistics
- Access detailed metrics for specific activities

## Data Structure

The MCP uses the following data structures:

- `ActivityMetrics`: A dataclass containing detailed metrics for a single activity
- `StravaMCP`: The main class that handles all Strava API interactions

## Error Handling

The script includes basic error handling for:
- Missing access token
- API connection issues
- Invalid activity IDs 