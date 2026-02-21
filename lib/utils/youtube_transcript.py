"""
YouTube Transcript Fetcher

Fetch transcripts from YouTube videos for learning Blender/Geometry Nodes.

SETUP OPTIONS:
==============

Option 1: youtube-transcript-api (Python library)
    pip install youtube-transcript-api

    Note: This library sometimes breaks due to YouTube API changes.
    If you get "VideoUnavailable" errors, try one of the alternatives below.

Option 2: yt-dlp (Recommended - More Reliable)
    pip install yt-dlp

    yt-dlp is actively maintained and handles YouTube changes quickly.
    You can use it to download subtitles:

    yt-dlp --write-auto-sub --sub-lang en --skip-download "https://youtube.com/watch?v=VIDEO_ID"

Option 3: Manual Download
    1. Open YouTube video in browser
    2. Click the "..." menu → "Show transcript"
    3. Copy the transcript text
    4. Save to a file

Option 4: Use transcripts/ directory
    Create a transcripts/ folder and paste tutorials there as .txt files

USAGE:
======
    from lib.utils.youtube_transcript import get_transcript, save_transcript

    # Get transcript as text
    text = get_transcript("https://www.youtube.com/watch?v=VIDEO_ID")

    # Save to file for later reference
    save_transcript("https://youtube.com/...", "transcripts/tutorial.txt")

    # Alternative: Use yt-dlp directly
    # yt-dlp --write-auto-sub --sub-lang en --skip-download "URL"
"""

from __future__ import annotations
import re
import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# Try to import transcript APIs
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False

# Check for yt-dlp
try:
    result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
    YTDLP_AVAILABLE = result.returncode == 0
except FileNotFoundError:
    YTDLP_AVAILABLE = False


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.

    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - VIDEO_ID (direct)

    Args:
        url: YouTube URL or video ID

    Returns:
        Video ID string or None if not found
    """
    # Direct video ID (11 characters, alphanumeric + - and _)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url

    # YouTube URL patterns
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_transcript_ytdlp(video_url: str, language: str = "en") -> Optional[str]:
    """
    Fetch transcript using yt-dlp (more reliable).

    Requires: pip install yt-dlp
    """
    if not YTDLP_AVAILABLE:
        return None

    video_id = extract_video_id(video_url)
    if not video_id:
        return None

    import tempfile
    import glob

    try:
        # Create temp directory for subtitle
        with tempfile.TemporaryDirectory() as tmpdir:
            # Download subtitles only
            cmd = [
                'yt-dlp',
                '--write-auto-sub',  # Get auto-generated if manual not available
                '--sub-lang', language,
                '--skip-download',   # Don't download video
                '--sub-format', 'vtt',
                '-o', f'{tmpdir}/subtitle',
                f'https://www.youtube.com/watch?v={video_id}'
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            # Find the downloaded subtitle file (yt-dlp adds language suffix)
            vtt_files = list(Path(tmpdir).glob('*.vtt'))

            if vtt_files:
                text = parse_vtt(vtt_files[0])
                return text

            return None

    except Exception as e:
        print(f"yt-dlp error: {e}")
        return None


def parse_vtt(vtt_path: Path) -> str:
    """Parse VTT subtitle file to plain text."""
    import re
    lines = []
    with open(vtt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip VTT headers, timestamps, and empty lines
            if not line:
                continue
            if line.startswith('WEBVTT'):
                continue
            if line.startswith('Kind:'):
                continue
            if line.startswith('Language:'):
                continue
            if '-->' in line:  # Timestamp line
                continue
            # Remove inline timestamp tags like <00:00:19.039><c>
            line = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', line)
            line = re.sub(r'</?c>', '', line)
            # Skip if only numbers/colons/dots
            if line.replace('.', '').replace(':', '').isdigit():
                continue
            # Skip if line is just formatting
            if not line:
                continue
            # This is actual text
            lines.append(line)

    return ' '.join(lines)


def get_transcript_api(video_url: str, language: str = "en") -> Optional[str]:
    """
    Fetch transcript using youtube-transcript-api.

    Note: This often breaks due to YouTube API changes.
    """
    if not TRANSCRIPT_API_AVAILABLE:
        return None

    video_id = extract_video_id(video_url)
    if not video_id:
        return None

    try:
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id)

        if transcript_data:
            return ' '.join(entry['text'] for entry in transcript_data)
        return None

    except Exception as e:
        print(f"Transcript API error: {e}")
        return None


def get_transcript(
    video_url: str,
    language: str = "en",
    include_timestamps: bool = False
) -> Optional[str]:
    """
    Fetch transcript from a YouTube video.

    Tries multiple methods:
    1. yt-dlp (most reliable)
    2. youtube-transcript-api

    Args:
        video_url: YouTube URL or video ID
        language: Language code (default: "en")
        include_timestamps: Whether to include timestamps in output

    Returns:
        Transcript text or None if unavailable
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from: {video_url}")

    # Try yt-dlp first (more reliable)
    if YTDLP_AVAILABLE:
        print("Trying yt-dlp...")
        transcript = get_transcript_ytdlp(video_url, language)
        if transcript:
            return transcript

    # Fall back to transcript API
    if TRANSCRIPT_API_AVAILABLE:
        print("Trying youtube-transcript-api...")
        transcript = get_transcript_api(video_url, language)
        if transcript:
            return transcript

    print("No transcript method available.")
    print("Install one of:")
    print("  pip install yt-dlp  (recommended)")
    print("  pip install youtube-transcript-api")
    return None


