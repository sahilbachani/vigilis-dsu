"""
Tasks API - monitor background scraping task progress
"""
from fastapi import APIRouter, HTTPException
from app.core.background_tasks import ScrapeTask

router = APIRouter()


@router.get("/{task_id}/status")
def get_task_status(task_id: str):
    """
    Get status of a background scraping task
    Returns progress: 0-100%, status, message, posts found/saved
    """
    task = ScrapeTask.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "success": True,
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "message": task.message,
        "posts_found": task.posts_found,
        "posts_saved": task.posts_saved,
        "error": task.error
    }
