"""
ComfyUI World Labs Node Pack — 3D worlds + filmmaker compositing for AI films.
"""

from .nodes.api_key_node import WorldLabsAPIKey
from .nodes.generate_text_node import WorldLabsGenerateText
from .nodes.generate_image_node import WorldLabsGenerateImage
from .nodes.generate_multi_image_node import WorldLabsGenerateMultiImage
from .nodes.poll_node import WorldLabsPollOperation
from .nodes.download_pano_node import WorldLabsDownloadPano
from .nodes.download_splat_node import WorldLabsDownloadSplat
from .nodes.world_info_node import WorldLabsWorldInfo
from .nodes.storyboard_batch_node import WorldLabsStoryboardBatch
from .nodes.virtual_camera_node import WorldLabsVirtualCamera
from .nodes.html_viewer_node import WorldLabsHTMLViewer
from .nodes.scene_compositor_node import WorldLabsSceneCompositor
from .nodes.composite_layers_node import WorldLabsCompositeLayers

NODE_CLASS_MAPPINGS = {
    "WorldLabsAPIKey": WorldLabsAPIKey,
    "WorldLabsGenerateText": WorldLabsGenerateText,
    "WorldLabsGenerateImage": WorldLabsGenerateImage,
    "WorldLabsGenerateMultiImage": WorldLabsGenerateMultiImage,
    "WorldLabsPollOperation": WorldLabsPollOperation,
    "WorldLabsDownloadPano": WorldLabsDownloadPano,
    "WorldLabsDownloadSplat": WorldLabsDownloadSplat,
    "WorldLabsWorldInfo": WorldLabsWorldInfo,
    "WorldLabsStoryboardBatch": WorldLabsStoryboardBatch,
    "WorldLabsVirtualCamera": WorldLabsVirtualCamera,
    "WorldLabsHTMLViewer": WorldLabsHTMLViewer,
    "WorldLabsSceneCompositor": WorldLabsSceneCompositor,
    "WorldLabsCompositeLayers": WorldLabsCompositeLayers,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WorldLabsAPIKey": "World Labs API Key",
    "WorldLabsGenerateText": "Generate World (Text)",
    "WorldLabsGenerateImage": "Generate World (Image)",
    "WorldLabsGenerateMultiImage": "Generate World (Multi-Image)",
    "WorldLabsPollOperation": "Poll Operation",
    "WorldLabsDownloadPano": "Download Panorama (360)",
    "WorldLabsDownloadSplat": "Download Gaussian Splat",
    "WorldLabsWorldInfo": "World Info",
    "WorldLabsStoryboardBatch": "Storyboard Batch Generator",
    "WorldLabsVirtualCamera": "Virtual Camera (360 to Shot)",
    "WorldLabsHTMLViewer": "HTML Fly-Through Viewer",
    "WorldLabsSceneCompositor": "Scene Compositor (Character Regions)",
    "WorldLabsCompositeLayers": "Composite Layers",
}

WEB_DIRECTORY = "./web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
