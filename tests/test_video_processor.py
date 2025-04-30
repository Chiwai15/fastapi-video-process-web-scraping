import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
pytest_plugins = ("pytest_asyncio",)

from services.video.video_processor import VideoProcessor
from core.exceptions import VideoProcessingError, ValidationError

@pytest.fixture
def mock_process_pool():
    """Create a mock process pool for testing."""
    with patch('concurrent.futures.ProcessPoolExecutor') as mock:
        executor = MagicMock()
        mock.return_value = executor
        yield executor

@pytest.fixture
def video_processor(mock_process_pool):
    """Create a VideoProcessor with mocked dependencies."""
    media_paths = {
        "media_dir": "/tmp/media",
        "output_dir": "/tmp/media/output",
        "font_path": "/tmp/fonts/test.ttf",
        "default_bg": "/tmp/media/default_bg.jpg"
    }
    
    # Mock the initialize and validate methods
    with patch.object(VideoProcessor, '_initialize_directories'), \
         patch.object(VideoProcessor, '_validate_font'), \
         patch.object(VideoProcessor, '_validate_background'), \
         patch.object(VideoProcessor, '_merge_fonts'):
        processor = VideoProcessor(process_pool=mock_process_pool, media_paths=media_paths)
        yield processor

@pytest.mark.asyncio
async def test_generate_video_success(video_processor):
    """Test successful video generation with text overlay."""
    # Setup - mock the _run_in_process method
    with patch.object(video_processor, '_run_in_process', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = "/tmp/media/output/video_123abc.mp4"
        
        # Execute
        result = await video_processor.generate_video(
            text="Test text",
            duration=5.0,
            text_position=(50, 150),
            text_start=1.0,
            text_end=4.0,
            font_size=30,
            text_color="white"
        )
        
        # Verify
        assert result.startswith("video_") and result.endswith(".mp4")
        mock_run.assert_called_once()
        # Check function name and parameters
        args, kwargs = mock_run.call_args
        assert args[0] == "_create_video_with_text"
        assert kwargs["text"] == "Test text"
        assert kwargs["duration"] == 5.0
        assert kwargs["text_position"] == (50, 150)
        assert kwargs["text_start"] == 1.0
        assert kwargs["text_end"] == 4.0
        assert kwargs["font_size"] == 30
        assert kwargs["text_color"] == "white"

@pytest.mark.asyncio
async def test_generate_video_default_text_end(video_processor):
    """Test that text_end defaults to duration when not provided."""
    # Setup
    with patch.object(video_processor, '_run_in_process', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = "/tmp/media/output/video_123.mp4"
        
        # Execute - without specifying text_end
        await video_processor.generate_video(
            text="Test text",
            duration=5.0,
            text_position=(50, 150),
            text_start=1.0  # No text_end
        )
        
        # Verify text_end was set to duration
        args, kwargs = mock_run.call_args
        assert kwargs["text_end"] == 5.0  # Should equal duration

@pytest.mark.asyncio
async def test_generate_video_validation_errors(video_processor):
    """Test validation errors for invalid parameters."""

    # Test case 1: Negative duration
    with pytest.raises(VideoProcessingError) as excinfo:
        await video_processor.generate_video(
            text="Test text",
            duration=-1.0,  # Invalid
            text_position=(50, 150)
        )
    assert "Duration must be positive" in str(excinfo.value)

    # Test case 2: Invalid text_start
    with pytest.raises(VideoProcessingError) as excinfo:
        await video_processor.generate_video(
            text="Test text",
            duration=5.0,
            text_position=(50, 150),
            text_start=6.0  # Invalid - after video duration
        )
    assert "Text start time must be between" in str(excinfo.value)

    # Test case 3: Invalid text_end
    with pytest.raises(VideoProcessingError) as excinfo:
        await video_processor.generate_video(
            text="Test text",
            duration=5.0,
            text_position=(50, 150),
            text_start=2.0,
            text_end=1.0  # Invalid - before text_start
        )
    assert "Text end time must be after start time" in str(excinfo.value)

@pytest.mark.asyncio
async def test_generate_video_processing_error(video_processor):
    """Test error handling when video processing fails."""
    # Setup - mock _run_in_process to raise an exception
    with patch.object(video_processor, '_run_in_process', new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = Exception("Video processing failed")
        
        # Execute & Verify
        with pytest.raises(VideoProcessingError) as excinfo:
            await video_processor.generate_video(
                text="Test text",
                duration=5.0,
                text_position=(50, 150)
            )
        assert "Failed to generate video" in str(excinfo.value)

@pytest.mark.asyncio
async def test_generate_animated_text_video_success(video_processor):
    """Test successful animated text video generation."""
    # Setup
    with patch.object(video_processor, '_run_in_process', new_callable=AsyncMock) as mock_run:
        mock_run.return_value = f"/tmp/media/output/animated_123abc.mp4"
        
        # Execute
        result = await video_processor.generate_animated_text_video(
            text="Animated test text",
            duration=5.0,
            font_size=40,
            text_color="blue"
        )
        
        # Verify
        assert result.startswith("animated_") and result.endswith(".mp4")
        mock_run.assert_called_once()
        # Check function name and parameters
        args, kwargs = mock_run.call_args
        assert args[0] == "_create_animated_text_video"
        assert kwargs["text"] == "Animated test text"
        assert kwargs["duration"] == 5.0
        assert kwargs["font_size"] == 40
        assert kwargs["text_color"] == "blue"

@pytest.mark.asyncio
async def test_generate_animated_text_video_validation_error(video_processor):
    """Test validation error for animated text video with invalid duration."""
    with pytest.raises(VideoProcessingError) as excinfo:
        await video_processor.generate_animated_text_video(
            text="Animated test text",
            duration=0.0,  # Invalid
            font_size=40,
            text_color="blue"
        )
    assert "Duration must be positive" in str(excinfo.value)

@pytest.mark.asyncio
async def test_run_in_process(video_processor, mock_process_pool):
    """Test the _run_in_process method that handles process pool execution."""
    # Setup
    mock_loop = AsyncMock()
    mock_loop.run_in_executor.return_value = "result"
    
    # Mock asyncio.get_running_loop to return our mock loop
    with patch('asyncio.get_running_loop', return_value=mock_loop):
        # Execute
        result = await video_processor._run_in_process(
            "test_func", arg1="value1", arg2="value2"
        )
        
        # Verify
        assert result == "result"
        mock_loop.run_in_executor.assert_called_once()
        # Verify it was called with the process pool and appropriate arguments
        args, kwargs = mock_loop.run_in_executor.call_args
        assert args[0] == mock_process_pool  # First arg should be the pool
        # Check that the wrapper function was passed
        assert len(args) > 1
        # The other args should be function name and kwargs dict
        assert "test_func" in args
        assert isinstance(dict(args[-1]), dict)
        assert dict(args[-1])["arg1"] == "value1"
        assert dict(args[-1])["arg2"] == "value2"