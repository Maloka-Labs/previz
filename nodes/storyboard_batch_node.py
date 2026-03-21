"""
Storyboard Batch Generator — the filmmaker's power node.
Takes a multi-line shot list and generates a 3D world + panorama for each shot.
Returns a batch of panorama images for visual storyboarding.
"""

import time
import json
import os
from . import api_client


class WorldLabsStoryboardBatch:
    """
    AI Film Storyboard Generator.

    Paste a shot list (one scene description per line) and this node will:
    1. Generate a 3D world for each shot via Marble
    2. Download the 360° panorama for each
    3. Output a batch of images + a JSON manifest

    Example shot list:
      INT. NOIR DETECTIVE OFFICE - NIGHT — rain on windows, desk lamp, whiskey glass
      EXT. RAINY TOKYO STREET - NIGHT — neon reflections on wet pavement, steam rising
      INT. SPACESHIP BRIDGE - DAY — holographic displays, captain's chair, starfield outside

    Use with Marble 0.1-mini for fast iteration, 0.1-plus for hero frames.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("WL_API_KEY",),
                "shot_list": ("STRING", {
                    "default": "INT. NOIR DETECTIVE OFFICE - NIGHT — rain on windows, desk lamp\nEXT. RAINY TOKYO STREET - NIGHT — neon reflections, steam rising\nINT. SPACESHIP BRIDGE - DAY — holographic displays, starfield",
                    "multiline": True,
                    "tooltip": "One scene per line. Use screenplay-style descriptions for best results.",
                }),
                "model": (["Marble 0.1-plus", "Marble 0.1-mini"], {
                    "default": "Marble 0.1-mini",
                    "tooltip": "mini for fast iteration, plus for hero frames",
                }),
            },
            "optional": {
                "project_name": ("STRING", {"default": "storyboard"}),
                "prefix_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Text prepended to every shot (e.g. 'Cinematic, photorealistic, 8K,')",
                }),
                "poll_interval": ("FLOAT", {"default": 10.0, "min": 3.0, "max": 60.0}),
                "timeout_per_shot": ("FLOAT", {"default": 600.0, "min": 60.0, "max": 1800.0}),
                "output_directory": ("STRING", {"default": "output/worldlabs_storyboard"}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("panorama_batch", "manifest_json", "output_dir")
    FUNCTION = "generate_storyboard"
    CATEGORY = "🌍 World Labs"
    OUTPUT_NODE = True

    def generate_storyboard(self, api_key, shot_list, model,
                            project_name="storyboard", prefix_prompt="",
                            poll_interval=10.0, timeout_per_shot=600.0,
                            output_directory="output/worldlabs_storyboard"):

        import torch

        lines = [l.strip() for l in shot_list.strip().split("\n") if l.strip()]
        if not lines:
            raise ValueError("Shot list is empty.")

        os.makedirs(output_directory, exist_ok=True)
        manifest = {"project": project_name, "model": model, "shots": []}
        all_tensors = []

        for idx, shot_desc in enumerate(lines):
            shot_num = idx + 1
            full_prompt = f"{prefix_prompt} {shot_desc}".strip() if prefix_prompt else shot_desc
            display = f"{project_name} — Shot {shot_num:02d}"

            print(f"[WorldLabs Storyboard] Generating shot {shot_num}/{len(lines)}: {shot_desc[:80]}...")

            # Generate world
            world_prompt = {"type": "text", "text_prompt": full_prompt}
            op = api_client.generate_world(
                api_key=api_key,
                world_prompt=world_prompt,
                display_name=display,
                model=model,
            )
            operation_id = op.get("operation_id", "")

            # Poll until done
            result = api_client.poll_until_done(
                api_key, operation_id,
                interval=poll_interval, timeout=timeout_per_shot,
            )

            # Extract world data
            resp = result.get("response") or {}
            world_id = resp.get("id") or resp.get("world_id") or ""
            assets = resp.get("assets") or {}
            imagery = assets.get("imagery") or {}
            pano_url = imagery.get("pano_url")
            caption = assets.get("caption", "")
            marble_url = resp.get("world_marble_url", "")

            # Download panorama
            pano_tensor = None
            saved_path = ""
            if pano_url:
                pano_bytes = api_client.download_panorama(pano_url)
                pano_tensor = api_client.png_bytes_to_tensor(pano_bytes)
                fname = f"shot_{shot_num:02d}_{world_id or 'unknown'}.png"
                saved_path = os.path.join(output_directory, fname)
                with open(saved_path, "wb") as f:
                    f.write(pano_bytes)
                all_tensors.append(pano_tensor)

            manifest["shots"].append({
                "shot_number": shot_num,
                "description": shot_desc,
                "full_prompt": full_prompt,
                "world_id": world_id,
                "marble_url": marble_url,
                "pano_url": pano_url or "",
                "caption": caption,
                "saved_path": saved_path,
            })

            print(f"[WorldLabs Storyboard] Shot {shot_num} complete: {marble_url}")

        # Save manifest
        manifest_path = os.path.join(output_directory, f"{project_name}_manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Stack tensors into a batch [N, H, W, 3]
        if all_tensors:
            batch = torch.cat(all_tensors, dim=0)
        else:
            # Fallback: 1x1 black pixel
            batch = torch.zeros(1, 1, 1, 3)

        manifest_str = json.dumps(manifest, indent=2)
        return (batch, manifest_str, output_directory)
