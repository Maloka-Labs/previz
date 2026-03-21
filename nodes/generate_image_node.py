"""Generate a 3D world from a ComfyUI IMAGE tensor via Marble API."""

import base64
from . import api_client


class WorldLabsGenerateImage:
    """
    Image → 3D World.
    Takes a ComfyUI IMAGE (e.g. from a FLUX/SDXL generation, a LoadImage node,
    or any upstream image) and sends it to Marble to create a navigable 3D world.
    Perfect for turning concept art into explorable environments.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("WL_API_KEY",),
                "image": ("IMAGE",),
                "model": (["Marble 0.1-plus", "Marble 0.1-mini"], {
                    "default": "Marble 0.1-plus",
                }),
            },
            "optional": {
                "text_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Optional text guidance. If empty, Marble auto-captions the image.",
                }),
                "is_panorama": ("BOOLEAN", {"default": False,
                    "tooltip": "Set True if the input image is already a 360° panorama"}),
                "display_name": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "disable_recaption": ("BOOLEAN", {"default": False}),
                "upload_method": (["base64_inline", "media_asset_upload"], {
                    "default": "base64_inline",
                    "tooltip": "base64_inline is simpler; media_asset_upload for large images",
                }),
                "poll_interval": ("FLOAT", {"default": 10.0, "min": 3.0, "max": 60.0}),
                "timeout": ("FLOAT", {"default": 600.0, "min": 60.0, "max": 1800.0}),
                "wait_for_result": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("WL_OPERATION", "STRING", "STRING")
    RETURN_NAMES = ("operation", "operation_id", "world_id")
    FUNCTION = "generate"
    CATEGORY = "🌍 World Labs"

    def generate(self, api_key, image, model,
                 text_prompt="", is_panorama=False, display_name="",
                 seed=-1, disable_recaption=False,
                 upload_method="base64_inline",
                 poll_interval=10.0, timeout=600.0, wait_for_result=True):

        png_bytes = api_client.image_tensor_to_png_bytes(image)

        if upload_method == "media_asset_upload":
            # Step 1: prepare upload
            prep = api_client.prepare_upload(api_key, "comfyui_input.png", "image", "png")
            media_asset_id = prep["media_asset"]["media_asset_id"]
            upload_url = prep["upload_info"]["upload_url"]
            req_headers = prep["upload_info"].get("required_headers") or {}
            req_headers["Content-Type"] = "image/png"

            # Step 2: upload
            api_client.upload_to_signed_url(upload_url, png_bytes, req_headers)

            # Step 3: build prompt with media_asset reference
            image_prompt = {
                "source": "media_asset",
                "media_asset_id": media_asset_id,
            }
        else:
            # Inline base64
            b64 = base64.b64encode(png_bytes).decode("ascii")
            image_prompt = {
                "source": "data_base64",
                "data_base64": b64,
                "extension": "png",
            }

        world_prompt = {
            "type": "image",
            "image_prompt": image_prompt,
        }
        if text_prompt.strip():
            world_prompt["text_prompt"] = text_prompt.strip()
        if is_panorama:
            world_prompt["is_pano"] = True
        if disable_recaption:
            world_prompt["disable_recaption"] = True

        op = api_client.generate_world(
            api_key=api_key,
            world_prompt=world_prompt,
            display_name=display_name or "ComfyUI Image World",
            model=model,
            seed=seed if seed >= 0 else None,
        )

        operation_id = op.get("operation_id", "")

        if not wait_for_result:
            return (op, operation_id, "")

        result = api_client.poll_until_done(
            api_key, operation_id,
            interval=poll_interval, timeout=timeout,
        )

        world_id = ""
        meta = result.get("metadata") or {}
        world_id = meta.get("world_id", "")
        if not world_id and result.get("response"):
            world_id = result["response"].get("id", result["response"].get("world_id", ""))

        return (result, operation_id, world_id)
