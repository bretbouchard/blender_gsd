"""
Footage Module - Video Format Import and Metadata Extraction

Handles import of various video formats (MOV, MP4, MXF, AVI, image sequences)
with automatic metadata extraction and frame rate detection.

Uses Blender API guards for testing outside Blender environment.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import os
import re
import struct

# Blender API guard
try:
    import bpy
    from bpy.types import MovieClip
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    MovieClip = None

from .types import FootageInfo


# Supported video formats
SUPPORTED_VIDEO_FORMATS = {
    # Container formats
    ".mov": {"name": "QuickTime", "codec_support": ["ProRes", "H.264", "DNxHD", "Animation"]},
    ".mp4": {"name": "MP4", "codec_support": ["H.264", "H.265", "ProRes"]},
    ".mxf": {"name": "MXF", "codec_support": ["DNxHD", "DNxHR", "XAVC", "ProRes"]},
    ".avi": {"name": "AVI", "codec_support": ["Uncompressed", "DNxHD", "Cineform"]},
    ".mkv": {"name": "Matroska", "codec_support": ["H.264", "H.265", "ProRes"]},
    ".webm": {"name": "WebM", "codec_support": ["VP8", "VP9", "AV1"]},
    ".m4v": {"name": "M4V", "codec_support": ["H.264", "H.265"]},

    # Image sequences (single frame extensions)
    ".exr": {"name": "OpenEXR", "is_sequence": True},
    ".dpx": {"name": "DPX", "is_sequence": True},
    ".tiff": {"name": "TIFF", "is_sequence": True},
    ".tif": {"name": "TIFF", "is_sequence": True},
    ".png": {"name": "PNG", "is_sequence": True},
    ".jpg": {"name": "JPEG", "is_sequence": True},
    ".jpeg": {"name": "JPEG", "is_sequence": True},
    ".tga": {"name": "Targa", "is_sequence": True},
    ".bmp": {"name": "Bitmap", "is_sequence": True},
}

# Common frame rates
FRAME_RATES = {
    "23.976": 23.976,  # 23.98fps (1080p/24)
    "24": 24.0,
    "25": 25.0,  # PAL
    "29.97": 29.97,  # NTSC
    "30": 30.0,
    "47.952": 47.952,  # 48fps HFR
    "48": 48.0,
    "50": 50.0,  # PAL 50fps
    "59.94": 59.94,  # NTSC 60fps
    "60": 60.0,
    "120": 120.0,
    "240": 240.0,
}


@dataclass
class ImageSequenceInfo:
    """
    Information about an image sequence.

    Attributes:
        pattern: File pattern (e.g., "frame_####.exr")
        start_frame: First frame number
        end_frame: Last frame number
        frame_step: Frame step (usually 1)
        padding: Number of digits in frame number
        missing_frames: List of missing frame numbers
    """
    pattern: str = ""
    start_frame: int = 1
    end_frame: int = 1
    frame_step: int = 1
    padding: int = 4
    missing_frames: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern": self.pattern,
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "frame_step": self.frame_step,
            "padding": self.padding,
            "missing_frames": self.missing_frames,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ImageSequenceInfo:
        return cls(
            pattern=data.get("pattern", ""),
            start_frame=data.get("start_frame", 1),
            end_frame=data.get("end_frame", 1),
            frame_step=data.get("frame_step", 1),
            padding=data.get("padding", 4),
            missing_frames=data.get("missing_frames", []),
        )


@dataclass
class VideoMetadata:
    """
    Detailed video metadata extracted from file.

    Attributes:
        duration_seconds: Duration in seconds
        frame_count: Total number of frames
        fps: Frames per second
        width: Frame width in pixels
        height: Frame height in pixels
        pixel_aspect_ratio: Pixel aspect ratio
        codec: Video codec name
        codec_profile: Codec profile
        bitrate: Bitrate in kbps
        colorspace: Color space information
        bit_depth: Bits per channel
        has_alpha: Has alpha channel
        interlaced: Is interlaced
        field_order: Field order for interlaced
        timecode_start: Starting timecode
    """
    duration_seconds: float = 0.0
    frame_count: int = 0
    fps: float = 24.0
    width: int = 1920
    height: int = 1080
    pixel_aspect_ratio: float = 1.0
    codec: str = ""
    codec_profile: str = ""
    bitrate: int = 0
    colorspace: str = ""
    bit_depth: int = 8
    has_alpha: bool = False
    interlaced: bool = False
    field_order: str = "progressive"
    timecode_start: str = "00:00:00:00"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration_seconds": self.duration_seconds,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "pixel_aspect_ratio": self.pixel_aspect_ratio,
            "codec": self.codec,
            "codec_profile": self.codec_profile,
            "bitrate": self.bitrate,
            "colorspace": self.colorspace,
            "bit_depth": self.bit_depth,
            "has_alpha": self.has_alpha,
            "interlaced": self.interlaced,
            "field_order": self.field_order,
            "timecode_start": self.timecode_start,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VideoMetadata:
        return cls(
            duration_seconds=data.get("duration_seconds", 0.0),
            frame_count=data.get("frame_count", 0),
            fps=data.get("fps", 24.0),
            width=data.get("width", 1920),
            height=data.get("height", 1080),
            pixel_aspect_ratio=data.get("pixel_aspect_ratio", 1.0),
            codec=data.get("codec", ""),
            codec_profile=data.get("codec_profile", ""),
            bitrate=data.get("bitrate", 0),
            colorspace=data.get("colorspace", ""),
            bit_depth=data.get("bit_depth", 8),
            has_alpha=data.get("has_alpha", False),
            interlaced=data.get("interlaced", False),
            field_order=data.get("field_order", "progressive"),
            timecode_start=data.get("timecode_start", "00:00:00:00"),
        )


class FootageImporter:
    """
    Video footage importer supporting multiple formats.

    Provides format detection, metadata extraction, and image sequence
    handling for motion tracking workflows.
    """

    def __init__(self):
        """Initialize footage importer."""
        pass

    def import_footage(
        self,
        source_path: str,
        detect_fps: bool = True,
        extract_metadata: bool = True,
    ) -> FootageInfo:
        """
        Import footage from file or image sequence.

        Args:
            source_path: Path to video file or first frame of sequence
            detect_fps: Automatically detect frame rate
            extract_metadata: Extract detailed metadata

        Returns:
            FootageInfo with extracted information
        """
        path = Path(source_path)

        if not path.exists():
            # Check if it's a pattern
            if "#" in source_path or "%" in source_path:
                return self._import_sequence_pattern(source_path)
            raise FileNotFoundError(f"Footage not found: {source_path}")

        ext = path.suffix.lower()

        if ext in SUPPORTED_VIDEO_FORMATS:
            format_info = SUPPORTED_VIDEO_FORMATS[ext]

            if format_info.get("is_sequence"):
                return self._import_image_sequence(path)
            else:
                return self._import_video_file(path, detect_fps, extract_metadata)
        else:
            raise ValueError(f"Unsupported format: {ext}")

    def _import_video_file(
        self,
        path: Path,
        detect_fps: bool,
        extract_metadata: bool,
    ) -> FootageInfo:
        """Import a video file."""
        if HAS_BLENDER:
            return self._import_via_blender(path)
        else:
            return self._import_fallback(path)

    def _import_via_blender(self, path: Path) -> FootageInfo:
        """Import video using Blender's MovieClip."""
        # Try to find existing clip or create new
        clip_name = path.name

        if clip_name in bpy.data.movieclips:
            clip = bpy.data.movieclips[clip_name]
        else:
            clip = bpy.data.movieclips.load(str(path.absolute()))

        # Extract metadata from clip
        return FootageInfo(
            source_path=str(path.absolute()),
            width=clip.size[0],
            height=clip.size[1],
            frame_start=clip.frame_offset + 1,
            frame_end=clip.frame_offset + clip.frame_duration,
            fps=clip.fps,
            duration_seconds=clip.frame_duration / clip.fps if clip.fps > 0 else 0,
            colorspace=clip.colorspace_settings.name,
            has_alpha=False,  # Video clips typically don't have alpha in Blender
            is_sequence=False,
        )

    def _import_fallback(self, path: Path) -> FootageInfo:
        """Fallback import for testing outside Blender."""
        # Parse basic info from filename and mock data
        filename = path.name

        # Try to detect common resolutions from filename patterns
        width, height = 1920, 1080  # Default

        if "4K" in filename or "4096" in filename:
            width, height = 4096, 2160
        elif "UHD" in filename or "3840" in filename:
            width, height = 3840, 2160
        elif "2K" in filename or "2048" in filename:
            width, height = 2048, 1080
        elif "HD" in filename or "1920" in filename:
            width, height = 1920, 1080
        elif "720" in filename:
            width, height = 1280, 720

        # Try to detect FPS from filename
        fps = 24.0  # Default
        for fps_str, fps_val in FRAME_RATES.items():
            if fps_str in filename:
                fps = fps_val
                break

        return FootageInfo(
            source_path=str(path.absolute()),
            width=width,
            height=height,
            frame_start=1,
            frame_end=120,  # Default duration
            fps=fps,
            duration_seconds=120.0 / fps,
            colorspace="sRGB",
            codec=path.suffix[1:].upper(),
            has_alpha=False,
            is_sequence=False,
        )

    def _import_image_sequence(self, first_frame: Path) -> FootageInfo:
        """Import an image sequence."""
        # Detect sequence pattern
        seq_info = self._detect_sequence_pattern(first_frame)

        # Get dimensions from first frame
        width, height = self._get_image_dimensions(first_frame)

        return FootageInfo(
            source_path=str(first_frame.parent),
            width=width,
            height=height,
            frame_start=seq_info.start_frame,
            frame_end=seq_info.end_frame,
            fps=24.0,  # Default for sequences
            duration_seconds=(seq_info.end_frame - seq_info.start_frame + 1) / 24.0,
            colorspace=self._detect_colorspace(first_frame),
            codec=first_frame.suffix[1:].upper(),
            has_alpha=self._check_alpha(first_frame),
            is_sequence=True,
        )

    def _import_sequence_pattern(self, pattern: str) -> FootageInfo:
        """Import from a sequence pattern like 'frame_####.exr'."""
        # Convert pattern to glob
        glob_pattern = pattern.replace("#", "?")
        if "%" in pattern:
            # Handle printf-style patterns
            glob_pattern = re.sub(r'%\d*d', '*', pattern)

        parent = Path(pattern).parent
        if not parent.exists():
            parent = Path(".")

        # Find matching files
        matches = sorted(parent.glob(Path(glob_pattern).name))

        if not matches:
            raise FileNotFoundError(f"No files matching pattern: {pattern}")

        # Get frame range
        seq_info = self._detect_sequence_pattern(matches[0])
        width, height = self._get_image_dimensions(matches[0])

        return FootageInfo(
            source_path=pattern,
            width=width,
            height=height,
            frame_start=seq_info.start_frame,
            frame_end=seq_info.end_frame,
            fps=24.0,
            duration_seconds=(seq_info.end_frame - seq_info.start_frame + 1) / 24.0,
            is_sequence=True,
        )

    def _detect_sequence_pattern(self, filepath: Path) -> ImageSequenceInfo:
        """Detect image sequence pattern from a file."""
        filename = filepath.name

        # Common patterns: frame_0001.exr, shot.1001.dpx, img_001.png
        patterns = [
            r'^(.+?)[._-]?(\d{4,})(\.[^.]+)$',  # frame_0001.exr or shot.1001.dpx
            r'^(.+?)(\d{2,})(\.[^.]+)$',  # img_001.png
        ]

        for pattern in patterns:
            match = re.match(pattern, filename)
            if match:
                prefix = match.group(1)
                frame_num = int(match.group(2))
                ext = match.group(3)
                padding = len(match.group(2))

                # Find all files in sequence
                parent = filepath.parent
                frame_numbers = []

                for f in parent.iterdir():
                    m = re.match(
                        re.escape(prefix) + r'[._-]?(\d{' + str(padding) + r',})' + re.escape(ext),
                        f.name
                    )
                    if m:
                        frame_numbers.append(int(m.group(1)))

                frame_numbers.sort()

                # Find missing frames
                missing = []
                if frame_numbers:
                    expected = set(range(min(frame_numbers), max(frame_numbers) + 1))
                    actual = set(frame_numbers)
                    missing = sorted(expected - actual)

                # Create pattern
                hash_pattern = "#" * padding
                pattern_str = f"{prefix}{hash_pattern}{ext}"

                return ImageSequenceInfo(
                    pattern=pattern_str,
                    start_frame=min(frame_numbers) if frame_numbers else frame_num,
                    end_frame=max(frame_numbers) if frame_numbers else frame_num,
                    padding=padding,
                    missing_frames=missing,
                )

        # Single file, not a sequence
        return ImageSequenceInfo(
            pattern=filename,
            start_frame=1,
            end_frame=1,
        )

    def _get_image_dimensions(self, filepath: Path) -> Tuple[int, int]:
        """Get image dimensions from file header."""
        try:
            ext = filepath.suffix.lower()

            if ext in [".exr"]:
                return self._get_exr_dimensions(filepath)
            elif ext in [".dpx"]:
                return self._get_dpx_dimensions(filepath)
            elif ext in [".png"]:
                return self._get_png_dimensions(filepath)
            elif ext in [".jpg", ".jpeg"]:
                return self._get_jpeg_dimensions(filepath)
            elif ext in [".tiff", ".tif"]:
                return self._get_tiff_dimensions(filepath)
            else:
                # Default dimensions
                return 1920, 1080

        except Exception:
            return 1920, 1080

    def _get_exr_dimensions(self, filepath: Path) -> Tuple[int, int]:
        """Read EXR header for dimensions."""
        try:
            with open(filepath, "rb") as f:
                # EXR magic number
                magic = f.read(4)
                if magic != b'\x76\x2f\x31\x01':
                    return 1920, 1080

                # Version field
                version = struct.unpack('<I', f.read(4))[0]

                # Read attributes until end-of-header
                while True:
                    name_len = struct.unpack('<B', f.read(1))[0]
                    if name_len == 0:
                        break
                    name = f.read(name_len)[:-1].decode('ascii')

                    type_len = struct.unpack('<B', f.read(1))[0]
                    type_name = f.read(type_len)[:-1].decode('ascii')

                    size = struct.unpack('<I', f.read(4))[0]
                    value = f.read(size)

                    if name == "dataWindow":
                        xMin, yMin, xMax, yMax = struct.unpack('<iiii', value)
                        return xMax - xMin + 1, yMax - yMin + 1

        except Exception:
            pass
        return 1920, 1080

    def _get_png_dimensions(self, filepath: Path) -> Tuple[int, int]:
        """Read PNG header for dimensions."""
        try:
            with open(filepath, "rb") as f:
                # PNG signature
                sig = f.read(8)
                if sig != b'\x89PNG\r\n\x1a\n':
                    return 1920, 1080

                # IHDR chunk
                length = struct.unpack('>I', f.read(4))[0]
                chunk_type = f.read(4)
                if chunk_type != b'IHDR':
                    return 1920, 1080

                width, height = struct.unpack('>II', f.read(8))
                return width, height

        except Exception:
            pass
        return 1920, 1080

    def _get_jpeg_dimensions(self, filepath: Path) -> Tuple[int, int]:
        """Read JPEG header for dimensions."""
        try:
            with open(filepath, "rb") as f:
                # JPEG SOI marker
                if f.read(2) != b'\xff\xd8':
                    return 1920, 1080

                while True:
                    marker = f.read(2)
                    if not marker or len(marker) < 2:
                        break

                    if marker[0] != 0xFF:
                        break

                    if marker[1] in [0xC0, 0xC2]:  # SOF markers
                        f.read(3)  # Skip length and precision
                        height, width = struct.unpack('>HH', f.read(4))
                        return width, height
                    elif marker[1] == 0xDA:  # SOS - start of scan
                        break
                    else:
                        # Skip this segment
                        length = struct.unpack('>H', f.read(2))[0]
                        f.read(length - 2)

        except Exception:
            pass
        return 1920, 1080

    def _get_dpx_dimensions(self, filepath: Path) -> Tuple[int, int]:
        """Read DPX header for dimensions."""
        try:
            with open(filepath, "rb") as f:
                # DPX magic (big or little endian)
                magic = f.read(4)
                if magic not in [b'SDPX', b'XPDS']:
                    return 1920, 1080

                # Width and height at offset 772 (big endian) or 776 (little)
                f.seek(772)
                width = struct.unpack('>I', f.read(4))[0]
                height = struct.unpack('>I', f.read(4))[0]
                return width, height

        except Exception:
            pass
        return 1920, 1080

    def _get_tiff_dimensions(self, filepath: Path) -> Tuple[int, int]:
        """Read TIFF header for dimensions."""
        # TIFF is complex - use default for now
        return 1920, 1080

    def _detect_colorspace(self, filepath: Path) -> str:
        """Detect colorspace from file."""
        ext = filepath.suffix.lower()

        if ext == ".exr":
            return "ACEScg"  # EXR is typically linear
        elif ext == ".dpx":
            return "Linear"  # DPX is typically log or linear
        else:
            return "sRGB"

    def _check_alpha(self, filepath: Path) -> bool:
        """Check if image has alpha channel."""
        ext = filepath.suffix.lower()

        if ext in [".png", ".exr", ".tiff", ".tif"]:
            return True  # These formats commonly have alpha
        return False

    def get_metadata(self, source_path: str) -> VideoMetadata:
        """
        Extract detailed metadata from video file.

        Args:
            source_path: Path to video file

        Returns:
            VideoMetadata with extracted information
        """
        # Try ffprobe if available
        metadata = self._extract_metadata_ffprobe(source_path)

        if not metadata:
            # Fallback to basic info
            info = self.import_footage(source_path)
            metadata = VideoMetadata(
                width=info.width,
                height=info.height,
                fps=info.fps,
                duration_seconds=info.duration_seconds,
                frame_count=int(info.duration_seconds * info.fps) if info.fps > 0 else 0,
                codec=info.codec,
                colorspace=info.colorspace,
                has_alpha=info.has_alpha,
            )

        return metadata

    def _extract_metadata_ffprobe(self, source_path: str) -> Optional[VideoMetadata]:
        """Extract metadata using ffprobe if available."""
        try:
            import subprocess
            import json as json_module

            # Try to run ffprobe
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    source_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return None

            data = json_module.loads(result.stdout)

            # Find video stream
            video_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break

            if not video_stream:
                return None

            format_info = data.get("format", {})

            # Parse frame rate (can be "24/1" or "23.976")
            fps_str = video_stream.get("r_frame_rate", "24/1")
            if "/" in fps_str:
                num, den = fps_str.split("/")
                fps = float(num) / float(den) if float(den) > 0 else 24.0
            else:
                fps = float(fps_str)

            duration = float(format_info.get("duration", 0))

            return VideoMetadata(
                duration_seconds=duration,
                frame_count=int(video_stream.get("nb_frames", duration * fps)),
                fps=fps,
                width=int(video_stream.get("width", 1920)),
                height=int(video_stream.get("height", 1080)),
                pixel_aspect_ratio=1.0,  # Would need display_aspect_ratio
                codec=video_stream.get("codec_name", ""),
                codec_profile=video_stream.get("profile", ""),
                bitrate=int(format_info.get("bit_rate", 0)) // 1000,
                colorspace=video_stream.get("color_space", ""),
                bit_depth=int(video_stream.get("bits_per_raw_sample", 8)),
                has_alpha=video_stream.get("pix_fmt", "").endswith("a"),
                interlaced=video_stream.get("field_order", "progressive") != "progressive",
                field_order=video_stream.get("field_order", "progressive"),
            )

        except Exception:
            return None


