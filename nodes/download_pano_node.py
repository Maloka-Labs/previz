"""Download the 360° panorama from a completed World Labs world."""

import os
from . import api_client


class WorldLabsDownloadPano:
    """
    Extract the equirectangular 360° panorama from a generated world.
    Outputs a standard ComfyUI IMAGE tensor you can pipe into:
      • Preview Image / Save Image
      • Image-to-video (Kling, Runway, SVD)
      • ControlNet for consistent scene lighting
      • Further World Labs generation (panorama → expanded world)

    For storyboarding: chain multiple of these to build a shot list
    with consistent environments.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("WL_API_KEY",),
            },
            "optional": {
                "operation": ("WL_OPERATION", {"tooltip": "Connect from a Generate or Poll node"}),
                "world_id": ("STRING", {"default": "",
                    "tooltip": "Or provide a world_id directly (overrides operation)"}),
                "save_to_disk": ("BOOLEAN", {"default": True}),
                "output_directory": ("STRING", {
                    "default": "output/worldlabs_panos",
                    "tooltip": "Relative to ComfyUI root",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("panorama_image", "pano_url", "saved_path")
    FUNCTION = "download"
    CATEGORY = "🌍 World Labs"
    OUTPUT_NODE = True

    def download(self, api_key,
                 operation=None, world_id="",
                 save_to_disk=True, output_directory="output/worldlabs_panos"):

        pano_url = None
        resolved_world_id = world_id.strip()

        # Try to extract pano_url from operation result
        if operation and not resolved_world_id:
            resp = operation.get("response") or {}
            assets = resp.get("assets") or {}
            imagery = assets.get("imagery") or {}
            pano_url = imagery.get("pano_url")
            resolved_world_id = resp.get("id") or resp.get("world_id") or ""
            if not resolved_world_id:
                meta = operation.get("metadata") or {}
                resolved_world_id = meta.get("world_id", "")

        # If we still don't have the pano_url, fetch the world directly
        if not pano_url and resolved_world_id:
            world_data = api_client.get_world(api_key, resolved_world_id)
            # Handle both {world: {...}} and flat responses
            world = world_data.get("world", world_data)
            assets = world.get("assets") or {}
            imagery = assets.get("imagery") or {}
            pano_url = imagery.get("pano_url")

        if not pano_url:
            raise RuntimeError(
                "Could not find panorama URL. Ensure world generation completed successfully."
            )

        # Download the panorama
        pano_bytes = api_client.download_panorama(pano_url)

        # Convert to ComfyUI IMAGE tensor
        image_tensor = api_client.png_bytes_to_tensor(pano_bytes)

        # Optionally save to disk
        saved_path = ""
        if save_to_disk:
            os.makedirs(output_directory, exist_ok=True)
            fname = f"pano_{resolved_world_id or 'unknown'}.png"
            saved_path = os.path.join(output_directory, fname)
            with open(saved_path, "wb") as f:
                f.write(pano_bytes)

        return (image_tensor, pano_url, saved_path)
