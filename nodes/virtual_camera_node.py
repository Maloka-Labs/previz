"""
Virtual Camera Node — the cinematographer's tool.
Takes a 360° equirectangular panorama and extracts a perspective-correct
"camera shot" at a given yaw, pitch, and field of view.

Use this to frame shots from your World Labs environments without
needing any 3D software. Chain multiple instances for a full shot list
from a single generated world.
"""

import math


class WorldLabsVirtualCamera:
    """
    Extract a perspective camera view from a 360° equirectangular panorama.
    Simulates pointing a virtual camera inside the 3D world.

    Outputs a standard ComfyUI IMAGE you can send to:
      • img2vid (Kling, Runway, SVD) for animated shots
      • img2img for style transfer
      • Save Image for storyboard frames
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "panorama": ("IMAGE",),
                "yaw": ("FLOAT", {
                    "default": 0.0, "min": -180.0, "max": 180.0, "step": 1.0,
                    "tooltip": "Horizontal rotation in degrees. 0=center, -180/180=behind",
                }),
                "pitch": ("FLOAT", {
                    "default": 0.0, "min": -90.0, "max": 90.0, "step": 1.0,
                    "tooltip": "Vertical tilt in degrees. Positive=up, negative=down",
                }),
                "fov": ("FLOAT", {
                    "default": 90.0, "min": 20.0, "max": 160.0, "step": 1.0,
                    "tooltip": "Field of view in degrees. 50=telephoto, 90=normal, 120=wide",
                }),
                "output_width": ("INT", {
                    "default": 1920, "min": 256, "max": 4096, "step": 64,
                }),
                "output_height": ("INT", {
                    "default": 1080, "min": 256, "max": 4096, "step": 64,
                }),
            },
            "optional": {
                "roll": ("FLOAT", {
                    "default": 0.0, "min": -180.0, "max": 180.0, "step": 1.0,
                    "tooltip": "Camera roll (Dutch angle) in degrees",
                }),
                "interpolation": (["bilinear", "nearest"], {"default": "bilinear"}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("camera_shot", "camera_info")
    FUNCTION = "extract_shot"
    CATEGORY = "🌍 World Labs"

    def extract_shot(self, panorama, yaw, pitch, fov,
                     output_width, output_height,
                     roll=0.0, interpolation="bilinear"):
        import torch
        import numpy as np

        # Get panorama as numpy [H, W, 3]
        if len(panorama.shape) == 4:
            pano_np = panorama[0].cpu().numpy()
        else:
            pano_np = panorama.cpu().numpy()

        pano_h, pano_w, _ = pano_np.shape

        # Convert angles to radians
        yaw_rad = math.radians(yaw)
        pitch_rad = math.radians(pitch)
        roll_rad = math.radians(roll)
        fov_rad = math.radians(fov)

        # Build rotation matrix (yaw → pitch → roll)
        # Yaw (around Y axis)
        Ry = np.array([
            [math.cos(yaw_rad),  0, math.sin(yaw_rad)],
            [0,                  1, 0                 ],
            [-math.sin(yaw_rad), 0, math.cos(yaw_rad)],
        ])
        # Pitch (around X axis)
        Rx = np.array([
            [1, 0,                   0                  ],
            [0, math.cos(pitch_rad), -math.sin(pitch_rad)],
            [0, math.sin(pitch_rad), math.cos(pitch_rad) ],
        ])
        # Roll (around Z axis)
        Rz = np.array([
            [math.cos(roll_rad), -math.sin(roll_rad), 0],
            [math.sin(roll_rad),  math.cos(roll_rad), 0],
            [0,                   0,                   1],
        ])

        R = Ry @ Rx @ Rz

        # Generate ray directions for each pixel in the output
        f = output_width / (2.0 * math.tan(fov_rad / 2.0))
        cx = output_width / 2.0
        cy = output_height / 2.0

        u = np.arange(output_width, dtype=np.float64)
        v = np.arange(output_height, dtype=np.float64)
        uu, vv = np.meshgrid(u, v)

        # Camera-space ray directions (looking along +Z)
        x = (uu - cx) / f
        y = -(vv - cy) / f  # flip Y (image coords vs world coords)
        z = np.ones_like(x)

        # Stack and normalize
        dirs = np.stack([x, y, z], axis=-1)  # [H, W, 3]
        norms = np.linalg.norm(dirs, axis=-1, keepdims=True)
        dirs = dirs / norms

        # Rotate rays to world space
        dirs_flat = dirs.reshape(-1, 3)
        world_dirs = (R @ dirs_flat.T).T  # [N, 3]
        world_dirs = world_dirs.reshape(output_height, output_width, 3)

        # Convert to spherical coordinates
        wx = world_dirs[..., 0]
        wy = world_dirs[..., 1]
        wz = world_dirs[..., 2]

        # theta = longitude [-pi, pi], phi = latitude [-pi/2, pi/2]
        theta = np.arctan2(wx, wz)  # yaw
        phi = np.arcsin(np.clip(wy, -1.0, 1.0))  # pitch

        # Map to equirectangular pixel coordinates
        map_x = ((theta / math.pi + 1.0) / 2.0 * pano_w).astype(np.float64)
        map_y = ((0.5 - phi / math.pi) * pano_h).astype(np.float64)

        # Wrap coordinates
        map_x = np.mod(map_x, pano_w)
        map_y = np.clip(map_y, 0, pano_h - 1)

        # Sample from panorama
        if interpolation == "bilinear":
            result = self._bilinear_sample(pano_np, map_x, map_y, output_height, output_width)
        else:
            ix = np.round(map_x).astype(int) % pano_w
            iy = np.clip(np.round(map_y).astype(int), 0, pano_h - 1)
            result = pano_np[iy, ix]

        # Convert to tensor [1, H, W, 3]
        result = np.clip(result, 0.0, 1.0).astype(np.float32)
        tensor = torch.from_numpy(result).unsqueeze(0)

        camera_info = (
            f"Yaw: {yaw}° | Pitch: {pitch}° | Roll: {roll}° | "
            f"FOV: {fov}° | Resolution: {output_width}x{output_height}"
        )

        return (tensor, camera_info)

    @staticmethod
    def _bilinear_sample(img, map_x, map_y, out_h, out_w):
        """Bilinear interpolation sampling from equirectangular image."""
        import numpy as np
        h, w, c = img.shape

        x0 = np.floor(map_x).astype(int)
        y0 = np.floor(map_y).astype(int)
        x1 = x0 + 1
        y1 = y0 + 1

        # Fractional parts
        fx = (map_x - x0).astype(np.float32)
        fy = (map_y - y0).astype(np.float32)

        # Wrap/clamp
        x0 = np.mod(x0, w)
        x1 = np.mod(x1, w)
        y0 = np.clip(y0, 0, h - 1)
        y1 = np.clip(y1, 0, h - 1)

        # Gather pixels
        p00 = img[y0, x0]  # [out_h, out_w, 3]
        p10 = img[y0, x1]
        p01 = img[y1, x0]
        p11 = img[y1, x1]

        fx = fx[..., np.newaxis]
        fy = fy[..., np.newaxis]

        result = (
            p00 * (1 - fx) * (1 - fy) +
            p10 * fx * (1 - fy) +
            p01 * (1 - fx) * fy +
            p11 * fx * fy
        )
        return result
