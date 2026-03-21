"""Download Gaussian Splat .spz files from a completed world."""

import os
from . import api_client


class WorldLabsDownloadSplat:
    """
    Download the 3D Gaussian Splat file (.spz) from a generated world.
    Available resolutions: 100k, 500k, full_res.
    Use these in Three.js/Spark, Blender, Unity, or Unreal Engine
    for full 3D scene composition.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("WL_API_KEY",),
                "resolution": (["full_res", "500k", "100k"], {
                    "default": "full_res",
                    "tooltip": "full_res = highest detail, 100k = lightweight preview",
                }),
            },
            "optional": {
                "operation": ("WL_OPERATION",),
                "world_id": ("STRING", {"default": ""}),
                "output_directory": ("STRING", {
                    "default": "output/worldlabs_splats",
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("splat_file_path", "splat_url")
    FUNCTION = "download"
    CATEGORY = "🌍 World Labs"
    OUTPUT_NODE = True

    def download(self, api_key, resolution="full_res",
                 operation=None, world_id="",
                 output_directory="output/worldlabs_splats"):

        splat_urls = None
        resolved_world_id = world_id.strip()

        if operation and not resolved_world_id:
            resp = operation.get("response") or {}
            assets = resp.get("assets") or {}
            splats = assets.get("splats") or {}
            splat_urls = splats.get("spz_urls")
            resolved_world_id = resp.get("id") or resp.get("world_id") or ""
            if not resolved_world_id:
                meta = operation.get("metadata") or {}
                resolved_world_id = meta.get("world_id", "")

        if not splat_urls and resolved_world_id:
            world_data = api_client.get_world(api_key, resolved_world_id)
            world = world_data.get("world", world_data)
            assets = world.get("assets") or {}
            splats = assets.get("splats") or {}
            splat_urls = splats.get("spz_urls")

        if not splat_urls:
            raise RuntimeError("No Gaussian splat URLs found in world assets.")

        url = splat_urls.get(resolution)
        if not url:
            available = list(splat_urls.keys())
            raise RuntimeError(
                f"Resolution '{resolution}' not available. Options: {available}"
            )

        splat_bytes = api_client.download_splat(url)

        os.makedirs(output_directory, exist_ok=True)
        fname = f"splat_{resolved_world_id or 'unknown'}_{resolution}.spz"
        save_path = os.path.join(output_directory, fname)
        with open(save_path, "wb") as f:
            f.write(splat_bytes)

        return (save_path, url)