def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def save_transcript(
    video_url: str,
    output_path: str,
    language: str = "en",
    include_metadata: bool = True
) -> bool:
    """
    Fetch and save transcript to a file.

    Args:
        video_url: YouTube URL or video ID
        output_path: Path to save transcript
        language: Language code
        include_metadata: Add metadata header

    Returns:
        True if successful, False otherwise
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        print(f"Could not extract video ID from: {video_url}")
        return False

    transcript = get_transcript(video_url, language)
    if not transcript:
        return False

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        if include_metadata:
            f.write(f"# YouTube Transcript\n")
            f.write(f"# Video ID: {video_id}\n")
            f.write(f"# URL: https://youtube.com/watch?v={video_id}\n")
            f.write(f"# Language: {language}\n")
            f.write(f"#\n\n")

        f.write(transcript)

    print(f"Transcript saved to: {output_file}")
    return True


def get_transcript_chunks(
    video_url: str,
    chunk_size: int = 1000,
    language: str = "en"
) -> List[str]:
    """
    Get transcript split into chunks for processing.

    Useful for feeding into LLMs with context limits.

    Args:
        video_url: YouTube URL or video ID
        chunk_size: Approximate characters per chunk
        language: Language code

    Returns:
        List of transcript chunks
    """
    transcript = get_transcript(video_url, language)
    if not transcript:
        return []

    # Split on sentence boundaries when possible
    words = transcript.split()
    chunks = []
    current_chunk = []
    current_size = 0

    for word in words:
        current_chunk.append(word)
        current_size += len(word) + 1

        if current_size >= chunk_size and word.endswith(('.', '!', '?')):
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_size = 0

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


# CLI interface
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("YouTube Transcript Fetcher")
        print()
        print("Usage:")
        print("  python youtube_transcript.py <youtube_url>           # Print transcript")
        print("  python youtube_transcript.py <youtube_url> output.txt # Save to file")
        print()
        print("Setup:")
        print("  pip install yt-dlp  # Recommended")
        sys.exit(1)

    url = sys.argv[1]

    if len(sys.argv) > 2:
        save_transcript(url, sys.argv[2])
    else:
        transcript = get_transcript(url)
        if transcript:
            print(transcript)
