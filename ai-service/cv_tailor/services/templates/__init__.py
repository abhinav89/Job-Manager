from .jakes_resume import JAKES_RESUME
from .modern_resume import MODERN_RESUME
from .layouts import ADDITIONAL_TEMPLATES

TEMPLATES = {
    "original": JAKES_RESUME,
    "classic": JAKES_RESUME,
    "modern": MODERN_RESUME,
    **ADDITIONAL_TEMPLATES,
}

TEMPLATE_CATALOG = [{"id": key, "name": key.title()} for key in TEMPLATES]
