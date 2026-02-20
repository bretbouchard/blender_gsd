"""
Footage Profiles Module - Video Metadata Extraction and Content Analysis

Provides advanced footage analysis for motion tracking workflows:
- FFprobe-based metadata extraction
- Device-specific profile inference
- Content quality metrics (motion blur, noise, contrast)
- Rolling shutter detection

Phase 7.2: Footage Profiles
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import subprocess
import json
import re
import math

from .types import FootageMetadata, RollingShutterConfig


# Device-specific rolling shutter read times (in seconds)
ROLLING_SHUTTER_TIMES = {
    # iPhone series
    "iphone_14_pro": 0.010,  # 10ms
    "iphone_14_pro_max": 0.012,
    "iphone_15_pro": 0.010,
    "iphone_15_pro_max": 0.012,
    # Android phones
    "pixel_8_pro": 0.014,
    "samsung_s24": 0.012,
    # Cinema cameras
    "red_komodo": 0.005,  # 5ms
    "red_v_raptor": 0.004,
    "arri_alexa_35": 0.004,
    "blackmagic_ursa_12k": 0.008,
    # DSLR/Mirrorless
    "sony_a7s_iii": 0.008,
    "canon_eos_r5": 0.010,
    # Drones
    "dji_mavic_3": 0.015,
    "dji_mini_4": 0.020,
    # Action cameras
    "gopro_hero_12": 0.025,  # High rolling shutter
}

# Rolling shutter severity thresholds (read time in ms)
SEVERITY_THRESHOLDS = {
    "none": 3.0,  # < 3ms
    "low": 8.0,
    "medium": 15.0,
    "high": float("inf"),  # >= 15ms
}


@dataclass
class ContentAnalysis:
    """
    Content quality analysis results.

    Attributes:
        motion_blur_level: "low", "medium", "high"
        noise_level: "low", "medium", "high"
        contrast_suitability: "poor", "fair", "good", "excellent"
        dominant_motion: "static", "pan", "tilt", "zoom", "handheld"
        average_motion_vector: Average pixel displacement per frame
        sharpness_score: 0.0-1.0
        contrast_ratio: 0.0-1.0
    """
    motion_blur_level: str = "medium"
    noise_level: str = "medium"
    contrast_suitability: str = "good"
    dominant_motion: str = "handheld"
    average_motion_vector: float = 0.0
    sharpness_score: float = 0.5
    contrast_ratio: float = 0.5


class FFprobeMetadataExtractor:
    """
    Comprehensive metadata extraction using ffprobe.

    Extracts video metadata including:
    - Basic info (resolution, fps, codec, duration)
    - Device metadata from QuickTime tags (camera model, ISO, focal length)
    - Color space information
    """

    def __init__(self, ffprobe_path: str = "ffprobe"):
        """
        Initialize the extractor.

        Args:
            ffprobe_path: Path to ffprobe executable (default: system PATH)
        """
        self.ffprobe_path = ffprobe_path
        self._check_ffprobe()

    def _check_ffprobe(self) -> bool:
        """Check if ffprobe is available."""
        try:
            result = subprocess.run(
                [self.ffprobe_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def extract(self, video_path: str) -> FootageMetadata:
        """
        Extract comprehensive metadata from video file.

        Args:
            video_path: Path to video file

        Returns:
            FootageMetadata with extracted information

        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If ffprobe fails
        """
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Run ffprobe
        data = self._run_ffprobe(video_path)

        # Build metadata
        metadata = FootageMetadata(source_path=str(path))

        # Extract video stream info
        video_stream = self._find_video_stream(data)
        if video_stream:
            self._extract_video_info(metadata, video_stream)

        # Extract format info
        fmt = data.get("format", {})
        self._extract_format_info(metadata, fmt)

        # Extract device metadata from tags
        tags = fmt.get("tags", {})
        self._extract_device_metadata(metadata, tags)

        return metadata

    def _run_ffprobe(self, video_path: str) -> Dict[str, Any]:
        """Run ffprobe and return parsed JSON."""
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-show_entries", "stream_tags=format_tags",
            str(video_path),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            raise RuntimeError("ffprobe not found. Please install ffmpeg.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("ffprobe timed out")

        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr}")

        return json.loads(result.stdout)

    def _find_video_stream(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the primary video stream."""
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                return stream
        return None

    def _extract_video_info(
        self,
        metadata: FootageMetadata,
        stream: Dict[str, Any],
    ) -> None:
        """Extract video stream information."""
        # Resolution
        metadata.width = stream.get("width", 1920)
        metadata.height = stream.get("height", 1080)

        # Frame rate
        fps_str = stream.get("r_frame_rate", "24/1")
        metadata.fps = self._parse_frame_rate(fps_str)

        # Codec
        metadata.codec = stream.get("codec_name", "")
        metadata.codec_profile = stream.get("profile", "")

        # Color info
        metadata.color_space = stream.get("color_space", "")
        metadata.color_range = stream.get("color_range", "limited")

        # Bit depth
        bits = stream.get("bits_per_raw_sample") or stream.get("bits_per_pixel", 8)
        metadata.bit_depth = int(bits) if bits else 8

        # Pixel aspect ratio
        par = stream.get("sample_aspect_ratio", "1:1")
        metadata.pixel_aspect_ratio = self._parse_ratio(par)

    def _extract_format_info(
        self,
        metadata: FootageMetadata,
        fmt: Dict[str, Any],
    ) -> None:
        """Extract format information."""
        # Duration
        if "duration" in fmt:
            metadata.duration_seconds = float(fmt["duration"])
            metadata.frame_count = int(metadata.duration_seconds * metadata.fps)

    def _extract_device_metadata(
        self,
        metadata: FootageMetadata,
        tags: Dict[str, Any],
    ) -> None:
        """Extract device metadata from QuickTime/MP4 tags."""
        # Camera make/model
        make = tags.get("com.apple.quicktime.make", "")
        model = tags.get("com.apple.quicktime.model", "")

        # Try other tag formats
        if not model:
            model = tags.get("model", "")
        if not make:
            make = tags.get("make", "")

        # Android format
        if not model:
            model = tags.get("AndroidModel", "")
        if not make:
            make = tags.get("AndroidMake", "")

        metadata.camera_make = make
        metadata.camera_model = model

        # Lens info
        metadata.lens_model = tags.get("com.apple.quicktime.lens", "")

        # Focal length
        fl_str = tags.get("com.apple.quicktime.focal_length", "0")
        metadata.focal_length_mm = self._parse_focal_length(fl_str)

        # ISO
        iso_str = tags.get("com.apple.quicktime.iso", "0")
        metadata.iso = int(float(iso_str)) if iso_str else 0

        # Aperture
        aperture_str = tags.get("com.apple.quicktime.aperture", "")
        if aperture_str:
            metadata.aperture = f"f/{aperture_str}"

        # White balance
        wb_str = tags.get("com.apple.quicktime.white_balance", "0")
        metadata.white_balance = int(float(wb_str)) if wb_str else 0

    def _parse_frame_rate(self, fps_str: str) -> float:
        """Parse frame rate from ffprobe format (e.g., "30000/1001")."""
        try:
            if "/" in fps_str:
                num, den = fps_str.split("/")
                den_val = float(den)
                if den_val > 0:
                    return float(num) / den_val
            return float(fps_str)
        except (ValueError, ZeroDivisionError):
            return 24.0

    def _parse_ratio(self, ratio_str: str) -> float:
        """Parse aspect ratio from format like "1:1" or "16:9"."""
        try:
            if ":" in ratio_str:
                num, den = ratio_str.split(":")
                den_val = float(den)
                if den_val > 0:
                    return float(num) / den_val
            return float(ratio_str)
        except (ValueError, ZeroDivisionError):
            return 1.0

    def _parse_focal_length(self, fl_str: str) -> float:
        """Parse focal length from tag like "4.2 mm"."""
        match = re.search(r"[\d.]+", fl_str)
        if match:
            return float(match.group())
        return 0.0


