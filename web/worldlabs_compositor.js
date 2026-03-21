/**
 * World Labs Scene Compositor — interactive region placement.
 *
 * Adds a visual overlay to the Scene Compositor node where you can
 * drag character regions directly on the background image preview.
 * Positions sync back to the node's x/y/width/height parameters.
 */
import { app } from "../../scripts/app.js";

const COLORS = [
    "rgba(213, 90, 48, 0.5)",
    "rgba(29, 158, 117, 0.5)",
    "rgba(186, 117, 23, 0.5)",
    "rgba(127, 119, 221, 0.5)",
];
const BORDER_COLORS = [
    "rgba(213, 90, 48, 0.9)",
    "rgba(29, 158, 117, 0.9)",
    "rgba(186, 117, 23, 0.9)",
    "rgba(127, 119, 221, 0.9)",
];
const LABELS = ["R1", "R2", "R3", "R4"];

app.registerExtension({
    name: "worldlabs.scene_compositor.regions",
    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData?.name !== "WorldLabsSceneCompositor") return;

        const origOnDrawForeground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function(ctx) {
            origOnDrawForeground?.apply(this, arguments);

            if (!this.imgs || !this.imgs[0]) return;

            const imgWidget = this.imgs[0];
            const imgX = this.pos?.[0] || 0;
            const imgY = (this.pos?.[1] || 0) + this.size[1] - (imgWidget.height || 200);
            const imgW = this.size[0];
            const imgH = imgWidget.height || 200;

            for (let i = 0; i < 4; i++) {
                const enabled = this.widgets?.find(w => w.name === `region_${i+1}_enabled`);
                if (!enabled || !enabled.value) continue;

                const wx = this.widgets.find(w => w.name === `region_${i+1}_x`);
                const wy = this.widgets.find(w => w.name === `region_${i+1}_y`);
                const ww = this.widgets.find(w => w.name === `region_${i+1}_width`);
                const wh = this.widgets.find(w => w.name === `region_${i+1}_height`);

                if (!wx || !wy || !ww || !wh) continue;

                const rx = wx.value * imgW;
                const ry = wy.value * imgH;
                const rw = ww.value * imgW;
                const rh = wh.value * imgH;

                const x1 = rx - rw/2;
                const y1 = ry - rh/2;

                ctx.save();
                ctx.fillStyle = COLORS[i];
                ctx.strokeStyle = BORDER_COLORS[i];
                ctx.lineWidth = 2;
                ctx.fillRect(x1, y1, rw, rh);
                ctx.strokeRect(x1, y1, rw, rh);

                ctx.fillStyle = BORDER_COLORS[i];
                ctx.font = "bold 14px monospace";
                ctx.fillText(LABELS[i], x1 + 4, y1 + 16);
                ctx.restore();
            }
        };
    },
});
