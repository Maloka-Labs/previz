"""Generate a 3D world from a text prompt via Marble API."""

from . import api_client


class WorldLabsGenerateText:
    """
    Text → 3D World.
    Sends a text prompt to Marble and waits for the world to generate.
    Outputs the full operation result for downstream nodes.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("WL_API_KEY",),
                "prompt": ("STRING", {
                    "default": "A dimly lit noir detective office, rain on the window, 1940s",
                    "multiline": True,
                    "tooltip": "Describe the 3D world / scene you want to generate",
                }),
                "model": (["Marble 0.1-plus", "Marble 0.1-mini"], {
                    "default": "Marble 0.1-plus",
                    "tooltip": "plus = best quality (~5 min), mini = fast draft (~30s)",
                }),
            },
            "optional": {
                "display_name": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647,
                          "tooltip": "-1 for random"}),
                "disable_recaption": ("BOOLEAN", {"default": False,
                    "tooltip": "Use your prompt exactly without AI recaptioning"}),
                "poll_interval": ("FLOAT", {"default": 10.0, "min": 3.0, "max": 60.0,
                    "tooltip": "Seconds between status checks"}),
                "timeout": ("FLOAT", {"default": 600.0, "min": 60.0, "max": 1800.0,
                    "tooltip": "Max seconds to wait for generation"}),
                "wait_for_result": ("BOOLEAN", {"default": True,
                    "tooltip": "If False, returns immediately with operation_id (use Poll node)"}),
            },
        }

    RETURN_TYPES = ("WL_OPERATION", "STRING", "STRING")
    RETURN_NAMES = ("operation", "operation_id", "world_id")
    FUNCTION = "generate"
    CATEGORY = "🌍 World Labs"

    def generate(self, api_key, prompt, model,
                 display_name="", seed=-1, disable_recaption=False,
                 poll_interval=10.0, timeout=600.0, wait_for_result=True):

        world_prompt = {"type": "text", "text_prompt": prompt}
        if disable_recaption:
            world_prompt["disable_recaption"] = True

        op = api_client.generate_world(
            api_key=api_key,
            world_prompt=world_prompt,
            display_name=display_name or f"ComfyUI: {prompt[:60]}",
            model=model,
            seed=seed if seed >= 0 else None,
        )

        operation_id = op.get("operation_id", "")

        if not wait_for_result:
            return (op, operation_id, "")

        # Poll until done
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
