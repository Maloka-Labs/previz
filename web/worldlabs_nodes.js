import { app } from "../../scripts/app.js";

// World Labs node styling — earth-toned palette for spatial intelligence nodes
app.registerExtension({
    name: "worldlabs.nodes.style",
    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (!nodeData?.name?.startsWith("WorldLabs")) return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origOnNodeCreated?.apply(this, arguments);

            // Color scheme: deep teal bg with warm accent
            this.color = "#1a3a3a";      // Dark teal body
            this.bgcolor = "#0d2626";    // Darker teal background
            this.shape = "box";

            // Title bar colors per node type
            const colors = {
                "WorldLabsAPIKey":           { title: "#2d5a5a" },
                "WorldLabsGenerateText":     { title: "#1e6b4f" },
                "WorldLabsGenerateImage":    { title: "#1e6b4f" },
                "WorldLabsPollOperation":    { title: "#3a5c3a" },
                "WorldLabsDownloadPano":     { title: "#5a6b1e" },
                "WorldLabsDownloadSplat":    { title: "#6b4f1e" },
                "WorldLabsWorldInfo":        { title: "#2d5a5a" },
                "WorldLabsStoryboardBatch":  { title: "#6b1e4f" },
            };

            const c = colors[nodeData.name];
            if (c) {
                this.color = c.title;
            }
        };
    },
});
