"""
Standalone HTML Viewer Generator.
Creates a self-contained HTML file that lets you fly through the 3D Gaussian
splat world in any browser. Includes WASD/mouse controls, camera position
export, and screenshot capability — all offline, no server needed.
"""

import os
import json


class WorldLabsHTMLViewer:
    """
    Generate a standalone HTML file with an interactive 3D viewer
    for your World Labs Gaussian splat world.

    Opens in any modern browser. Controls:
      WASD / Arrow keys = move
      Mouse drag = look around
      Scroll = zoom
      P = print camera position to console
      S = screenshot

    Also embeds the panorama as a fallback skybox.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("WL_API_KEY",),
            },
            "optional": {
                "operation": ("WL_OPERATION",),
                "world_id": ("STRING", {"default": ""}),
                "viewer_title": ("STRING", {"default": "World Labs Scene Viewer"}),
                "output_directory": ("STRING", {"default": "output/worldlabs_viewers"}),
                "splat_resolution": (["500k", "100k", "full_res"], {
                    "default": "500k",
                    "tooltip": "500k is a good balance of quality vs load time for browsers",
                }),
                "include_camera_export": ("BOOLEAN", {"default": True,
                    "tooltip": "Add button to export camera position as JSON for shot planning"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("html_file_path", "marble_viewer_url")
    FUNCTION = "generate_viewer"
    CATEGORY = "🌍 World Labs"
    OUTPUT_NODE = True

    def generate_viewer(self, api_key,
                        operation=None, world_id="",
                        viewer_title="World Labs Scene Viewer",
                        output_directory="output/worldlabs_viewers",
                        splat_resolution="500k",
                        include_camera_export=True):

        from . import api_client

        resolved_id = world_id.strip()
        world = None

        if operation:
            resp = operation.get("response") or {}
            if resp:
                world = resp
                resolved_id = resolved_id or resp.get("id") or resp.get("world_id") or ""
            if not resolved_id:
                meta = operation.get("metadata") or {}
                resolved_id = meta.get("world_id", "")

        if not world and resolved_id:
            data = api_client.get_world(api_key, resolved_id)
            world = data.get("world", data)

        if not world:
            raise RuntimeError("No world data. Connect a Generate/Poll node or provide world_id.")

        assets = world.get("assets") or {}
        splats = assets.get("splats") or {}
        spz_urls = splats.get("spz_urls") or {}
        imagery = assets.get("imagery") or {}
        pano_url = imagery.get("pano_url", "")
        marble_url = world.get("world_marble_url", "")
        caption = assets.get("caption", "")

        splat_url = spz_urls.get(splat_resolution) or spz_urls.get("500k") or spz_urls.get("100k") or ""

        html = self._build_html(
            title=viewer_title,
            splat_url=splat_url,
            pano_url=pano_url,
            marble_url=marble_url,
            caption=caption,
            world_id=resolved_id,
            include_camera_export=include_camera_export,
        )

        os.makedirs(output_directory, exist_ok=True)
        fname = f"viewer_{resolved_id or 'unknown'}.html"
        path = os.path.join(output_directory, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        return (path, marble_url)

    def _build_html(self, title, splat_url, pano_url, marble_url,
                    caption, world_id, include_camera_export):

        camera_export_js = ""
        camera_export_ui = ""
        if include_camera_export:
            camera_export_js = """
            function exportCamera() {
                const cam = viewer.getCamera ? viewer.getCamera() : null;
                const data = {
                    world_id: WORLD_ID,
                    timestamp: new Date().toISOString(),
                    camera: cam ? {
                        position: cam.position,
                        rotation: cam.rotation,
                        fov: cam.fov
                    } : { note: "Camera data not available from this renderer" },
                    note: "Use yaw/pitch/fov in ComfyUI Virtual Camera node"
                };
                const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = `camera_${WORLD_ID}_${Date.now()}.json`;
                a.click();
            }
            """
            camera_export_ui = '<button onclick="exportCamera()" class="btn">📷 Export Camera Position</button>'

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #0a0a0f;
    color: #e0e0e0;
    font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    overflow: hidden;
    height: 100vh;
  }}
  #viewer-container {{
    width: 100vw;
    height: 100vh;
    position: relative;
  }}
  #pano-fallback {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }}
  #splat-viewer {{
    width: 100%;
    height: 100%;
    border: none;
    display: none;
  }}
  .hud {{
    position: fixed;
    top: 16px;
    left: 16px;
    z-index: 100;
    display: flex;
    flex-direction: column;
    gap: 8px;
    pointer-events: none;
  }}
  .hud > * {{ pointer-events: auto; }}
  .hud-title {{
    font-size: 14px;
    font-weight: 600;
    color: #6fefce;
    text-shadow: 0 0 20px rgba(111, 239, 206, 0.3);
    letter-spacing: 0.5px;
  }}
  .hud-caption {{
    font-size: 11px;
    color: #888;
    max-width: 400px;
    line-height: 1.4;
  }}
  .controls {{
    position: fixed;
    bottom: 16px;
    left: 16px;
    z-index: 100;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .btn {{
    background: rgba(20, 20, 30, 0.85);
    border: 1px solid rgba(111, 239, 206, 0.3);
    color: #6fefce;
    padding: 8px 14px;
    font-size: 12px;
    font-family: inherit;
    cursor: pointer;
    border-radius: 6px;
    backdrop-filter: blur(10px);
    transition: all 0.2s;
  }}
  .btn:hover {{
    background: rgba(111, 239, 206, 0.15);
    border-color: #6fefce;
  }}
  .info-panel {{
    position: fixed;
    top: 16px;
    right: 16px;
    z-index: 100;
    background: rgba(10, 10, 15, 0.9);
    border: 1px solid rgba(111, 239, 206, 0.2);
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 11px;
    backdrop-filter: blur(10px);
    display: none;
  }}
  .info-panel.show {{ display: block; }}
  .info-panel h3 {{
    color: #6fefce;
    margin-bottom: 8px;
    font-size: 12px;
  }}
  .info-panel p {{
    color: #999;
    margin: 4px 0;
    line-height: 1.4;
  }}
  .info-panel a {{
    color: #6fefce;
    text-decoration: none;
  }}
  .info-panel a:hover {{ text-decoration: underline; }}
  .mode-label {{
    position: fixed;
    bottom: 16px;
    right: 16px;
    font-size: 10px;
    color: #444;
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  /* Panorama drag-to-look */
  #pano-fallback {{
    cursor: grab;
  }}
  #pano-fallback:active {{
    cursor: grabbing;
  }}
</style>
</head>
<body>

<div id="viewer-container">
  <img id="pano-fallback" src="{pano_url}" alt="360 Panorama" draggable="false" />
  <iframe id="splat-viewer" allowfullscreen></iframe>
</div>

<div class="hud">
  <div class="hud-title">🌍 {title}</div>
  <div class="hud-caption">{caption[:200]}</div>
</div>

<div class="controls">
  <button onclick="toggleMode()" class="btn" id="mode-btn">🎬 Load 3D Splat</button>
  <button onclick="openMarble()" class="btn">🔗 Open in Marble</button>
  {camera_export_ui}
  <button onclick="toggleInfo()" class="btn">ℹ️ Info</button>
  <button onclick="screenshotPano()" class="btn">📸 Screenshot</button>
</div>

<div class="info-panel" id="info-panel">
  <h3>World Info</h3>
  <p><strong>World ID:</strong> {world_id}</p>
  <p><strong>Splat:</strong> {splat_resolution_label(splat_url)}</p>
  <p><a href="{marble_url}" target="_blank">Open in Marble Viewer →</a></p>
  <p style="margin-top: 8px; color: #555;">
    <strong>Panorama controls:</strong> Click & drag to look around.<br>
    <strong>3D Splat:</strong> WASD to move, mouse to orbit.
  </p>
</div>

<div class="mode-label" id="mode-label">PANORAMA MODE</div>

<script>
const WORLD_ID = "{world_id}";
const MARBLE_URL = "{marble_url}";
const SPLAT_URL = "{splat_url}";
const PANO_URL = "{pano_url}";
let mode = "pano";
let viewer = null;

// ── Panorama drag-to-pan ──
const panoEl = document.getElementById('pano-fallback');
let isDragging = false, startX = 0, startY = 0, offsetX = 0, offsetY = 0;
let currentX = 0, currentY = 0;

panoEl.addEventListener('mousedown', (e) => {{
  isDragging = true;
  startX = e.clientX - currentX;
  startY = e.clientY - currentY;
}});

window.addEventListener('mousemove', (e) => {{
  if (!isDragging || mode !== 'pano') return;
  currentX = e.clientX - startX;
  currentY = Math.max(Math.min(e.clientY - startY, 300), -300);
  panoEl.style.transform = `translate(${{currentX}}px, ${{currentY}}px) scale(1.5)`;
}});

window.addEventListener('mouseup', () => {{ isDragging = false; }});

// Start zoomed in slightly to allow panning
panoEl.style.transform = 'scale(1.5)';
panoEl.style.transformOrigin = 'center center';

// ── Mode toggle ──
function toggleMode() {{
  const pano = document.getElementById('pano-fallback');
  const splat = document.getElementById('splat-viewer');
  const btn = document.getElementById('mode-btn');
  const label = document.getElementById('mode-label');

  if (mode === 'pano') {{
    if (MARBLE_URL) {{
      splat.src = MARBLE_URL;
      splat.style.display = 'block';
      pano.style.display = 'none';
      btn.textContent = '🖼️ Show Panorama';
      label.textContent = '3D SPLAT MODE';
      mode = 'splat';
    }} else {{
      alert('No 3D splat URL available for this world.');
    }}
  }} else {{
    splat.style.display = 'none';
    pano.style.display = 'block';
    btn.textContent = '🎬 Load 3D Splat';
    label.textContent = 'PANORAMA MODE';
    mode = 'pano';
  }}
}}

function openMarble() {{
  if (MARBLE_URL) window.open(MARBLE_URL, '_blank');
  else alert('No Marble URL available.');
}}

function toggleInfo() {{
  document.getElementById('info-panel').classList.toggle('show');
}}

function screenshotPano() {{
  if (mode === 'pano') {{
    const canvas = document.createElement('canvas');
    const img = document.getElementById('pano-fallback');
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    canvas.getContext('2d').drawImage(img, 0, 0);
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    a.download = `screenshot_${{WORLD_ID}}_${{Date.now()}}.png`;
    a.click();
  }} else {{
    alert('Screenshots in 3D mode: use your OS screenshot tool.');
  }}
}}

{camera_export_js}
</script>
</body>
</html>"""


def splat_resolution_label(url):
    if not url:
        return "N/A"
    if "full_res" in url:
        return "Full Resolution"
    if "500k" in url:
        return "500K"
    if "100k" in url:
        return "100K"
    return "Unknown"