def is_supported_format(filepath: str) -> bool:
    """Check if file format is supported."""
    ext = Path(filepath).suffix.lower()
    return ext in SUPPORTED_VIDEO_FORMATS


def get_format_info(filepath: str) -> Optional[Dict[str, Any]]:
    """Get format information for a file."""
    ext = Path(filepath).suffix.lower()
    return SUPPORTED_VIDEO_FORMATS.get(ext)


# ============================================================================
# FootageMetadata-based API (Plan 07.0-03)
# ============================================================================

# Import FootageMetadata from types
from .types import FootageMetadata


def get_frame_rate(stream: dict) -> float:
    """
    Parse frame rate from ffprobe stream data.

    Handles rational format like "30000/1001" -> 29.97
    Returns 24.0 as default if parsing fails.

    Args:
        stream: ffprobe stream dictionary with r_frame_rate field

    Returns:
        Frame rate as float
    """
    fps_str = stream.get('r_frame_rate', '24/1')
    try:
        if '/' in fps_str:
            num, den = fps_str.split('/')
            den_val = float(den)
            if den_val > 0:
                return float(num) / den_val
        return float(fps_str)
    except (ValueError, ZeroDivisionError):
        return 24.0


def extract_metadata(video_path: str) -> FootageMetadata:
    """
    Extract video metadata using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        FootageMetadata with extracted information

    Raises:
        RuntimeError: If ffprobe fails or is not available
        FileNotFoundError: If video file doesn't exist
    """
    import subprocess
    import json

    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cmd = [
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format', '-show_streams',
        str(path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        raise RuntimeError("ffprobe not found. Please install ffmpeg.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("ffprobe timed out")

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    data = json.loads(result.stdout)
    metadata = FootageMetadata(filename=path.name)

    # Extract video stream info
    for stream in data.get('streams', []):
        if stream.get('codec_type') == 'video':
            metadata.resolution = (
                stream.get('width', 1920),
                stream.get('height', 1080)
            )
            metadata.codec = stream.get('codec_name', '')
            metadata.frame_rate = get_frame_rate(stream)

            # Extract bit depth if available
            bits = stream.get('bits_per_raw_component', 8)
            metadata.bit_depth = bits if bits else 8

            # Color space
            metadata.color_space = stream.get('color_space', '')
            break

    # Extract format info
    fmt = data.get('format', {})
    if 'duration' in fmt:
        metadata.duration_seconds = float(fmt['duration'])
        metadata.duration_frames = int(metadata.duration_seconds * metadata.frame_rate)

    return metadata


def analyze_footage(video_path: str) -> Dict[str, Any]:
    """
    Comprehensive footage analysis including metadata and content hints.

    Args:
        video_path: Path to video file

    Returns:
        Dict with metadata and analysis results
    """
    metadata = extract_metadata(video_path)

    # Content analysis placeholders (full implementation requires frame analysis)
    analysis = {
        'metadata': metadata.to_dict(),
        'content': {
            'motion_blur_level': 'unknown',  # Would require frame diff analysis
            'rolling_shutter_detected': False,  # Would require motion analysis
        },
        'recommendations': {
            'tracking_preset': 'balanced',
            'min_corners': 100,
        }
    }

    return analysis


def load_footage_to_clip(video_path: str):
    """
    Load footage into Blender Movie Clip Editor.

    Args:
        video_path: Path to video file

    Returns:
        MovieClip object or None if Blender not available
    """
    if not HAS_BLENDER:
        return None

    clip = bpy.data.movieclips.load(video_path)
    return clip
