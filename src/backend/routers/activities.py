"""
Endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional, List

from ..database import get_all_activities, get_activity, add_participant_to_activity, get_teacher

router = APIRouter(
    prefix="/activities",
    tags=["activities"]
)

@router.get("/", response_model=Dict[str, Any])
def get_activities(
    day: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all activities with their details, with optional filtering by day and time
    
    - day: Filter activities occurring on this day (e.g., 'Monday', 'Tuesday')
    - start_time: Filter activities starting at or after this time (24-hour format, e.g., '14:30')
    - end_time: Filter activities ending at or before this time (24-hour format, e.g., '17:00')
    """
    activities = get_all_activities()
    
    # Apply filters if provided
    filtered_activities = {}
    for name, activity in activities.items():
        include_activity = True
        
        # Filter by day
        if day and include_activity:
            if day not in activity.get("schedule_details", {}).get("days", []):
                include_activity = False
        
        # Filter by start time
        if start_time and include_activity:
            activity_start = activity.get("schedule_details", {}).get("start_time", "")
            if activity_start < start_time:
                include_activity = False
        
        # Filter by end time
        if end_time and include_activity:
            activity_end = activity.get("schedule_details", {}).get("end_time", "")
            if activity_end > end_time:
                include_activity = False
        
        if include_activity:
            filtered_activities[name] = activity
    
    return filtered_activities

@router.get("/days", response_model=List[str])
def get_available_days() -> List[str]:
    """Get a list of all days that have activities scheduled"""
    activities = get_all_activities()
    days_set = set()
    
    for activity in activities.values():
        schedule_days = activity.get("schedule_details", {}).get("days", [])
        days_set.update(schedule_days)
    
    return sorted(list(days_set))

@router.post("/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, teacher_username: Optional[str] = Query(None)):
    """Sign up a student for an activity - requires teacher authentication"""
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")
    
    teacher = get_teacher(teacher_username)
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    
    # Get the activity
    activity = get_activity(activity_name)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400, detail="Already signed up for this activity")

    # Add student to participants
    success = add_participant_to_activity(activity_name, email)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update activity")
    
    return {"message": f"Signed up {email} for {activity_name}"}

@router.post("/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, teacher_username: Optional[str] = Query(None)):
    """Remove a student from an activity - requires teacher authentication"""
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Authentication required for this action")
    
    teacher = get_teacher(teacher_username)
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")
    
    # Get the activity
    activity = get_activity(activity_name)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400, detail="Not registered for this activity")

    # Remove student from participants
    activity["participants"].remove(email)
    
    return {"message": f"Unregistered {email} from {activity_name}"}