class FootageAnalyzer:
    """
    Comprehensive footage analysis including content quality metrics.

    Analyzes footage for tracking suitability:
    - Motion blur estimation
    - Noise level detection
    - Contrast analysis
    - Motion pattern classification
    """

    def __init__(self, ffprobe_path: str = "ffprobe"):
        """Initialize analyzer with optional ffprobe path."""
        self.extractor = FFprobeMetadataExtractor(ffprobe_path)

    def analyze(self, video_path: str) -> Tuple[FootageMetadata, ContentAnalysis]:
        """
        Perform comprehensive footage analysis.

        Args:
            video_path: Path to video file

        Returns:
            Tuple of (FootageMetadata, ContentAnalysis)
        """
        # Extract metadata
        metadata = self.extractor.extract(video_path)

        # Perform content analysis (simplified - would need frame access for real analysis)
        content = self._analyze_content(video_path, metadata)

        # Update metadata with content analysis results
        metadata.motion_blur_level = content.motion_blur_level
        metadata.noise_level = content.noise_level
        metadata.contrast_suitability = content.contrast_suitability
        metadata.dominant_motion = content.dominant_motion

        return metadata, content

    def _analyze_content(
        self,
        video_path: str,
        metadata: FootageMetadata,
    ) -> ContentAnalysis:
        """
        Analyze content quality (simplified implementation).

        Full implementation would use frame sampling and image processing.
        This version infers from metadata and heuristics.
        """
        content = ContentAnalysis()

        # Infer motion blur from fps and device
        if metadata.fps >= 60:
            content.motion_blur_level = "low"  # HFR reduces blur
        elif metadata.fps <= 24:
            content.motion_blur_level = "medium"
        else:
            content.motion_blur_level = "medium"

        # Infer noise from ISO (if available)
        if metadata.iso > 0:
            if metadata.iso >= 3200:
                content.noise_level = "high"
            elif metadata.iso >= 1600:
                content.noise_level = "medium"
            else:
                content.noise_level = "low"

        # Infer contrast from resolution and codec
        # Higher resolution typically has better dynamic range
        if metadata.width >= 4096:
            content.contrast_suitability = "excellent"
        elif metadata.width >= 1920:
            content.contrast_suitability = "good"
        else:
            content.contrast_suitability = "fair"

        return content


