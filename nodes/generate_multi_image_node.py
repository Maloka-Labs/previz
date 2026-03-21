"""
Generate World from Multiple Images — feeds multiple camera angles to Marble
for more accurate 3D world reconstruction.

Pipeline idea:
  Take an initial concept image → use Nunchaku/FLUX/zero123 to generate
  reverse angle, side views → feed all angles into this node →
  World Labs builds a geometrically tighter 3D world.

The API supports up to 4 images in standard mode, or 8 in reconstruction mode.
Each image gets an azimuth tag (0=front, 90=right, 180=back, 270=left)
telling Marble where the camera was pointing.
"""

import base64
from . import api_client


class WorldLabsGenerateMultiImage:
    """
    Multiple images → 3D World.

    Feed 2-8 views of the same scene from different angles.
    Each input gets an azimuth angle so Marble knows the camera position.

    Best results when images show the same environment from genuinely
    different viewpoints with consistent lighting and style.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("WL_API_KEY",),
                "image_front": ("IMAGE",),
                "model": (["Marble 0.1-plus", "Marble 0.1-mini"], {
                    "default": "Marble 0.1-plus",
                    "tooltip": "Multi-image benefits most from plus quality",
                }),
            },
            "optional": {
                "image_right": ("IMAGE",),
                "image_back": ("IMAGE",),
                "image_left": ("IMAGE",),

                "image_front_right": ("IMAGE",),
                "image_back_right": ("IMAGE",),
                "image_back_left": ("IMAGE",),
                "image_front_left": ("IMAGE",),

                "azimuth_front": ("FLOAT", {"default": 0.0, "min": -180.0, "max": 360.0, "step": 15.0,
                    "tooltip": "0 = front/forward facing"}),
                "azimuth_right": ("FLOAT", {"default": 90.0, "min": -180.0, "max": 360.0, "step": 15.0}),
                "azimuth_back": ("FLOAT", {"default": 180.0, "min": -180.0, "max": 360.0, "step": 15.0}),
                "azimuth_left": ("FLOAT", {"default": 270.0, "min": -180.0, "max": 360.0, "step": 15.0}),

                "azimuth_front_right": ("FLOAT", {"default": 45.0, "min": -180.0, "max": 360.0, "step": 15.0}),
                "azimuth_back_right": ("FLOAT", {"default": 135.0, "min": -180.0, "max": 360.0, "step": 15.0}),
                "azimuth_back_left": ("FLOAT", {"default": 225.0, "min": -180.0, "max": 360.0, "step": 15.0}),
                "azimuth_front_left": ("FLOAT", {"default": 315.0, "min": -180.0, "max": 360.0, "step": 15.0}),

                "text_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Optional scene description. If empty, Marble auto-captions.",
                }),
                "reconstruction_mode": ("BOOLEAN", {"default": False,
                    "tooltip": "Enable for 5-8 images. Standard mode supports up to 4."}),
                "disable_recaption": ("BOOLEAN", {"default": False}),
                "display_name": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "poll_interval": ("FLOAT", {"default": 10.0, "min": 3.0, "max": 60.0}),
                "timeout": ("FLOAT", {"default": 600.0, "min": 60.0, "max": 1800.0}),
                "wait_for_result": ("BOOLEAN", {"default": True}),
            },
        }

    RETURN_TYPES = ("WL_OPERATION", "STRING", "STRING", "INT")
    RETURN_NAMES = ("operation", "operation_id", "world_id", "images_sent")
    FUNCTION = "generate"
    CATEGORY = "🌍 World Labs"

    def generate(self, api_key, image_front, model,
                 image_right=None, image_back=None, image_left=None,
                 image_front_right=None, image_back_right=None,
                 image_back_left=None, image_front_left=None,
                 azimuth_front=0.0, azimuth_right=90.0,
                 azimuth_back=180.0, azimuth_left=270.0,
                 azimuth_front_right=45.0, azimuth_back_right=135.0,
                 azimuth_back_left=225.0, azimuth_front_left=315.0,
                 text_prompt="", reconstruction_mode=False,
                 disable_recaption=False, display_name="",
                 seed=-1, poll_interval=10.0, timeout=600.0,
                 wait_for_result=True):

        # Collect all provided images with their azimuths
        image_pairs = [
            (image_front, azimuth_front, "front"),
            (image_right, azimuth_right, "right"),
            (image_back, azimuth_back, "back"),
            (image_left, azimuth_left, "left"),
            (image_front_right, azimuth_front_right, "front-right"),
            (image_back_right, azimuth_back_right, "back-right"),
            (image_back_left, azimuth_back_left, "back-left"),
            (image_front_left, azimuth_front_left, "front-left"),
        ]

        multi_image_prompt = []
        for img_tensor, azimuth, label in image_pairs:
            if img_tensor is None:
                continue

            png_bytes = api_client.image_tensor_to_png_bytes(img_tensor)
            b64 = base64.b64encode(png_bytes).decode("ascii")

            multi_image_prompt.append({
                "azimuth": azimuth,
                "content": {
                    "source": "data_base64",
                    "data_base64": b64,
                    "extension": "png",
                },
            })

        num_images = len(multi_image_prompt)

        if num_images < 2:
            raise ValueError(
                f"Multi-image generation needs at least 2 images. "
                f"Got {num_images}. Connect more angle views or use the "
                f"single-image Generate World (Image) node instead."
            )

        if not reconstruction_mode and num_images > 4:
            raise ValueError(
                f"Standard mode supports max 4 images (got {num_images}). "
                f"Enable reconstruction_mode for 5-8 images."
            )

        if reconstruction_mode and num_images > 8:
            raise ValueError(
                f"Reconstruction mode supports max 8 images (got {num_images})."
            )

        print(f"[WorldLabs Multi-Image] Sending {num_images} views: "
              f"{', '.join(f'{p[2]}({p[1]}°)' for p in image_pairs if p[0] is not None)}")

        world_prompt = {
            "type": "multi-image",
            "multi_image_prompt": multi_image_prompt,
        }
        if reconstruction_mode:
            world_prompt["reconstruct_images"] = True
        if text_prompt.strip():
            world_prompt["text_prompt"] = text_prompt.strip()
        if disable_recaption:
            world_prompt["disable_recaption"] = True

        op = api_client.generate_world(
            api_key=api_key,
            world_prompt=world_prompt,
            display_name=display_name or f"ComfyUI Multi-Image ({num_images} views)",
            model=model,
            seed=seed if seed >= 0 else None,
        )

        operation_id = op.get("operation_id", "")

        if not wait_for_result:
            return (op, operation_id, "", num_images)

        result = api_client.poll_until_done(
            api_key, operation_id,
            interval=poll_interval, timeout=timeout,
        )

        world_id = ""
        meta = result.get("metadata") or {}
        world_id = meta.get("world_id", "")
        if not world_id and result.get("response"):
            world_id = result["response"].get("id", result["response"].get("world_id", ""))

        return (result, operation_id, world_id, num_images)
