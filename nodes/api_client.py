"""
World Labs Marble API client — shared by all nodes.
Handles authentication, generation requests, polling, and asset downloads.
"""

import json
import time
import urllib.request
import urllib.error
import urllib.parse
import ssl
import base64
import io
import os

API_BASE = "https://api.worldlabs.ai"

# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _headers(api_key: str, content_type: str = "application/json") -> dict:
    h = {"WLT-Api-Key": api_key}
    if content_type:
        h["Content-Type"] = content_type
    return h


def _request(method: str, url: str, api_key: str, body: dict | None = None) -> dict:
    """Fire an HTTP request and return parsed JSON."""
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(
        url,
        data=data,
        headers=_headers(api_key),
        method=method,
    )
    # Allow self-signed certs in dev environments
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"World Labs API error {exc.code}: {error_body}"
        ) from exc


def _download_bytes(url: str) -> bytes:
    """Download raw bytes from a URL (for assets)."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, context=ctx, timeout=300) as resp:
        return resp.read()


# ---------------------------------------------------------------------------
# Public API wrappers
# ---------------------------------------------------------------------------

def generate_world(
    api_key: str,
    world_prompt: dict,
    display_name: str = "",
    model: str = "Marble 0.1-plus",
    seed: int | None = None,
    tags: list[str] | None = None,
) -> dict:
    """
    POST /marble/v1/worlds:generate
    Returns the Operation object (operation_id, done, etc.)
    """
    payload: dict = {"world_prompt": world_prompt, "model": model}
    if display_name:
        payload["display_name"] = display_name
    if seed is not None and seed >= 0:
        payload["seed"] = seed
    if tags:
        payload["tags"] = tags
    return _request("POST", f"{API_BASE}/marble/v1/worlds:generate", api_key, payload)


def poll_operation(api_key: str, operation_id: str) -> dict:
    """
    GET /marble/v1/operations/{operation_id}
    Returns the Operation object.
    """
    url = f"{API_BASE}/marble/v1/operations/{urllib.parse.quote(operation_id)}"
    return _request("GET", url, api_key)


def poll_until_done(
    api_key: str,
    operation_id: str,
    interval: float = 10.0,
    timeout: float = 600.0,
) -> dict:
    """
    Poll until done==True or timeout.
    Returns the final Operation dict.
    """
    elapsed = 0.0
    while elapsed < timeout:
        op = poll_operation(api_key, operation_id)
        if op.get("done"):
            if op.get("error"):
                err = op["error"]
                raise RuntimeError(
                    f"World generation failed: {err.get('message', err)}"
                )
            return op
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError(
        f"World generation timed out after {timeout}s (operation {operation_id})"
    )


def get_world(api_key: str, world_id: str) -> dict:
    """GET /marble/v1/worlds/{world_id}"""
    url = f"{API_BASE}/marble/v1/worlds/{urllib.parse.quote(world_id)}"
    return _request("GET", url, api_key)


def download_panorama(pano_url: str) -> bytes:
    """Download the panorama (equirectangular 360°) image bytes."""
    return _download_bytes(pano_url)


def download_splat(splat_url: str) -> bytes:
    """Download a Gaussian Splat .spz file."""
    return _download_bytes(splat_url)


def prepare_upload(api_key: str, file_name: str, kind: str, extension: str) -> dict:
    """POST /marble/v1/media-assets:prepare_upload"""
    payload = {"file_name": file_name, "kind": kind, "extension": extension}
    return _request("POST", f"{API_BASE}/marble/v1/media-assets:prepare_upload", api_key, payload)


def upload_to_signed_url(upload_url: str, data: bytes, required_headers: dict | None = None):
    """PUT raw bytes to the signed upload URL."""
    req = urllib.request.Request(upload_url, data=data, method="PUT")
    if required_headers:
        for k, v in required_headers.items():
            req.add_header(k, v)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=300) as resp:
        return resp.status


def image_tensor_to_png_bytes(image_tensor) -> bytes:
    """Convert a ComfyUI IMAGE tensor [B,H,W,C] (float 0-1) → PNG bytes."""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Pillow is required. pip install Pillow")
    import numpy as np

    # Take first image in batch
    if len(image_tensor.shape) == 4:
        img_np = image_tensor[0].cpu().numpy()
    else:
        img_np = image_tensor.cpu().numpy()

    img_np = (img_np * 255).clip(0, 255).astype(np.uint8)
    img = Image.fromarray(img_np)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def png_bytes_to_tensor(png_data: bytes):
    """PNG bytes → ComfyUI IMAGE tensor [1,H,W,3] float32."""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Pillow is required.")
    import numpy as np
    import torch

    img = Image.open(io.BytesIO(png_data)).convert("RGB")
    arr = np.array(img).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)  # [1,H,W,3]