class RollingShutterDetector:
    """
    Rolling shutter detection and compensation configuration.

    Detects rolling shutter from:
    - Device model inference
    - Visual analysis (would require frame access)
    """

    # Device patterns for rolling shutter inference
    DEVICE_PATTERNS = {
        r"iphone.*14.*pro": 0.010,
        r"iphone.*15.*pro": 0.010,
        r"iphone.*14": 0.012,
        r"iphone.*15": 0.012,
        r"pixel.*8": 0.014,
        r"pixel.*7": 0.016,
        r"galaxy.*s24": 0.012,
        r"galaxy.*s23": 0.014,
        r"gopro.*12": 0.025,
        r"gopro.*11": 0.028,
        r"dji.*mavic.*3": 0.015,
        r"dji.*mini": 0.020,
        r"red.*komodo": 0.005,
        r"red.*raptor": 0.004,
        r"arri.*alexa": 0.004,
        r"blackmagic.*ursa": 0.008,
    }

    def detect(self, metadata: FootageMetadata) -> RollingShutterConfig:
        """
        Detect rolling shutter configuration from metadata.

        Args:
            metadata: FootageMetadata with device info

        Returns:
            RollingShutterConfig with detection results
        """
        config = RollingShutterConfig()
        config.row_count = metadata.height

        # Infer from device model
        device_id = f"{metadata.camera_make} {metadata.camera_model}".lower()

        read_time = 0.0
        for pattern, time in self.DEVICE_PATTERNS.items():
            if re.search(pattern, device_id):
                read_time = time
                break

        if read_time > 0:
            config.detected = True
            config.read_time = read_time
            config.severity = self._get_severity(read_time * 1000)  # Convert to ms
            config.compensation_enabled = config.severity in ("medium", "high")

        return config

    def _get_severity(self, read_time_ms: float) -> str:
        """Get severity level from read time in milliseconds."""
        if read_time_ms < SEVERITY_THRESHOLDS["none"]:
            return "none"
        elif read_time_ms < SEVERITY_THRESHOLDS["low"]:
            return "low"
        elif read_time_ms < SEVERITY_THRESHOLDS["medium"]:
            return "medium"
        else:
            return "high"


