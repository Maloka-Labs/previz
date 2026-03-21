"""
Scene Compositor — layered character generation on a Virtual Camera background plate.

Takes a background frame (from Virtual Camera or Download Panorama),
lets you define up to 4 character regions with position, size, and prompt,
then outputs the composited frame plus individual layer masks.

Each region becomes an inpainting zone — downstream nodes handle the actual
generation (ControlNet, LoRA, etc.) while this node handles the spatial logic:
where characters go, what size they are, and how the layers blend.
"""



class WorldLabsSceneCompositor:
    """
    Layer-based scene compositor for character placement.

    Workflow:
      Virtual Camera → Scene Compositor → (per-region masks + crops)
                                        → img2img with LoRA per region
                                        → Composite Layers node → final frame

    Outputs region masks and cropped background patches so you can
    generate characters that match the scene lighting and perspective.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "background": ("IMAGE",),

                "region_1_enabled": ("BOOLEAN", {"default": True}),
                "region_1_x": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": "Horizontal center (0=left, 1=right)"}),
                "region_1_y": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": "Vertical center (0=top, 1=bottom)"}),
                "region_1_width": ("FLOAT", {"default": 0.25, "min": 0.05, "max": 1.0, "step": 0.01}),
                "region_1_height": ("FLOAT", {"default": 0.6, "min": 0.05, "max": 1.0, "step": 0.01}),
                "region_1_prompt": ("STRING", {
                    "default": "a detective sitting at a desk, film noir, 1940s",
                    "multiline": True,
                }),
            },
            "optional": {
                "region_2_enabled": ("BOOLEAN", {"default": False}),
                "region_2_x": ("FLOAT", {"default": 0.25, "min": 0.0, "max": 1.0, "step": 0.01}),
                "region_2_y": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.01}),
                "region_2_width": ("FLOAT", {"default": 0.2, "min": 0.05, "max": 1.0, "step": 0.01}),
                "region_2_height": ("FLOAT", {"default": 0.55, "min": 0.05, "max": 1.0, "step": 0.01}),
                "region_2_prompt": ("STRING", {"default": "", "multiline": True}),

                "region_3_enabled": ("BOOLEAN", {"default": False}),
                "region_3_x": ("FLOAT", {"default": 0.75, "min": 0.0, "max": 1.0, "step": 0.01}),
                "region_3_y": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.01}),
                "region_3_width": ("FLOAT", {"default": 0.2, "min": 0.05, "max": 1.0, "step": 0.01}),
                "region_3_height": ("FLOAT", {"default": 0.55, "min": 0.05, "max": 1.0, "step": 0.01}),
                "region_3_prompt": ("STRING", {"default": "", "multiline": True}),

                "region_4_enabled": ("BOOLEAN", {"default": False}),
                "region_4_x": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "region_4_y": ("FLOAT", {"default": 0.4, "min": 0.0, "max": 1.0, "step": 0.01}),
                "region_4_width": ("FLOAT", {"default": 0.15, "min": 0.05, "max": 1.0, "step": 0.01}),
                "region_4_height": ("FLOAT", {"default": 0.4, "min": 0.05, "max": 1.0, "step": 0.01}),
                "region_4_prompt": ("STRING", {"default": "", "multiline": True}),

                "mask_feather": ("INT", {"default": 24, "min": 0, "max": 128, "step": 4,
                    "tooltip": "Soft edge in pixels for blending regions into the background"}),
                "mask_shape": (["rectangle", "ellipse"], {"default": "ellipse",
                    "tooltip": "Ellipse gives more natural character silhouettes"}),
                "context_padding": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 0.5, "step": 0.05,
                    "tooltip": "Extra background context around each crop for inpainting coherence"}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK", "IMAGE", "MASK", "IMAGE", "MASK", "IMAGE", "MASK", "IMAGE", "STRING")
    RETURN_NAMES = (
        "region_1_crop", "region_1_mask",
        "region_2_crop", "region_2_mask",
        "region_3_crop", "region_3_mask",
        "region_4_crop", "region_4_mask",
        "preview_with_guides", "region_prompts_json",
    )
    FUNCTION = "compose"
    CATEGORY = "🌍 World Labs/Filmmaker"

    def compose(self, background,
                region_1_enabled=True, region_1_x=0.5, region_1_y=0.6,
                region_1_width=0.25, region_1_height=0.6, region_1_prompt="",
                region_2_enabled=False, region_2_x=0.25, region_2_y=0.6,
                region_2_width=0.2, region_2_height=0.55, region_2_prompt="",
                region_3_enabled=False, region_3_x=0.75, region_3_y=0.6,
                region_3_width=0.2, region_3_height=0.55, region_3_prompt="",
                region_4_enabled=False, region_4_x=0.5, region_4_y=0.4,
                region_4_width=0.15, region_4_height=0.4, region_4_prompt="",
                mask_feather=24, mask_shape="ellipse", context_padding=0.15):

        import torch
        import json
        import numpy as np

        if len(background.shape) == 4:
            bg = background[0].cpu().numpy()
        else:
            bg = background.cpu().numpy()

        h, w, c = bg.shape

        regions = []
        for i, (enabled, rx, ry, rw, rh, prompt) in enumerate([
            (region_1_enabled, region_1_x, region_1_y, region_1_width, region_1_height, region_1_prompt),
            (region_2_enabled, region_2_x, region_2_y, region_2_width, region_2_height, region_2_prompt),
            (region_3_enabled, region_3_x, region_3_y, region_3_width, region_3_height, region_3_prompt),
            (region_4_enabled, region_4_x, region_4_y, region_4_width, region_4_height, region_4_prompt),
        ], 1):
            if enabled:
                regions.append({
                    "index": i,
                    "cx": rx, "cy": ry,
                    "rw": rw, "rh": rh,
                    "prompt": prompt,
                })

        crops = []
        masks = []
        prompts_data = []

        # Build preview overlay
        preview = bg.copy()

        # Region colours for guides (RGBA overlays)
        guide_colors = [
            np.array([0.85, 0.35, 0.2]),   # coral
            np.array([0.1, 0.6, 0.45]),     # teal
            np.array([0.75, 0.55, 0.1]),    # amber
            np.array([0.5, 0.3, 0.7]),      # purple
        ]

        for idx in range(4):
            region = None
            for r in regions:
                if r["index"] == idx + 1:
                    region = r
                    break

            if region is None:
                # Output a 1x1 black placeholder
                crops.append(torch.zeros(1, 64, 64, 3))
                masks.append(torch.zeros(1, 64, 64))
                continue

            # Compute pixel coordinates
            cx_px = int(region["cx"] * w)
            cy_px = int(region["cy"] * h)
            rw_px = int(region["rw"] * w)
            rh_px = int(region["rh"] * h)

            # Region bounds (clamped)
            x1 = max(0, cx_px - rw_px // 2)
            y1 = max(0, cy_px - rh_px // 2)
            x2 = min(w, cx_px + rw_px // 2)
            y2 = min(h, cy_px + rh_px // 2)

            # Context-padded bounds for crop
            pad_x = int(rw_px * context_padding)
            pad_y = int(rh_px * context_padding)
            cx1 = max(0, x1 - pad_x)
            cy1 = max(0, y1 - pad_y)
            cx2 = min(w, x2 + pad_x)
            cy2 = min(h, y2 + pad_y)

            # Crop the background region with context
            crop = bg[cy1:cy2, cx1:cx2].copy()
            crop_tensor = torch.from_numpy(crop).unsqueeze(0).float()
            crops.append(crop_tensor)

            # Build mask (in crop space)
            crop_h = cy2 - cy1
            crop_w = cx2 - cx1
            mask = np.zeros((crop_h, crop_w), dtype=np.float32)

            # Region bounds in crop space
            rx1 = x1 - cx1
            ry1 = y1 - cy1
            rx2 = x2 - cx1
            ry2 = y2 - cy1

            if mask_shape == "ellipse":
                # Elliptical mask
                yy, xx = np.ogrid[:crop_h, :crop_w]
                ecx = (rx1 + rx2) / 2.0
                ecy = (ry1 + ry2) / 2.0
                erx = (rx2 - rx1) / 2.0
                ery = (ry2 - ry1) / 2.0
                if erx > 0 and ery > 0:
                    dist = ((xx - ecx) / erx) ** 2 + ((yy - ecy) / ery) ** 2
                    mask[dist <= 1.0] = 1.0
            else:
                # Rectangle mask
                mask[ry1:ry2, rx1:rx2] = 1.0

            # Feather the mask
            if mask_feather > 0:
                mask = self._feather_mask(mask, mask_feather)

            mask_tensor = torch.from_numpy(mask).unsqueeze(0).float()
            masks.append(mask_tensor)

            # Draw guide overlay on preview
            color = guide_colors[idx]
            alpha = 0.25
            for py in range(y1, y2):
                for px in range(x1, x2):
                    if mask_shape == "ellipse":
                        ecx_full = (x1 + x2) / 2.0
                        ecy_full = (y1 + y2) / 2.0
                        erx_full = (x2 - x1) / 2.0
                        ery_full = (y2 - y1) / 2.0
                        if erx_full > 0 and ery_full > 0:
                            d = ((px - ecx_full) / erx_full) ** 2 + ((py - ecy_full) / ery_full) ** 2
                            if d > 1.0:
                                continue
                    preview[py, px] = preview[py, px] * (1 - alpha) + color * alpha

            # Draw border on preview
            border_alpha = 0.7
            for px in range(x1, x2):
                for t in range(2):
                    if y1 + t < h:
                        preview[y1 + t, px] = preview[y1 + t, px] * (1 - border_alpha) + color * border_alpha
                    if y2 - 1 - t >= 0:
                        preview[y2 - 1 - t, px] = preview[y2 - 1 - t, px] * (1 - border_alpha) + color * border_alpha
            for py in range(y1, y2):
                for t in range(2):
                    if x1 + t < w:
                        preview[py, x1 + t] = preview[py, x1 + t] * (1 - border_alpha) + color * border_alpha
                    if x2 - 1 - t >= 0:
                        preview[py, x2 - 1 - t] = preview[py, x2 - 1 - t] * (1 - border_alpha) + color * border_alpha

            prompts_data.append({
                "region": idx + 1,
                "prompt": region["prompt"],
                "bounds_px": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "crop_bounds_px": {"x1": cx1, "y1": cy1, "x2": cx2, "y2": cy2},
            })

        preview_tensor = torch.from_numpy(np.clip(preview, 0, 1).astype(np.float32)).unsqueeze(0)

        return (
            crops[0], masks[0],
            crops[1], masks[1],
            crops[2], masks[2],
            crops[3], masks[3],
            preview_tensor,
            json.dumps(prompts_data, indent=2),
        )

    @staticmethod
    def _feather_mask(mask, radius):
        """Simple box-blur feathering."""
        from functools import reduce
        import numpy as np
        kernel_size = radius * 2 + 1
        result = mask.copy()

        # Horizontal pass
        cumsum = np.cumsum(result, axis=1)
        padded = np.pad(cumsum, ((0, 0), (kernel_size, 0)), mode='edge')
        result = (padded[:, kernel_size:] - padded[:, :-kernel_size]) / kernel_size

        # Vertical pass
        cumsum = np.cumsum(result, axis=0)
        padded = np.pad(cumsum, ((kernel_size, 0), (0, 0)), mode='edge')
        result = (padded[kernel_size:, :] - padded[:-kernel_size, :]) / kernel_size

        return np.clip(result, 0.0, 1.0)
