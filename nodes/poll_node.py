"""Poll a World Labs operation until complete."""

from . import api_client


class WorldLabsPollOperation:
    """
    Poll an in-progress operation.
    Use when you set wait_for_result=False on a Generate node.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("WL_API_KEY",),
                "operation_id": ("STRING", {"default": ""}),
            },
            "optional": {
                "poll_interval": ("FLOAT", {"default": 10.0, "min": 3.0, "max": 60.0}),
                "timeout": ("FLOAT", {"default": 600.0, "min": 60.0, "max": 1800.0}),
            },
        }

    RETURN_TYPES = ("WL_OPERATION", "STRING", "BOOLEAN")
    RETURN_NAMES = ("operation", "world_id", "is_done")
    FUNCTION = "poll"
    CATEGORY = "🌍 World Labs"

    def poll(self, api_key, operation_id, poll_interval=10.0, timeout=600.0):
        if not operation_id.strip():
            raise ValueError("operation_id is empty")

        result = api_client.poll_until_done(
            api_key, operation_id.strip(),
            interval=poll_interval, timeout=timeout,
        )

        world_id = ""
        meta = result.get("metadata") or {}
        world_id = meta.get("world_id", "")
        if not world_id and result.get("response"):
            world_id = result["response"].get("id", result["response"].get("world_id", ""))

        return (result, world_id, True)
