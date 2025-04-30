import logging
import os
import uuid
import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, Optional, Tuple, Any, Callable

from moviepy.editor import (
    TextClip, ImageClip, CompositeVideoClip, 
    VideoFileClip
)
from PIL import Image, ImageFont

from core.decorators import error_handler, timing_decorator
from core.exceptions import VideoProcessingError, ValidationError
from utils.font_fallback import merge_missing_glyphs

logger = logging.getLogger(__name__)


# This is a module-level function that will be called by the process pool
# It needs to be defined at the module level to be picklable
def _process_func_wrapper(func_name, kwargs_dict):
    """
    A wrapper to call the appropriate processing function by name.
    
    Args:
        func_name: Name of the function to call
        kwargs_dict: Dictionary of keyword arguments to pass to the function
        
    Returns:
        Result of calling the function
    """
    if func_name == "_create_video_with_text":
        return VideoProcessor._create_video_with_text(**kwargs_dict)
    elif func_name == "_create_animated_text_video":
        return VideoProcessor._create_animated_text_video(**kwargs_dict)
    elif func_name == "_add_text_to_video":
        return VideoProcessor._add_text_to_video(**kwargs_dict)
    elif func_name == "_test_font_in_process":
        return VideoProcessor._test_font_in_process(**kwargs_dict)
    else:
        raise ValueError(f"Unknown function name: {func_name}")

