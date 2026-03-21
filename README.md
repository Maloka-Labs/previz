# ComfyUI World Labs — 3D World Generation for AI Filmmakers

Generate explorable 3D worlds, 360° panoramas, and Gaussian splats directly in ComfyUI using the **World Labs Marble API**. Built for **shot composition**, **storyboarding**, and **spatial previs** in AI film production.

---

## What This Does

Turn text prompts or AI-generated images into **navigable 3D environments** with a single node chain. Extract cinematic camera shots from the 360° panorama, batch-generate entire shot lists, and fly through your scenes in an embedded WebGL viewer — all without leaving ComfyUI.

### For AI Filmmakers

- **Concept to 3D World**: Describe a scene or feed a FLUX/SDXL image and get a full 3D environment
- **360 Panoramas**: Equirectangular images for lighting reference, environment maps, or video-gen input
- **Virtual Camera**: Frame specific shots from the 360 at any yaw/pitch/FOV — output goes straight to img2vid
- **Storyboard Batch**: Paste your entire shot list, get a batch of panoramas and a JSON manifest
- **3D Fly-Through**: Interactive WebGL viewer inside ComfyUI + standalone HTML files to share with your team

---

## Nodes (10 total)

| Node | Purpose |
|------|---------|
| **World Labs API Key** | Store your API credentials |
| **Generate World (Text)** | Text prompt → 3D world |
| **Generate World (Image)** | ComfyUI IMAGE → 3D world |
| **Poll Operation** | Check async generation status |
| **Download Panorama (360)** | Get equirectangular panorama as IMAGE |
| **Download Gaussian Splat** | Download .spz splat file |
| **World Info** | Extract URLs, caption, metadata |
| **Storyboard Batch Generator** | Shot list → batch of panoramas |
| **Virtual Camera (360 to Shot)** | Extract framed shots from 360 pano |
| **HTML Fly-Through Viewer** | Generate standalone 3D viewer HTML |

---

## Installation

### 1. Clone into ComfyUI custom nodes

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/YOUR_REPO/comfyui-worldlabs.git
```

### 2. Install dependencies

```bash
cd comfyui-worldlabs
pip install -r requirements.txt
```

### 3. Get a World Labs API Key

1. Sign in at platform.worldlabs.ai
2. Add payment method on the billing page
3. Generate an API key from the API keys page

### 4. Restart ComfyUI

Nodes appear under the **World Labs** category.

---

## Quick Start Workflows

### Text to 360 Panorama

```
[API Key] → [Generate World (Text)] → [Download Panorama] → [Preview Image]
```

### Image to Framed Shot (filmmaker pipeline)

```
[FLUX/SDXL] → [Generate World (Image)] → [Download Panorama] → [Virtual Camera] → [img2vid]
```

### Batch Storyboard

```
[API Key] → [Storyboard Batch Generator] → [Preview Image]
```

Paste your shot list (one scene per line). Get batch panoramas + JSON manifest.

### 3D Viewer

```
[Generate World] → [HTML Fly-Through Viewer]
```

Generates a standalone HTML you can open in any browser to fly through the scene.

---

## Virtual Camera — Shot Composition

| Parameter | Range | Use |
|-----------|-------|-----|
| **Yaw** | -180 to 180 | Pan left/right |
| **Pitch** | -90 to 90 | Tilt up/down |
| **FOV** | 20 to 160 | 20=telephoto, 90=normal, 120=wide |
| **Roll** | -180 to 180 | Dutch angle |
| **Resolution** | 256 to 4096 | Output frame size |

Chain multiple Virtual Camera nodes from the same panorama to build a complete shot list from one environment.

---

## Embedded 3D Viewer

Right-click any Download Panorama or HTML Viewer node after execution and select **Open 360 Viewer** for a full-screen interactive panorama inside ComfyUI.

- Click and drag to orbit
- Scroll to zoom FOV
- ESC to close
- Screenshot button saves current view

The camera readout shows Yaw/Pitch/FOV values you can copy into the Virtual Camera node.

---

## API Models

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| Marble 0.1-mini | ~30s | Draft | Iteration, storyboarding |
| Marble 0.1-plus | ~5 min | Best | Hero frames, client work |

---

## License

MIT
