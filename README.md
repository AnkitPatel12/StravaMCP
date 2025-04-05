# Strava MCP Server

A Model Context Protocol (MCP) server that connects to Strava's API, allowing you to retrieve your fitness data and interact with it via Claude or other AI assistants.

## Overview

This project provides a [Model Context Protocol](https://modelcontextprotocol.io/) server that connects to the Strava API. It enables AI assistants like Claude to access and analyze your Strava data, including:

- Activities (runs, rides, swims, etc.)
- Athlete statistics
- Activity details
- Routes
- Athlete profile information

## Requirements

- Python 3.10 or higher
- A Strava account with API access
- Strava API credentials (client ID, client secret, and refresh token)
- Claude for Desktop or another MCP-compatible AI assistant
- `uv` package manager (recommended for environment setup)

## Installation

### Option 1: Using the GitHub Repository

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/strava-mcp.git
   cd strava-mcp
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   # Or with uv:
   uv pip install -r requirements.txt
   ```

3. Create a `.env` file with your Strava API credentials (see below).

### Option 2: Setting Up From Scratch with uv

1. Install `uv` package manager:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   *Note: Restart your terminal after installation*

2. Create and set up your project:
   ```bash
   # Create a new directory for the project
   uv init strava-mcp
   cd strava-mcp

   # Create virtual environment and activate it
   uv venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate

   # Install dependencies
   uv add "mcp[cli]" httpx python-dotenv
   ```

3. Download the `strava.py` file from the GitHub repository or create your own.

4. Create a `.env` file in the project directory with your Strava API credentials:
   ```
   STRAVA_CLIENT_ID=your_client_id
   STRAVA_CLIENT_SECRET=your_client_secret
   STRAVA_REFRESH_TOKEN=your_refresh_token
   STRAVA_ACCESS_TOKEN=your_access_token 
   ```

## Getting Strava API Credentials

To use this MCP server, you need to register an application with Strava to obtain API credentials.

### Step 1: Create a Strava API Application

1. Log in to your Strava account
2. Go to [https://www.strava.com/settings/api](https://www.strava.com/settings/api)
3. Create a new application:
   - Enter an application name (e.g., "My Strava MCP")
   - Enter a website (e.g., your GitHub profile or "http://localhost")
   - Enter a description
   - Upload an icon (optional)
   - Set the authorization callback domain to `localhost`
4. After creating the application, you'll receive a **Client ID** and **Client Secret**

### Step 2: Authorize Your Application

You need to authorize your application to obtain a refresh token:

1. Construct the authorization URL with your client ID:
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost&response_type=code&scope=activity:read_all,profile:read_all,read_all
   ```

2. Visit this URL in your browser and click "Authorize"

3. You'll be redirected to a URL like:
   ```
   http://localhost?state=&code=AUTHORIZATION_CODE
   ```

4. Extract the authorization code from the URL (it's the value after `code=`)

### Step 3: Exchange the Authorization Code for Tokens

Use the authorization code to obtain access and refresh tokens:

```bash
curl -X POST https://www.strava.com/oauth/token \
  -F client_id=YOUR_CLIENT_ID \
  -F client_secret=YOUR_CLIENT_SECRET \
  -F code=AUTHORIZATION_CODE \
  -F grant_type=authorization_code
```

The response will include an `access_token` and a `refresh_token`. Add these to your `.env` file.

## Usage

### Running the MCP Server

Run the server using `uv`:

```bash
# From within your project directory
uv run strava.py
```

Or using Python directly:

```bash
python strava.py
```

### Configuring Claude for Desktop

1. Open Claude for Desktop
2. Click on your profile picture in the top right, then select "Settings"
3. Navigate to the "Experimental" section
4. Toggle on "Enable Model Context Protocol"
5. Click "Edit Config" to open the configuration file. The default locations are:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
6. Add your Strava MCP server to the configuration:

```json
{
    "mcpServers": {
        "strava": {
            "command": "uv",
            "args": [
                "--directory",
                "/ABSOLUTE/PATH/TO/YOUR/strava-mcp",
                "run",
                "strava.py"
            ]
        }
    }
}
```

For example, if your project is in `/Users/username/projects/strava-mcp`, your configuration would be:

```json
{
    "mcpServers": {
        "strava": {
            "command": "uv",
            "args": [
                "--directory",
                "/Users/username/projects/strava-mcp",
                "run",
                "strava.py"
            ]
        }
    }
}
```

You can also use the full path to the Python interpreter instead:

```json
{
    "mcpServers": {
        "strava": {
            "command": "/usr/bin/python3",
            "args": [
                "/ABSOLUTE/PATH/TO/YOUR/strava-mcp/strava.py"
            ]
        }
    }
}
```

7. Save the file and restart Claude for Desktop

### Available Tools

The Strava MCP server provides the following tools:

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `ping` | Simple ping endpoint to test connectivity | None |
| `activities` | List your recent activities | `per_page`: Number of activities to return (default: 30)<br>`page`: Page number (default: 1) |
| `activity` | Get detailed information about a specific activity | `activity_id`: ID of the activity |
| `athlete` | Get your profile information | None |
| `stats` | Get your athlete statistics | `athlete_id`: ID of the athlete |
| `routes` | List your saved routes | `per_page`: Number of routes to return (default: 30)<br>`page`: Page number (default: 1) |

When your MCP server is properly connected to Claude, you'll see a hammer icon (🔨) in the interface. Click this icon to see the available tools from your Strava MCP server.

### Example Queries for Claude

Once your MCP server is properly configured and running, you can ask Claude questions like:

- "What are my most recent activities?"
- "Show me my running statistics for this year."
- "What was my longest ride in the past month?"
- "Calculate my average pace for my recent runs."
- "Analyze my training pattern over the last few weeks."
- "Compare my cycling performance this month with last month."
- "What's my total elevation gain from hiking activities?"
- "Show me details about my most recent marathon."
- "How many kilometers have I run this year?"
- "Am I training consistently based on my activity history?"

## Strava API Details

### Supported Activity Types

Strava supports many activity types including:
- Run
- Ride (cycling)
- Swim
- Hike
- Walk
- Alpine Ski
- Backcountry Ski
- Canoe
- Crossfit
- E-Bike Ride
- Elliptical
- Handcycle
- Ice Skate
- Inline Skate
- Kayak
- Kitesurf
- Nordic Ski
- Rock Climb
- Roller Ski
- Row
- Snowboard
- Snowshoe
- Stair Stepper
- Stand Up Paddle
- Surf
- Velomobile
- Virtual Ride
- Virtual Run
- Weight Training
- Wheelchair
- Windsurf
- Workout
- Yoga

### API Rate Limits

The Strava API has the following rate limits:
- 100 requests every 15 minutes
- 1,000 requests per day

The MCP server handles these limits gracefully and will wait if limits are reached.

### Data Privacy

This MCP server only accesses the Strava data you've authorized. It does not store any data permanently - it simply passes information between Strava and Claude. Your Strava credentials are stored only in your local `.env` file.

## Architecture

This MCP server:
1. Authenticates with the Strava API using OAuth2
2. Automatically refreshes tokens when they expire
3. Converts Strava API responses into a format suitable for AI analysis
4. Implements the Model Context Protocol to communicate with AI assistants
5. Provides a clean, consistent interface to access your fitness data

### How It Works

When you ask Claude a question about your Strava data:

1. Claude analyzes your request and determines which Strava tool to use
2. Claude sends a request to the MCP server with the appropriate tool name and parameters
3. The MCP server makes the necessary API calls to Strava
4. Strava returns the data, which the MCP server formats and sends back to Claude
5. Claude processes the data and generates a response that answers your question

This flow allows Claude to access your Strava data without needing direct API access, and without sharing your API credentials with Claude.

## Troubleshooting

### Connection Issues

If you're having trouble connecting to Strava:

1. Verify your credentials in the `.env` file
2. Make sure you've granted the necessary permissions
3. Try refreshing your tokens manually
4. Check your internet connection

### Strava API Issues

Common Strava API issues include:

- **401 Unauthorized**: Your access token is invalid or expired. The server should automatically refresh it, but if it can't, you may need to obtain a new refresh token.
- **403 Forbidden**: You're trying to access data you don't have permission for.
- **404 Not Found**: The requested resource doesn't exist.
- **429 Too Many Requests**: You've hit the API rate limit.

### Error: No access token
If you see this error, your refresh token may be invalid or expired. Follow the steps in "Getting Strava API Credentials" to obtain a new refresh token.

### Error: String should match pattern
If you see this error, it means the tool name format is incorrect. Make sure all tool names follow the pattern `^[a-zA-Z0-9_-]{1,64}$` (only letters, numbers, underscores, and hyphens). Do not use forward slashes or special characters in your tool names.

### Claude for Desktop Debugging

If Claude for Desktop isn't recognizing your MCP server:

1. **Check the Configuration**:
   - Make sure your `claude_desktop_config.json` file is formatted correctly
   - Ensure all paths are absolute paths
   - Verify the server name matches in your code and config

2. **Check the Logs**:
   ```bash
   # On macOS:
   tail -f ~/Library/Logs/Claude/mcp*.log
   
   # On Windows:
   type %APPDATA%\Claude\Logs\mcp*.log
   ```

3. **Check for Claude Updates**:
   - Make sure Claude for Desktop is updated to the latest version

4. **Restart Claude for Desktop**:
   - After making configuration changes, restart Claude for Desktop

5. **Advanced Logging**:
   ```bash
   # To save logs to a file:
   tail -n 20 -F ~/Library/Logs/Claude/mcp*.log > strava_log_output.txt 2>&1
   
   # To both view and save logs:
   tail -n 20 -F ~/Library/Logs/Claude/mcp*.log | tee strava_log_output.txt
   ```

6. **Use the MCP Inspector**:
   ```bash
   # First, install the MCP CLI tools if you haven't already:
   pip install mcp[cli]
   
   # Then, run the inspector:
   mcp inspect --server-id strava
   ```

7. **Run the Server in Debug Mode**:
   ```bash
   # If your server supports a debug flag:
   python strava.py --debug
   # Or:
   uv run strava.py --debug
   ```

## Security Considerations

This MCP server stores your Strava API credentials in a `.env` file. Make sure to:
- Keep your `.env` file secure and never commit it to public repositories
- Review the permissions you grant when authorizing the API access
- Use the minimal scope required for your use case

## License

[MIT License](LICENSE)

## Acknowledgments

- [Strava API](https://developers.strava.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude AI Assistant](https://claude.ai/)
- [uv Package Manager](https://github.com/astral-sh/uv/)