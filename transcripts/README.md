# YouTube Transcripts

This directory stores transcripts from Blender and Geometry Nodes tutorials.

## Usage

### Fetch transcripts from Python

```python
from lib.utils.youtube_transcript import get_transcript, save_transcript

# Get transcript as text
text = get_transcript("https://youtube.com/watch?v=VIDEO_ID")

# Save to file
save_transcript("https://youtube.com/watch?v=VIDEO_ID", "transcripts/tutorial_name.txt")
```

### Fetch transcripts from CLI

```bash
# Using yt-dlp (recommended)
yt-dlp --write-auto-sub --sub-lang en --skip-download "https://youtube.com/watch?v=VIDEO_ID"

# Using our script
python lib/utils/youtube_transcript.py "https://youtube.com/watch?v=VIDEO_ID" tutorial_name.txt
```

## Setup

```bash
pip install yt-dlp
```

## Suggested Blender Tutorial Channels

- **Blender Guru** - https://www.youtube.com/@BlenderGuru
- **CG Cookie** - https://www.youtube.com/@cgcookie
- **Default Cube** - https://www.youtube.com/@DefaultCube
- **CG Matter** - https://www.youtube.com/@CGMatter
- **Erindale** - Geometry Nodes focus - https://www.youtube.com/@Erindale
- **Johnny Matthews** - Geometry Nodes - https://www.youtube.com/@johnny_matthews
- **Cartesian Caramel** - Advanced GN - https://www.youtube.com/@CartesianCaramel
