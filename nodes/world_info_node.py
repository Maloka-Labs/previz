"""Extract info and URLs from a completed world — useful for logging, UI, and chaining."""

from . import api_client


class WorldLabsWorldInfo:
    """
    Extract all metadata from a generated world:
    caption, Marble viewer URL, thumbnail URL, mesh URL, etc.
    Useful for building storyboard metadata or linking to the
    interactive 3D viewer.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("WL_API_KEY",),
            },
            "optional": {
                "operation": ("WL_OPERATION",),
                "world_id": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("world_id", "marble_url", "caption", "thumbnail_url", "mesh_url", "model_used")
    FUNCTION = "extract"
    CATEGORY = "🌍 World Labs"

    def extract(self, api_key, operation=None, world_id=""):
        resolved_id = world_id.strip()
        world = None

        if operation:
            resp = operation.get("response") or {}
            if resp:
                world = resp
                resolved_id = resolved_id or resp.get("id") or resp.get("world_id") or ""
            if not resolved_id:
                meta = operation.get("metadata") or {}
                resolved_id = meta.get("world_id", "")

        if not world and resolved_id:
            data = api_client.get_world(api_key, resolved_id)
            world = data.get("world", data)

        if not world:
            raise RuntimeError("No world data found. Provide operation or world_id.")

        assets = world.get("assets") or {}
        imagery = assets.get("imagery") or {}
        mesh = assets.get("mesh") or {}

        return (
            world.get("id") or world.get("world_id") or resolved_id,
            world.get("world_marble_url", ""),
            assets.get("caption", ""),
            assets.get("thumbnail_url", ""),
            mesh.get("collider_mesh_url", ""),
            world.get("model", ""),
        )
