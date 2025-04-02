import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from stravalib.client import Client
from dotenv import load_dotenv

@dataclass
class ActivityMetrics:
    distance: float
    moving_time: int
    total_elevation_gain: float
    average_speed: float
    max_speed: float
    average_heartrate: Optional[float]
    average_cadence: Optional[float]

class StravaMCP:
    def __init__(self):
        load_dotenv()
        self.client = Client()
        self.access_token = os.getenv('STRAVA_ACCESS_TOKEN')
        if self.access_token:
            self.client.access_token = self.access_token
        else:
            raise ValueError("STRAVA_ACCESS_TOKEN not found in environment variables")

    def get_athlete(self):
        """Get the authenticated athlete's information"""
        return self.client.get_athlete()

    def get_recent_activities(self, limit: int = 10) -> List[Dict]:
        """Fetch recent activities with detailed metrics"""
        activities = []
        for activity in self.client.get_activities(limit=limit):
            activity_dict = {
                'id': activity.id,
                'name': activity.name,
                'type': activity.type,
                'start_date': activity.start_date,
                'distance': activity.distance,
                'moving_time': activity.moving_time,
                'total_elevation_gain': activity.total_elevation_gain,
                'average_speed': activity.average_speed,
                'max_speed': activity.max_speed,
                'average_heartrate': activity.average_heartrate,
                'average_cadence': activity.average_cadence
            }
            activities.append(activity_dict)
        return activities

    def get_activity_metrics(self, activity_id: int) -> ActivityMetrics:
        """Get detailed metrics for a specific activity"""
        activity = self.client.get_activity(activity_id)
        return ActivityMetrics(
            distance=activity.distance,
            moving_time=activity.moving_time,
            total_elevation_gain=activity.total_elevation_gain,
            average_speed=activity.average_speed,
            max_speed=activity.max_speed,
            average_heartrate=activity.average_heartrate,
            average_cadence=activity.average_cadence
        )

    def get_weekly_stats(self) -> Dict:
        """Calculate weekly statistics"""
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        
        activities = self.client.get_activities(after=week_ago)
        
        total_distance = 0
        total_time = 0
        total_elevation = 0
        activity_count = 0
        
        for activity in activities:
            total_distance += activity.distance
            total_time += activity.moving_time
            total_elevation += activity.total_elevation_gain
            activity_count += 1
            
        return {
            'total_distance': total_distance,
            'total_time': total_time,
            'total_elevation': total_elevation,
            'activity_count': activity_count
        }

def main():
    try:
        mcp = StravaMCP()
        
        # Get athlete info
        athlete = mcp.get_athlete()
        print(f"Connected to Strava as: {athlete.firstname} {athlete.lastname}")
        
        # Get recent activities
        recent_activities = mcp.get_recent_activities(limit=5)
        print("\nRecent Activities:")
        for activity in recent_activities:
            print(f"- {activity['name']} ({activity['start_date']})")
            
        # Get weekly stats
        weekly_stats = mcp.get_weekly_stats()
        print("\nWeekly Statistics:")
        print(f"Total Distance: {weekly_stats['total_distance']/1000:.2f} km")
        print(f"Total Time: {weekly_stats['total_time']/3600:.2f} hours")
        print(f"Total Elevation: {weekly_stats['total_elevation']:.2f} m")
        print(f"Number of Activities: {weekly_stats['activity_count']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 