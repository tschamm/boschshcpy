from .shutter_contact import SHCShutterContact
from .shutter_control import SHCShutterControl

MODEL_MAPPING = {
    "SWD": "ShutterContact",
    "BBL": "ShutterControl"
    }

SUPPORTED_MODELS = MODEL_MAPPING.keys()
