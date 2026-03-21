"""
Composite Layers — blends generated character regions back onto the background plate.

Takes the background from Virtual Camera and up to 4 generated character layers
(each with its mask from Scene Compositor), and composites them in order.
"""



class WorldLabsCompositeLayers:
    """
    Final compositing step.

    Workflow:
      Virtual Camera → background
      Scene Compositor → region crops + masks
      (Your img2img/LoRA pipeline) → generated characters per region
      → Composite Layers → final frame with characters in scene

    Each layer is blended using its mask with optional opacity control.
    Layers composite in order: 1 (back) → 4 (front).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "background": ("IMAGE",),
            },
            "optional": {
                "layer_1_image": ("IMAGE",),
                "layer_1_mask": ("MASK",),
                "layer_1_opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
                "layer_1_x": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": "Horizontal center position (0=left, 1=right)"}),
                "layer_1_y": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": "Vertical center position (0=top, 1=bottom)"}),

                "layer_2_image": ("IMAGE",),
                "layer_2_mask": ("MASK",),
                "layer_2_opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
                "layer_2_x": ("FLOAT", {"default": 0.25, "min": 0.0, "max": 1.0, "step": 0.01}),
                "layer_2_y": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.01}),

                "layer_3_image": ("IMAGE",),
                "layer_3_mask": ("MASK",),
                "layer_3_opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
                "layer_3_x": ("FLOAT", {"default": 0.75, "min": 0.0, "max": 1.0, "step": 0.01}),
                "layer_3_y": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.01}),

                "layer_4_image": ("IMAGE",),
                "layer_4_mask": ("MASK",),
                "layer_4_opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
                "layer_4_x": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "layer_4_y": ("FLOAT", {"default": 0.4, "min": 0.0, "max": 1.0, "step": 0.01}),

                "color_match": ("BOOLEAN", {"default": True,
                    "tooltip": "Match layer color temperature to background region"}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("composited_frame",)
    FUNCTION = "composite"
    CATEGORY = "🌍 World Labs/Filmmaker"

    def composite(self, background,
                  layer_1_image=None, layer_1_mask=None, layer_1_opacity=1.0,
                  layer_1_x=0.5, layer_1_y=0.6,
                  layer_2_image=None, layer_2_mask=None, layer_2_opacity=1.0,
                  layer_2_x=0.25, layer_2_y=0.6,
                  layer_3_image=None, layer_3_mask=None, layer_3_opacity=1.0,
                  layer_3_x=0.75, layer_3_y=0.6,
                  layer_4_image=None, layer_4_mask=None, layer_4_opacity=1.0,
                  layer_4_x=0.5, layer_4_y=0.4,
                  color_match=True):

        import torch

        if len(background.shape) == 4:
            result = background[0].cpu().numpy().copy()
        else:
            result = background.cpu().numpy().copy()

        bg_h, bg_w, _ = result.shape

        layers = [
            (layer_1_image, layer_1_mask, layer_1_opacity, layer_1_x, layer_1_y),
            (layer_2_image, layer_2_mask, layer_2_opacity, layer_2_x, layer_2_y),
            (layer_3_image, layer_3_mask, layer_3_opacity, layer_3_x, layer_3_y),
            (layer_4_image, layer_4_mask, layer_4_opacity, layer_4_x, layer_4_y),
        ]

        for img_tensor, mask_tensor, opacity, lx, ly in layers:
            if img_tensor is None:
                continue

            # Get numpy arrays
            if len(img_tensor.shape) == 4:
                layer_img = img_tensor[0].cpu().numpy()
            else:
                layer_img = img_tensor.cpu().numpy()

            lh, lw, _ = layer_img.shape

            if mask_tensor is not None:
                if len(mask_tensor.shape) == 3:
                    mask = mask_tensor[0].cpu().numpy()
                else:
                    mask = mask_tensor.cpu().numpy()
                # Resize mask to match layer if needed
                if mask.shape[0] != lh or mask.shape[1] != lw:
                    mask = self._resize_mask(mask, lw, lh)
            else:
                mask = np.ones((lh, lw), dtype=np.float32)

            mask = mask * opacity

            # Optional colour matching
            if color_match:
                # Sample the background region at target position for colour reference
                cx = int(lx * bg_w)
                cy = int(ly * bg_h)
                sx1 = max(0, cx - lw // 2)
                sy1 = max(0, cy - lh // 2)
                sx2 = min(bg_w, sx1 + lw)
                sy2 = min(bg_h, sy1 + lh)

                bg_region = result[sy1:sy2, sx1:sx2]
                if bg_region.size > 0 and layer_img.size > 0:
                    layer_img = self._simple_color_match(layer_img, bg_region)

            # Compute placement bounds (centered on lx, ly)
            place_x1 = int(lx * bg_w - lw / 2)
            place_y1 = int(ly * bg_h - lh / 2)

            # Composite with clipping
            for dy in range(lh):
                by = place_y1 + dy
                if by < 0 or by >= bg_h:
                    continue
                for dx in range(lw):
                    bx = place_x1 + dx
                    if bx < 0 or bx >= bg_w:
                        continue
                    alpha = mask[dy, dx]
                    if alpha > 0.001:
                        result[by, bx] = result[by, bx] * (1 - alpha) + layer_img[dy, dx] * alpha

        result = np.clip(result, 0.0, 1.0).astype(np.float32)
        return (torch.from_numpy(result).unsqueeze(0),)

    @staticmethod
    def _resize_mask(mask, target_w, target_h):
        """Nearest-neighbour resize for masks."""
        src_h, src_w = mask.shape
        y_indices = (np.arange(target_h) * src_h / target_h).astype(int)
        x_indices = (np.arange(target_w) * src_w / target_w).astype(int)
        y_indices = np.clip(y_indices, 0, src_h - 1)
        x_indices = np.clip(x_indices, 0, src_w - 1)
        return mask[np.ix_(y_indices, x_indices)]

    @staticmethod
    def _simple_color_match(layer, bg_region):
        """
        Simple mean/std colour transfer.
        Shifts the layer's colour distribution to match the background region.
        """
        result = layer.copy()
        for ch in range(3):
            l_mean = np.mean(layer[:, :, ch])
            l_std = np.std(layer[:, :, ch]) + 1e-6
            b_mean = np.mean(bg_region[:, :, ch])
            b_std = np.std(bg_region[:, :, ch]) + 1e-6
            result[:, :, ch] = (layer[:, :, ch] - l_mean) * (b_std / l_std) + b_mean
        return np.clip(result, 0.0, 1.0)