class FootageProfile:
    """
    Complete footage profile combining metadata and analysis.

    Provides a unified interface for footage information used
    in tracking workflow configuration.
    """

    def __init__(
        self,
        metadata: FootageMetadata,
        content: Optional[ContentAnalysis] = None,
        rolling_shutter: Optional[RollingShutterConfig] = None,
    ):
        """Initialize footage profile."""
        self.metadata = metadata
        self.content = content or ContentAnalysis()
        self.rolling_shutter = rolling_shutter or RollingShutterConfig()

    @classmethod
    def from_file(
        cls,
        video_path: str,
        analyze_content: bool = True,
        ffprobe_path: str = "ffprobe",
    ) -> "FootageProfile":
        """
        Create footage profile from video file.

        Args:
            video_path: Path to video file
            analyze_content: Whether to perform content analysis
            ffprobe_path: Path to ffprobe executable

        Returns:
            FootageProfile instance
        """
        analyzer = FootageAnalyzer(ffprobe_path)

        if analyze_content:
            metadata, content = analyzer.analyze(video_path)
        else:
            metadata = analyzer.extractor.extract(video_path)
            content = ContentAnalysis()

        # Detect rolling shutter
        rs_detector = RollingShutterDetector()
        rolling_shutter = rs_detector.detect(metadata)

        return cls(metadata, content, rolling_shutter)

    @classmethod
    def from_image_sequence(
        cls,
        sequence_path: str,
        fps: float = 24.0,
    ) -> "FootageProfile":
        """
        Create footage profile from image sequence.

        Args:
            sequence_path: Path to first image or pattern
            fps: Frame rate for the sequence

        Returns:
            FootageProfile instance
        """
        analyzer = ImageSequenceAnalyzer()
        metadata, content = analyzer.analyze(sequence_path, fps)

        # Rolling shutter typically not applicable for still cameras
        # but we can detect from device model if available
        rs_detector = RollingShutterDetector()
        rolling_shutter = rs_detector.detect(metadata)

        return cls(metadata, content, rolling_shutter)

    def get_tracking_recommendations(self) -> Dict[str, Any]:
        """
        Get tracking workflow recommendations based on profile.

        Returns:
            Dict with recommended settings for tracking
        """
        recommendations = {
            "preset": "balanced",
            "min_correlation": 0.6,
            "pattern_size": 21,
            "search_size": 41,
            "rolling_shutter_compensation": False,
            "frame_limit": 0,  # No limit
            "notes": [],
        }

        # Adjust for motion blur
        if self.metadata.motion_blur_level == "high":
            recommendations["preset"] = "precise"
            recommendations["min_correlation"] = 0.5
            recommendations["pattern_size"] = 31
            recommendations["notes"].append("High motion blur - use larger pattern size")

        # Adjust for noise
        if self.metadata.noise_level == "high":
            recommendations["min_correlation"] = 0.5
            recommendations["notes"].append("High noise - lower correlation threshold")

        # Adjust for rolling shutter
        if self.rolling_shutter.compensation_enabled:
            recommendations["rolling_shutter_compensation"] = True
            recommendations["notes"].append(
                f"Rolling shutter detected ({self.rolling_shutter.severity})"
            )

        # Adjust for contrast
        if self.metadata.contrast_suitability == "poor":
            recommendations["notes"].append("Poor contrast - may affect tracking quality")
        elif self.metadata.contrast_suitability == "excellent":
            recommendations["notes"].append("Excellent contrast - tracking should be reliable")

        return recommendations

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization."""
        return {
            "metadata": self.metadata.to_dict(),
            "content": {
                "motion_blur_level": self.content.motion_blur_level,
                "noise_level": self.content.noise_level,
                "contrast_suitability": self.content.contrast_suitability,
                "dominant_motion": self.content.dominant_motion,
                "average_motion_vector": self.content.average_motion_vector,
                "sharpness_score": self.content.sharpness_score,
                "contrast_ratio": self.content.contrast_ratio,
            },
            "rolling_shutter": self.rolling_shutter.to_dict(),
        }


class ImageSequenceAnalyzer:
    """
    Analyzer for image sequences.

    Provides metadata extraction and analysis for image-based
    footage (EXR, DPX, PNG sequences, etc.).
    """

    # Supported image formats
    SUPPORTED_FORMATS = {
        ".exr": {"name": "OpenEXR", "colorspace": "ACEScg", "has_depth": True},
        ".dpx": {"name": "DPX", "colorspace": "Linear", "has_depth": False},
        ".tiff": {"name": "TIFF", "colorspace": "sRGB", "has_depth": False},
        ".tif": {"name": "TIFF", "colorspace": "sRGB", "has_depth": False},
        ".png": {"name": "PNG", "colorspace": "sRGB", "has_depth": False},
        ".jpg": {"name": "JPEG", "colorspace": "sRGB", "has_depth": False},
        ".jpeg": {"name": "JPEG", "colorspace": "sRGB", "has_depth": False},
        ".tga": {"name": "Targa", "colorspace": "sRGB", "has_depth": False},
    }

    def __init__(self):
        """Initialize image sequence analyzer."""
        pass

    def analyze(
        self,
        sequence_path: str,
        fps: float = 24.0,
    ) -> Tuple[FootageMetadata, ContentAnalysis]:
        """
        Analyze image sequence.

        Args:
            sequence_path: Path to first image or pattern
            fps: Frame rate for the sequence

        Returns:
            Tuple of (FootageMetadata, ContentAnalysis)
        """
        path = Path(sequence_path)

        # Parse sequence info
        seq_info = self._parse_sequence(path)

        # Build metadata
        metadata = FootageMetadata(
            source_path=str(seq_info.get("pattern", path)),
            fps=fps,
        )

        # Get dimensions from first frame
        if seq_info.get("first_frame") and seq_info["first_frame"].exists():
            self._extract_image_info(metadata, seq_info["first_frame"])

        # Set frame count
        metadata.frame_count = seq_info.get("frame_count", 1)
        metadata.duration_seconds = metadata.frame_count / fps if fps > 0 else 0

        # Determine colorspace from format
        ext = path.suffix.lower()
        if ext in self.SUPPORTED_FORMATS:
            metadata.color_space = self.SUPPORTED_FORMATS[ext]["colorspace"]

        # Perform content analysis (simplified)
        content = self._analyze_content(seq_info)

        return metadata, content

    def _parse_sequence(self, path: Path) -> Dict[str, Any]:
        """Parse image sequence information."""
        info = {
            "pattern": str(path),
            "first_frame": path if path.exists() else None,
            "frame_count": 1,
            "padding": 4,
            "start_frame": 1,
            "end_frame": 1,
            "missing_frames": [],
        }

        if not path.exists():
            # Check if it's a pattern
            if "#" in str(path):
                info = self._parse_hash_pattern(path)
            elif "%" in str(path):
                info = self._parse_printf_pattern(path)
            return info

        # Try to detect sequence from actual file
        filename = path.name
        parent = path.parent

        # Common patterns: frame_0001.exr, shot.1001.dpx, img_001.png
        patterns = [
            r'^(.+?)[._-]?(\d{4,})(\.[^.]+)$',  # frame_0001.exr or shot.1001.dpx
            r'^(.+?)(\d{2,})(\.[^.]+)$',  # img_001.png
        ]

        for pattern in patterns:
            match = re.match(pattern, filename)
            if match:
                prefix = match.group(1)
                ext = match.group(3)
                padding = len(match.group(2))

                # Find all frames in sequence
                frame_numbers = []
                for f in parent.iterdir():
                    m = re.match(
                        re.escape(prefix) + r'[._-]?(\d{' + str(padding) + r',})' + re.escape(ext),
                        f.name
                    )
                    if m:
                        frame_numbers.append(int(m.group(1)))

                if frame_numbers:
                    frame_numbers.sort()
                    info["frame_count"] = len(frame_numbers)
                    info["start_frame"] = min(frame_numbers)
                    info["end_frame"] = max(frame_numbers)
                    info["padding"] = padding

                    # Find missing frames
                    expected = set(range(info["start_frame"], info["end_frame"] + 1))
                    actual = set(frame_numbers)
                    info["missing_frames"] = sorted(expected - actual)

                    # Create pattern
                    hash_pattern = "#" * padding
                    info["pattern"] = str(parent / f"{prefix}{hash_pattern}{ext}")

                    # Find first existing frame
                    first_num = min(frame_numbers)
                    info["first_frame"] = parent / f"{prefix}{str(first_num).zfill(padding)}{ext}"

                break

        return info

    def _parse_hash_pattern(self, path: Path) -> Dict[str, Any]:
        """Parse #### style pattern."""
        info = {
            "pattern": str(path),
            "first_frame": None,
            "frame_count": 0,
            "padding": 0,
            "start_frame": 1,
            "end_frame": 1,
            "missing_frames": [],
        }

        # Count hashes
        pattern_str = str(path)
        hash_count = pattern_str.count("#")
        if hash_count == 0:
            return info

        info["padding"] = hash_count

        # Convert to glob - use ? for each character instead of * for better matching
        glob_pattern = pattern_str.replace("#" * hash_count, "?" * hash_count)
        parent = path.parent if path.parent.exists() else Path(".")

        # Only try to glob if the parent directory exists
        if not parent.exists():
            return info

        # Find matching files
        try:
            matches = sorted(parent.glob(Path(glob_pattern).name))
            if matches:
                info["first_frame"] = matches[0]
                info["frame_count"] = len(matches)

                # Extract frame numbers
                prefix = pattern_str.split("#")[0]
                ext = path.suffix
                frame_numbers = []
                for m in matches:
                    name = m.name
                    # Extract frame number
                    prefix_name = Path(prefix).name if prefix else ""
                    if prefix_name and name.startswith(prefix_name) and name.endswith(ext):
                        frame_str = name[len(prefix_name):-len(ext)]
                        try:
                            frame_numbers.append(int(frame_str))
                        except ValueError:
                            pass

                if frame_numbers:
                    info["start_frame"] = min(frame_numbers)
                    info["end_frame"] = max(frame_numbers)
        except (ValueError, OSError):
            # Invalid glob pattern or directory access issue
            pass

        return info

    def _parse_printf_pattern(self, path: Path) -> Dict[str, Any]:
        """Parse %04d style pattern."""
        info = {
            "pattern": str(path),
            "first_frame": None,
            "frame_count": 0,
            "padding": 0,
            "start_frame": 1,
            "end_frame": 1,
            "missing_frames": [],
        }

        pattern_str = str(path)

        # Find %d pattern
        match = re.search(r'%(\d*)d', pattern_str)
        if not match:
            return info

        padding_str = match.group(1)
        info["padding"] = int(padding_str) if padding_str else 1

        # Convert to glob
        glob_pattern = re.sub(r'%\d*d', '*', pattern_str)
        parent = path.parent if path.parent.exists() else Path(".")

        matches = sorted(parent.glob(Path(glob_pattern).name))
        if matches:
            info["first_frame"] = matches[0]
            info["frame_count"] = len(matches)

        return info

    def _extract_image_info(
        self,
        metadata: FootageMetadata,
        image_path: Path,
    ) -> None:
        """Extract image dimensions and other info from file."""
        try:
            width, height = self._get_image_dimensions(image_path)
            metadata.width = width
            metadata.height = height
            metadata.codec = image_path.suffix[1:].upper()
        except Exception:
            metadata.width = 1920
            metadata.height = 1080

    def _get_image_dimensions(self, path: Path) -> Tuple[int, int]:
        """Get image dimensions from file header."""
        ext = path.suffix.lower()

        if ext == ".exr":
            return self._get_exr_dimensions(path)
        elif ext == ".dpx":
            return self._get_dpx_dimensions(path)
        elif ext in [".png"]:
            return self._get_png_dimensions(path)
        elif ext in [".jpg", ".jpeg"]:
            return self._get_jpeg_dimensions(path)
        elif ext in [".tiff", ".tif"]:
            return self._get_tiff_dimensions(path)
        else:
            # Try PNG-like header
            try:
                return self._get_png_dimensions(path)
            except Exception:
                return 1920, 1080

    def _get_exr_dimensions(self, path: Path) -> Tuple[int, int]:
        """Read EXR header for dimensions."""
        try:
            with open(path, "rb") as f:
                magic = f.read(4)
                if magic != b'\x76\x2f\x31\x01':
                    return 1920, 1080

                version = struct.unpack('<I', f.read(4))[0]

                while True:
                    name_len = struct.unpack('<B', f.read(1))[0]
                    if name_len == 0:
                        break
                    name = f.read(name_len)[:-1].decode('ascii')

                    type_len = struct.unpack('<B', f.read(1))[0]
                    f.read(type_len)

                    size = struct.unpack('<I', f.read(4))[0]
                    value = f.read(size)

                    if name == "dataWindow":
                        xMin, yMin, xMax, yMax = struct.unpack('<iiii', value)
                        return xMax - xMin + 1, yMax - yMin + 1
        except Exception:
            pass
        return 1920, 1080

    def _get_dpx_dimensions(self, path: Path) -> Tuple[int, int]:
        """Read DPX header for dimensions."""
        try:
            with open(path, "rb") as f:
                magic = f.read(4)
                if magic not in [b'SDPX', b'XPDS']:
                    return 1920, 1080

                f.seek(772)
                width = struct.unpack('>I', f.read(4))[0]
                height = struct.unpack('>I', f.read(4))[0]
                return width, height
        except Exception:
            pass
        return 1920, 1080

    def _get_png_dimensions(self, path: Path) -> Tuple[int, int]:
        """Read PNG header for dimensions."""
        try:
            with open(path, "rb") as f:
                sig = f.read(8)
                if sig != b'\x89PNG\r\n\x1a\n':
                    return 1920, 1080

                f.read(4)  # Length
                chunk_type = f.read(4)
                if chunk_type != b'IHDR':
                    return 1920, 1080

                width, height = struct.unpack('>II', f.read(8))
                return width, height
        except Exception:
            pass
        return 1920, 1080

    def _get_jpeg_dimensions(self, path: Path) -> Tuple[int, int]:
        """Read JPEG header for dimensions."""
        try:
            with open(path, "rb") as f:
                if f.read(2) != b'\xff\xd8':
                    return 1920, 1080

                while True:
                    marker = f.read(2)
                    if not marker or len(marker) < 2:
                        break

                    if marker[0] != 0xFF:
                        break

                    if marker[1] in [0xC0, 0xC2]:
                        f.read(3)
                        height, width = struct.unpack('>HH', f.read(4))
                        return width, height
                    elif marker[1] == 0xDA:
                        break
                    else:
                        length = struct.unpack('>H', f.read(2))[0]
                        f.read(length - 2)
        except Exception:
            pass
        return 1920, 1080

    def _get_tiff_dimensions(self, path: Path) -> Tuple[int, int]:
        """Read TIFF header for dimensions."""
        # TIFF is complex - use defaults
        return 1920, 1080

    def _analyze_content(self, seq_info: Dict[str, Any]) -> ContentAnalysis:
        """Analyze image sequence content (simplified)."""
        content = ContentAnalysis()

        # Image sequences typically have:
        # - Low motion blur (high shutter speed stills)
        content.motion_blur_level = "low"

        # - Good contrast (professional formats)
        content.contrast_suitability = "good"

        # - Unknown dominant motion without frame analysis
        content.dominant_motion = "handheld"

        return content


# Convenience functions

def extract_metadata(video_path: str) -> FootageMetadata:
    """
    Extract metadata from video file.

    Args:
        video_path: Path to video file

    Returns:
        FootageMetadata instance
    """
    extractor = FFprobeMetadataExtractor()
    return extractor.extract(video_path)


def analyze_footage(video_path: str) -> FootageProfile:
    """
    Perform comprehensive footage analysis.

    Args:
        video_path: Path to video file

    Returns:
        FootageProfile instance
    """
    return FootageProfile.from_file(video_path)


def analyze_image_sequence(sequence_path: str, fps: float = 24.0) -> FootageProfile:
    """
    Analyze image sequence.

    Args:
        sequence_path: Path to first image or pattern
        fps: Frame rate for sequence

    Returns:
        FootageProfile instance
    """
    return FootageProfile.from_image_sequence(sequence_path, fps)


def get_tracking_recommendations(video_path: str) -> Dict[str, Any]:
    """
    Get tracking recommendations for footage.

    Args:
        video_path: Path to video file

    Returns:
        Dict with recommended tracking settings
    """
    profile = FootageProfile.from_file(video_path)
    return profile.get_tracking_recommendations()
