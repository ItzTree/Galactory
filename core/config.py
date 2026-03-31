# Window
WINDOW_TITLE = "3D Folder Explorer"
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080

# Node colors (R, G, B, A)
FOLDER_COLOR = (1.0, 0.95, 0.25, 1.0)
PERMISSION_ERROR_COLOR = (0.5, 0.5, 0.5, 1.0)

# File colors by extension category
FILE_COLORS = {
    # Image
    "png": (0.35, 0.95, 0.45, 1.0), "jpg": (0.35, 0.95, 0.45, 1.0), "jpeg": (0.35, 0.95, 0.45, 1.0),
    "gif": (0.35, 0.95, 0.45, 1.0), "svg": (0.35, 0.95, 0.45, 1.0), "webp": (0.35, 0.95, 0.45, 1.0),
    "bmp": (0.35, 0.95, 0.45, 1.0),
    # Video
    "mp4": (1.0, 0.35, 0.35, 1.0), "mov": (1.0, 0.35, 0.35, 1.0), "avi": (1.0, 0.35, 0.35, 1.0),
    "mkv": (1.0, 0.35, 0.35, 1.0), "wmv": (1.0, 0.35, 0.35, 1.0), "flv": (1.0, 0.35, 0.35, 1.0),
    # Document
    "pdf": (0.35, 0.55, 1.0, 1.0), "docx": (0.35, 0.55, 1.0, 1.0), "doc": (0.35, 0.55, 1.0, 1.0),
    "pptx": (0.35, 0.55, 1.0, 1.0), "xlsx": (0.35, 0.55, 1.0, 1.0), "txt": (0.35, 0.55, 1.0, 1.0),
    "md": (0.35, 0.55, 1.0, 1.0),
    # Code
    "py": (0.85, 0.35, 1.0, 1.0), "js": (0.85, 0.35, 1.0, 1.0), "ts": (0.85, 0.35, 1.0, 1.0),
    "cpp": (0.85, 0.35, 1.0, 1.0), "c": (0.85, 0.35, 1.0, 1.0), "java": (0.85, 0.35, 1.0, 1.0),
    "html": (0.85, 0.35, 1.0, 1.0), "css": (0.85, 0.35, 1.0, 1.0), "go": (0.85, 0.35, 1.0, 1.0),
    "rs": (0.85, 0.35, 1.0, 1.0),
    # Archive
    "zip": (1.0, 0.65, 0.25, 1.0), "rar": (1.0, 0.65, 0.25, 1.0), "7z": (1.0, 0.65, 0.25, 1.0),
    "tar": (1.0, 0.65, 0.25, 1.0), "gz": (1.0, 0.65, 0.25, 1.0),
    # Audio
    "mp3": (0.35, 0.95, 1.0, 1.0), "wav": (0.35, 0.95, 1.0, 1.0), "flac": (0.35, 0.95, 1.0, 1.0),
    "aac": (0.35, 0.95, 1.0, 1.0), "ogg": (0.35, 0.95, 1.0, 1.0),
}
FILE_COLOR_DEFAULT = (0.75, 0.75, 0.75, 1.0)   # other

# Node visual scale (radius of the sphere model)
FOLDER_SCALE = 0.14
FILE_SCALE = 0.08
CENTER_PLANET_SCALE = 0.42   # ~3× FOLDER_SCALE
CENTER_PLANET_COLOR = (1.0, 0.95, 0.25, 1.0)  # same hue as folder

# Layout
SPHERE_RADIUS = 3.5
MAX_NODES = 60

# Camera
CAMERA_DIST_DEFAULT = 8.0
CAMERA_DIST_MIN = 3.0
CAMERA_DIST_MAX = 20.0
CAMERA_ZOOM_STEP = 1.2
CAMERA_ROT_SPEED = 200.0      # degrees per normalized mouse unit
CAMERA_DRAG_THRESHOLD = 0.01  # normalized mouse units before drag is detected

# Background color
BG_COLOR = (0.04, 0.04, 0.10, 1.0)
