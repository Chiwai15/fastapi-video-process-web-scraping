from fastapi import APIRouter, Depends, HTTPException, Query, Body, File, UploadFile
from fastapi.responses import FileResponse
from typing import Dict, Optional, Tuple, List, Any
import os
from pydantic import BaseModel, Field

from core.dependencies import get_video_processor
from services.video.video_processor import VideoProcessor
from core.config import get_settings
from core.decorators import api_error_handler

router = APIRouter(tags=["Video Generation"])


class VideoGenerationParams(BaseModel):
    """Parameters for video generation."""
    text: str = Field(
        "The IFA doesn't offer separate down payment assistance (DPA) programs for first-time homebuyers, but rather, assistance in conjunction with the FirstHome and Homes for Iowans programs.",
        description="Text to display in the video"
    )
    duration: float = Field(5.0, description="Video duration in seconds", gt=0)
    text_position_x: int = Field(50, description="X coordinate of text position")
    text_position_y: int = Field(150, description="Y coordinate of text position")
    text_start: float = Field(1.0, description="Start time for text display in seconds", ge=0)
    text_end: Optional[float] = Field(5.0, description="End time for text display (default: end of video)")
    font_size: int = Field(30, description="Font size for text", gt=0)
    text_color: str = Field("white", description="Color of the text")
    
    def get_text_position(self) -> Tuple[int, int]:
        """Get text position as a tuple."""
        return (self.text_position_x, self.text_position_y)


class VideoGenerationResponse(BaseModel):
    """Response model for video generation."""
    video_url: str = Field(..., description="URL path to access the generated video")
    duration: float = Field(..., description="Duration of the video in seconds")
    file_size: int = Field(..., description="File size in bytes")


@router.post("/generate-video", response_model=VideoGenerationResponse)
@api_error_handler()
async def generate_video(
    params: VideoGenerationParams = Body(...),
    video_processor: VideoProcessor = Depends(get_video_processor)
) -> Dict[str, Any]:
    """
    Generate a video with text overlay on a background image.
    
    Creates a video of specified duration with the provided text displayed 
    from the specified start time until the end time (or video end).
    
    Returns the URL path to access the generated video.
    """
    # Generate the video - with await added
    output_filename = await video_processor.generate_video(
        text=params.text,
        duration=params.duration,
        text_position=params.get_text_position(),
        text_start=params.text_start,
        text_end=params.text_end,
        font_size=params.font_size,
        text_color=params.text_color
    )
    
    # Get full path from filename
    settings = get_settings()
    video_path = os.path.join(settings.OUTPUT_DIR, output_filename)
    
    # Get file stats
    file_size = os.path.getsize(video_path)
    
    # Return the response with video URL
    video_url = f"/videos/{output_filename}"
    
    return {
        "video_url": video_url,
        "duration": params.duration,
        "file_size": file_size
    }


@router.post("/animate-text-video", response_model=VideoGenerationResponse)
@api_error_handler()
async def animate_text_video(
    text: str = Body("The IFA doesn't offer separate down payment assistance (DPA) programs for first-time homebuyers, but rather, assistance in conjunction with the FirstHome and Homes for Iowans programs.", embed=True),
    duration: float = Query(5.0, gt=0, description="Video duration in seconds"),
    font_size: int = Query(30, gt=0, description="Font size for text"),
    text_color: str = Query("white", description="Color of the text"),
    video_processor: VideoProcessor = Depends(get_video_processor)
) -> Dict[str, Any]:
    """
    Generate a video with text animating from top-left to bottom-right.
    
    Creates a video of specified duration with the provided text animating 
    from the top-left corner to the bottom-right corner.
    
    Returns the URL path to access the generated video.
    """
    # Generate the animated video - with await added
    output_filename = await video_processor.generate_animated_text_video(
        text=text,
        duration=duration,
        font_size=font_size,
        text_color=text_color
    )
    
    # Get full path from filename
    settings = get_settings()
    video_path = os.path.join(settings.OUTPUT_DIR, output_filename)
    
    # Get file stats
    file_size = os.path.getsize(video_path)
    
    # Return the response with video URL
    video_url = f"/videos/{output_filename}"
    
    return {
        "video_url": video_url,
        "duration": duration,
        "file_size": file_size
    }


@router.get("/videos/{filename}")
@api_error_handler()
async def get_video(filename: str) -> FileResponse:
    """
    Retrieve a generated video file.
    
    Args:
        filename: Name of the video file to retrieve
        
    Returns:
        The video file as a streamable response
        
    Raises:
        HTTPException: If the video file is not found
    """
    settings = get_settings()
    video_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename
    )