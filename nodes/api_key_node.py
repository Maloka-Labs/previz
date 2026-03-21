"""API Key credential node — feeds into all World Labs nodes."""


class WorldLabsAPIKey:
    """Store your World Labs API key. Connect to any generation node."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Your WLT-Api-Key from platform.worldlabs.ai/api-keys",
                }),
            },
        }

    RETURN_TYPES = ("WL_API_KEY",)
    RETURN_NAMES = ("api_key",)
    FUNCTION = "passthrough"
    CATEGORY = "🌍 World Labs"

    def passthrough(self, api_key: str):
        if not api_key.strip():
            raise ValueError("World Labs API key is empty. Get one at platform.worldlabs.ai")
        return (api_key.strip(),)