class VideoProcessor:
    """Async service for video generation and processing."""
    
    def __init__(
        self, 
        process_pool: ProcessPoolExecutor,
        media_paths: Dict[str, str],
    ):
        """
        Initialize video processor.
        
        Args:
            process_pool: Process pool for parallel video processing
            media_paths: Dict with paths for media files
        """
        self.process_pool = process_pool
        self.media_dir = media_paths.get("media_dir", "media")
        self.output_dir = media_paths.get("output_dir", "media/output")
        self.font_path = media_paths.get("font_path", "/usr/share/fonts/truetype/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCu173w0aXp-p7K4KLjztg.ttf")
        self.default_bg = media_paths.get("default_bg")
        from moviepy.config import change_settings
        change_settings({"FFMPEG_THREADS": 2})  # Limit FFMPEG threads per process
        
        # Ensure directories exist
        self._initialize_directories()
        
        # Validate font file
        self._validate_font()

        # Merge fonts if necessary
        self._merge_fonts()
        
        # Validate or create default background
        self._validate_background()
        
        logger.info(
            f"VideoProcessor initialized with: "
            f"media_dir={self.media_dir}, "
            f"output_dir={self.output_dir}, "
            f"font_path={self.font_path}"
        )
    

    def _initialize_directories(self) -> None:
        """Ensure all required directories exist."""
        os.makedirs(self.media_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Also ensure font directory exists
        if self.font_path:
            font_dir = os.path.dirname(self.font_path)
            os.makedirs(font_dir, exist_ok=True)

    def _validate_font(self) -> None:
        """Validate that the font file exists."""
        from core import moviepy_config
        if not moviepy_config.check_font_availability(self.font_path):
            raise VideoProcessingError(f"Default Font not found: {self.font_path}")


    def _merge_fonts(self) -> str:   
        """Merge font files if necessary."""
        merged_font_path = self.font_path + "merged-font.ttf"
        if not os.path.exists(merged_font_path):
            find_fallback_font = "/usr/share/fonts/truetype/Poppins-Black.ttf"
            logger.info(f"Merging fonts: {self.font_path} and {find_fallback_font}")
            merge_missing_glyphs(self.font_path, find_fallback_font, merged_font_path)
        self.font_path = merged_font_path
    
    def _validate_background(self, width: int = 1920, height: int = 1080) -> None:
        """Validate or create the default background image."""
        if not self.default_bg or not os.path.exists(self.default_bg):
            # If the default background doesn't exist, create it
            logger.info(f"Default background not found at {self.default_bg}, creating...")
            self._create_default_bg(width, height)
            
    def _create_default_bg(self, width: int = 1920, height: int = 1080) -> None:
        """Create a default background image if none exists."""
        try:
            img = Image.new('RGB', (width, height), color=(25, 55, 109))
            
            # Ensure the directory exists
            if self.default_bg:
                os.makedirs(os.path.dirname(self.default_bg), exist_ok=True)
                img.save(self.default_bg)
                logger.info(f"Created default background image at {self.default_bg}")
            else:
                # Create a default location if none provided
                self.default_bg = os.path.join(self.media_dir, "default_bg.jpg")
                os.makedirs(os.path.dirname(self.default_bg), exist_ok=True)
                img.save(self.default_bg)
                logger.info(f"Created default background at {self.default_bg}")
        except Exception as e:
            logger.error(f"Failed to create default background: {str(e)}")
            raise VideoProcessingError(f"Failed to create default background: {str(e)}")
    
    async def _run_in_process(self, func_name, **kwargs):
        """
        Run a function in the process pool asynchronously.
        
        Args:
            func_name: Name of the function to run
            **kwargs: Arguments to the function
            
        Returns:
            The result of the function
        """
        loop = asyncio.get_running_loop()
        # Package the kwargs into a dict that we'll pass as a single argument
        return await loop.run_in_executor(
            self.process_pool,
            _process_func_wrapper,  # Call the module-level wrapper
            func_name,              
            kwargs                  
        )
    
    # ************** Feature 1 Generate a video with text overlay. **************
    @error_handler(default_error=VideoProcessingError)
    @timing_decorator()
    async def generate_video(
        self,
        text: str,
        duration: float = 5.0,
        text_position: Tuple[int, int] = (50, 150),
        text_start: float = 1.0,
        text_end: Optional[float] = None,
        background_image: Optional[str] = None,
        font_size: int = 30,
        text_color: str = "white"
    ) -> str:
        """
        Generate a video with text overlay asynchronously.
        
        Args:
            text: Text to display
            duration: Video duration in seconds
            text_position: (x, y) position of the text
            text_start: Start time for text display in seconds
            text_end: End time for text display (default: end of video)
            background_image: Path to background image (default: use default bg)
            font_size: Font size for text
            text_color: Color of the text
            
        Returns:
            Path to the generated video file
            
        Raises:
            VideoProcessingError: If video generation fails
        """
        # Parameter validation
        if duration <= 0:
            raise ValidationError("Duration must be positive")
        
        if text_start < 0 or text_start >= duration:
            raise ValidationError("Text start time must be between 0 and video duration")
        
        if text_end is not None and (text_end <= text_start or text_end > duration):
            raise ValidationError("Text end time must be after start time and within video duration")
        
        # Default text end time to video duration if not specified
        if text_end is None:
            text_end = duration
        
        # Use default background if none provided
        bg_path = background_image if background_image and os.path.exists(background_image) else self.default_bg
        
        # Create output filename
        output_filename = f"video_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Submit video creation task to process pool using async wrapper
        try:
            output_path = await self._run_in_process(
                "_create_video_with_text",
                bg_path=bg_path,
                text=text,
                output_path=output_path,
                duration=duration,
                text_position=text_position,
                text_start=text_start,
                text_end=text_end,
                font_path=self.font_path,
                font_size=font_size,
                text_color=text_color
            )
            logger.info(f"Video generation completed: {output_path}")
            return output_filename  # Return just the filename for URL construction
        except Exception as e:
            logger.error(f"Video generation failed: {str(e)}")
            raise VideoProcessingError(f"Failed to generate video: {str(e)}")
    
    @staticmethod
    def _create_video_with_text(
        bg_path: str,
        text: str,
        output_path: str,
        duration: float,
        text_position: Tuple[int, int],
        text_start: float,
        text_end: float,
        font_path: str,
        font_size: int,
        text_color: str
    ) -> str:
        """
        Create a video with text overlay (runs in a separate process).
        
        Args:
            bg_path: Path to background image
            text: Text to display
            output_path: Where to save the video
            duration: Video duration in seconds
            text_position: (x, y) position of text
            text_start: When to start showing text (seconds)
            text_end: When to stop showing text (seconds)
            font_path: Path to font file
            font_size: Font size
            text_color: Text color
            
        Returns:
            Path to the generated video file
        """

        try:
            # Validate background image
            if not os.path.exists(bg_path):
                raise VideoProcessingError(f"Background image not found at {bg_path}")
            
            # Create background clip from image
            try:
                bg_clip = ImageClip(bg_path).set_duration(duration)
            except Exception as e:
                raise VideoProcessingError(f"Failed to load background image: {str(e)}")
                        
            # Create text clip
            try:
                text_clip = TextClip(
                    text,
                    fontsize=font_size,
                    color=text_color,
                    font=font_path,
                    method="caption",
                    size=(1600, None), 
                    align="West"  
                )
            except Exception as e:
                # Close previously created clips
                if 'bg_clip' in locals():
                    bg_clip.close()
                raise VideoProcessingError(f"Failed to create text clip: {str(e)}")
                    
            # Set text position and timing
            text_clip = text_clip.set_position(text_position).set_start(text_start).set_end(text_end)
            
            # Combine clips
            try:
                video = CompositeVideoClip([bg_clip, text_clip])
            except Exception as e:
                # Close previously created clips
                if 'bg_clip' in locals():
                    bg_clip.close()
                if 'text_clip' in locals():
                    text_clip.close()
                raise VideoProcessingError(f"Failed to combine clips: {str(e)}")
            
            # Write to file
            try:
                video.write_videofile(
                    output_path,
                    fps=24,
                    codec='libx264',
                    audio=False,
                    preset='medium',
                    threads=2  # Use limited threads within each process
                )
            except Exception as e:
                # Close all clips
                if 'bg_clip' in locals():
                    bg_clip.close()
                if 'text_clip' in locals():
                    text_clip.close()
                if 'video' in locals():
                    video.close()
                raise VideoProcessingError(f"Failed to write video file: {str(e)}")
            
            # Close clips to prevent memory leaks
            bg_clip.close()
            text_clip.close()
            video.close()
            
            # Verify the output file exists and is a valid size
            if not os.path.exists(output_path):
                raise VideoProcessingError(f"Output file was not created at {output_path}")
            
            file_size = os.path.getsize(output_path)
            if file_size < 1000:  # Less than 1KB is probably an error
                raise VideoProcessingError(f"Output file is too small ({file_size} bytes)")
            
            return output_path
        
        except VideoProcessingError:
            # Re-raise VideoProcessingError directly
            raise
        except Exception as e:
            raise VideoProcessingError(f"Unexpected error in video processing: {str(e)}")
    
    # ************** Feature 2: Generate a video with animated text overlay. **************
    @error_handler(default_error=VideoProcessingError)
    @timing_decorator()
    async def generate_animated_text_video(
        self,
        text: str,
        duration: float = 5.0,
        background_image: Optional[str] = None,
        font_size: int = 30,
        text_color: str = "white"
    ) -> str:
        """
        Generate a video with text animating from top-left to bottom-right asynchronously.
        
        Args:
            text: Text to display
            duration: Video duration in seconds
            background_image: Path to background image (default: use default bg)
            font_size: Font size for text
            text_color: Color of the text
            
        Returns:
            Path to the generated video file (filename only)
            
        Raises:
            VideoProcessingError: If video generation fails
        """
        # Parameter validation
        if duration <= 0:
            raise ValidationError("Duration must be positive")
        
        # Use default background if none provided
        bg_path = background_image if background_image and os.path.exists(background_image) else self.default_bg
        
        # Create output filename
        output_filename = f"animated_{uuid.uuid4().hex}.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Submit video creation task to process pool using async wrapper
        try:
            await self._run_in_process(
                "_create_animated_text_video",
                bg_path=bg_path,
                text=text,
                output_path=output_path,
                duration=duration,
                font_path=self.font_path,
                font_size=font_size,
                text_color=text_color
            )
            logger.info(f"Animated video generation completed: {output_path}")
            return output_filename
        except Exception as e:
            logger.error(f"Animated video generation failed: {str(e)}")
            raise VideoProcessingError(f"Failed to generate animated video: {str(e)}")

    @staticmethod
    def _create_animated_text_video(
        bg_path: str,
        text: str,
        output_path: str,
        duration: float,
        font_path: str,  # Changed to match what's passed from generate_animated_text_video
        font_size: int,
        text_color: str
    ) -> str:
        """
        Create a video with text animating from top-left to bottom-right.
        
        Args:
            bg_path: Path to background image
            text: Text to display
            output_path: Where to save the video
            duration: Video duration in seconds
            font: Font name or path
            font_size: Font size
            text_color: Text color
            
        Returns:
            Path to the generated video file
        """
        bg_clip = None
        text_clip = None
        video = None
        
        try:
            # Validate background image
            if not os.path.exists(bg_path):
                raise VideoProcessingError(f"Background image not found at {bg_path}")
            
            # Create background clip from image
            bg_clip = ImageClip(bg_path).set_duration(duration)
            
            # Get background dimensions
            bg_width, bg_height = bg_clip.size
            
            # Create text clip - use font directly, don't try to validate a font path
            wrap_width = int(bg_width * 0.6)
            text_clip = TextClip(
                text,
                fontsize=font_size,
                color=text_color,
                font=font_path,  # Use the font name directly
                method="caption",
                size=(wrap_width, None),
                align="West"
            )
            
            
            # Define animation function for text position
            def text_position(t):
                progress = t / duration
                x = (bg_width - wrap_width) * progress
                y = (bg_height - text_clip.h) * progress
                return (x, y)
            
            # Set text position to be animated and timing to full duration
            text_clip = text_clip.set_position(text_position).set_duration(duration)
            
            # Combine clips
            video = CompositeVideoClip([bg_clip, text_clip])
            
            # Write to file
            video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio=False,
                preset='medium',
                threads=2  # Use limited threads within each process
            )
            
            # Verify the output file exists and is a valid size
            if not os.path.exists(output_path):
                raise VideoProcessingError(f"Output file was not created at {output_path}")
            
            file_size = os.path.getsize(output_path)
            if file_size < 1000:  # Less than 1KB is probably an error
                raise VideoProcessingError(f"Output file is too small ({file_size} bytes)")
            
            return output_path
        
        except VideoProcessingError:
            # Re-raise VideoProcessingError directly
            raise
        except Exception as e:
            raise VideoProcessingError(f"Unexpected error in animated video processing: {str(e)}")
        
        finally:
            # Close clips to prevent memory leaks
            if bg_clip:
                try:
                    bg_clip.close()
                except:
                    pass
                
            if text_clip:
                try:
                    text_clip.close()
                except:
                    pass
                
            if video:
                try:
                    video.close()
                except:
                    pass

   