/**
 * World Labs Embedded Viewer — renders 360° panoramas inside ComfyUI
 * as an interactive equirectangular viewer with mouse-drag orbit controls.
 *
 * Adds a "🌍 View" button to panorama/viewer nodes that opens
 * a full-screen overlay with the panorama rendered on a sphere.
 */
import { app } from "../../scripts/app.js";

const VIEWER_ID = "worldlabs-3d-viewer-overlay";

function createViewerOverlay() {
    // Reuse existing overlay if present
    let existing = document.getElementById(VIEWER_ID);
    if (existing) return existing;

    const overlay = document.createElement("div");
    overlay.id = VIEWER_ID;
    Object.assign(overlay.style, {
        position: "fixed",
        top: "0",
        left: "0",
        width: "100vw",
        height: "100vh",
        zIndex: "99999",
        background: "rgba(5, 5, 10, 0.97)",
        display: "none",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'SF Mono', 'Fira Code', monospace",
    });

    overlay.innerHTML = `
        <div id="wl-viewer-hud" style="
            position: absolute; top: 16px; left: 16px; z-index: 10;
            color: #6fefce; font-size: 13px; pointer-events: none;
        ">
            <div style="font-weight: 600; margin-bottom: 4px;">🌍 World Labs Panorama Viewer</div>
            <div style="font-size: 11px; color: #666;">Click & drag to orbit · Scroll to zoom · ESC to close</div>
        </div>
        <canvas id="wl-pano-canvas" style="width: 100%; height: 100%; cursor: grab;"></canvas>
        <div style="
            position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
            display: flex; gap: 8px; z-index: 10;
        ">
            <button id="wl-viewer-close" style="
                background: rgba(20,20,30,0.85); border: 1px solid rgba(111,239,206,0.3);
                color: #6fefce; padding: 8px 18px; font-size: 12px; cursor: pointer;
                border-radius: 6px; font-family: inherit; backdrop-filter: blur(10px);
            ">✕ Close</button>
            <button id="wl-viewer-reset" style="
                background: rgba(20,20,30,0.85); border: 1px solid rgba(111,239,206,0.3);
                color: #6fefce; padding: 8px 18px; font-size: 12px; cursor: pointer;
                border-radius: 6px; font-family: inherit; backdrop-filter: blur(10px);
            ">⟲ Reset View</button>
            <button id="wl-viewer-screenshot" style="
                background: rgba(20,20,30,0.85); border: 1px solid rgba(111,239,206,0.3);
                color: #6fefce; padding: 8px 18px; font-size: 12px; cursor: pointer;
                border-radius: 6px; font-family: inherit; backdrop-filter: blur(10px);
            ">📸 Screenshot</button>
        </div>
        <div id="wl-cam-readout" style="
            position: absolute; bottom: 16px; right: 16px;
            color: #444; font-size: 10px; letter-spacing: 0.5px;
        ">YAW: 0° PITCH: 0° FOV: 90°</div>
    `;

    document.body.appendChild(overlay);
    return overlay;
}

/**
 * Minimal WebGL equirectangular panorama renderer.
 * Renders the panorama on the inside of a sphere with orbit controls.
 */
class PanoViewer {
    constructor(canvas) {
        this.canvas = canvas;
        this.gl = canvas.getContext("webgl", { antialias: true, preserveDrawingBuffer: true });
        if (!this.gl) throw new Error("WebGL not available");

        this.yaw = 0;
        this.pitch = 0;
        this.fov = 90;
        this.dragging = false;
        this.lastX = 0;
        this.lastY = 0;
        this.texture = null;
        this.program = null;
        this.animFrame = null;

        this._initShaders();
        this._initGeometry();
        this._initEvents();
    }

    _initShaders() {
        const gl = this.gl;
        const vs = `
            attribute vec2 aPos;
            varying vec2 vUV;
            void main() {
                vUV = aPos * 0.5 + 0.5;
                gl_Position = vec4(aPos, 0.0, 1.0);
            }
        `;
        const fs = `
            precision highp float;
            varying vec2 vUV;
            uniform sampler2D uPano;
            uniform float uYaw;
            uniform float uPitch;
            uniform float uFov;
            uniform float uAspect;

            #define PI 3.14159265359

            mat3 rotY(float a) {
                float c = cos(a), s = sin(a);
                return mat3(c,0,s, 0,1,0, -s,0,c);
            }
            mat3 rotX(float a) {
                float c = cos(a), s = sin(a);
                return mat3(1,0,0, 0,c,-s, 0,s,c);
            }

            void main() {
                float fovRad = uFov * PI / 180.0;
                float f = 1.0 / tan(fovRad * 0.5);
                vec2 uv = vUV * 2.0 - 1.0;
                vec3 dir = normalize(vec3(uv.x * uAspect / f, uv.y / f, 1.0));
                dir = rotX(uPitch) * rotY(uYaw) * dir;

                float theta = atan(dir.x, dir.z);
                float phi = asin(clamp(dir.y, -1.0, 1.0));

                vec2 panoUV = vec2(
                    0.5 + theta / (2.0 * PI),
                    0.5 - phi / PI
                );

                gl_FragColor = texture2D(uPano, panoUV);
            }
        `;

        const compile = (type, src) => {
            const s = gl.createShader(type);
            gl.shaderSource(s, src);
            gl.compileShader(s);
            if (!gl.getShaderParameter(s, gl.COMPILE_STATUS))
                console.error(gl.getShaderInfoLog(s));
            return s;
        };

        this.program = gl.createProgram();
        gl.attachShader(this.program, compile(gl.VERTEX_SHADER, vs));
        gl.attachShader(this.program, compile(gl.FRAGMENT_SHADER, fs));
        gl.linkProgram(this.program);
        gl.useProgram(this.program);
    }

    _initGeometry() {
        const gl = this.gl;
        const buf = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buf);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
            -1,-1, 1,-1, -1,1, 1,1
        ]), gl.STATIC_DRAW);

        const loc = gl.getAttribLocation(this.program, "aPos");
        gl.enableVertexAttribArray(loc);
        gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    }

    _initEvents() {
        const c = this.canvas;
        c.addEventListener("mousedown", (e) => {
            this.dragging = true;
            this.lastX = e.clientX;
            this.lastY = e.clientY;
            c.style.cursor = "grabbing";
        });
        window.addEventListener("mousemove", (e) => {
            if (!this.dragging) return;
            const dx = e.clientX - this.lastX;
            const dy = e.clientY - this.lastY;
            this.yaw -= dx * 0.003;
            this.pitch += dy * 0.003;
            this.pitch = Math.max(-Math.PI * 0.49, Math.min(Math.PI * 0.49, this.pitch));
            this.lastX = e.clientX;
            this.lastY = e.clientY;
        });
        window.addEventListener("mouseup", () => {
            this.dragging = false;
            c.style.cursor = "grab";
        });
        c.addEventListener("wheel", (e) => {
            this.fov += e.deltaY * 0.05;
            this.fov = Math.max(20, Math.min(150, this.fov));
            e.preventDefault();
        }, { passive: false });
    }

    loadImage(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => {
                const gl = this.gl;
                this.texture = gl.createTexture();
                gl.bindTexture(gl.TEXTURE_2D, this.texture);
                gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
                gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
                gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
                gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
                gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
                resolve();
            };
            img.onerror = reject;
            img.src = url;
        });
    }

    render() {
        const gl = this.gl;
        const c = this.canvas;
        c.width = c.clientWidth * (window.devicePixelRatio || 1);
        c.height = c.clientHeight * (window.devicePixelRatio || 1);
        gl.viewport(0, 0, c.width, c.height);

        gl.useProgram(this.program);
        gl.uniform1f(gl.getUniformLocation(this.program, "uYaw"), this.yaw);
        gl.uniform1f(gl.getUniformLocation(this.program, "uPitch"), this.pitch);
        gl.uniform1f(gl.getUniformLocation(this.program, "uFov"), this.fov);
        gl.uniform1f(gl.getUniformLocation(this.program, "uAspect"), c.width / c.height);

        if (this.texture) {
            gl.activeTexture(gl.TEXTURE0);
            gl.bindTexture(gl.TEXTURE_2D, this.texture);
            gl.uniform1i(gl.getUniformLocation(this.program, "uPano"), 0);
        }

        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

        // Update camera readout
        const readout = document.getElementById("wl-cam-readout");
        if (readout) {
            const yDeg = ((this.yaw * 180 / Math.PI) % 360).toFixed(1);
            const pDeg = (this.pitch * 180 / Math.PI).toFixed(1);
            readout.textContent = `YAW: ${yDeg}° PITCH: ${pDeg}° FOV: ${this.fov.toFixed(0)}°`;
        }

        this.animFrame = requestAnimationFrame(() => this.render());
    }

    reset() {
        this.yaw = 0;
        this.pitch = 0;
        this.fov = 90;
    }

    destroy() {
        if (this.animFrame) cancelAnimationFrame(this.animFrame);
        if (this.texture) this.gl.deleteTexture(this.texture);
        if (this.program) this.gl.deleteProgram(this.program);
    }

    screenshot() {
        const dataURL = this.canvas.toDataURL("image/png");
        const a = document.createElement("a");
        a.href = dataURL;
        a.download = `worldlabs_shot_${Date.now()}.png`;
        a.click();
    }
}

// ── Viewer state ──
let activeViewer = null;

function openPanoViewer(panoUrl) {
    const overlay = createViewerOverlay();
    overlay.style.display = "flex";

    const canvas = document.getElementById("wl-pano-canvas");

    if (activeViewer) activeViewer.destroy();
    activeViewer = new PanoViewer(canvas);

    activeViewer.loadImage(panoUrl).then(() => {
        activeViewer.render();
    }).catch(err => {
        console.error("Failed to load panorama:", err);
        alert("Failed to load panorama image. Check the URL and CORS settings.");
        closePanoViewer();
    });

    // Wire buttons
    document.getElementById("wl-viewer-close").onclick = closePanoViewer;
    document.getElementById("wl-viewer-reset").onclick = () => activeViewer?.reset();
    document.getElementById("wl-viewer-screenshot").onclick = () => activeViewer?.screenshot();

    // ESC to close
    const escHandler = (e) => {
        if (e.key === "Escape") {
            closePanoViewer();
            window.removeEventListener("keydown", escHandler);
        }
    };
    window.addEventListener("keydown", escHandler);
}

function closePanoViewer() {
    const overlay = document.getElementById(VIEWER_ID);
    if (overlay) overlay.style.display = "none";
    if (activeViewer) {
        activeViewer.destroy();
        activeViewer = null;
    }
}

// ── Register ComfyUI extension ──
app.registerExtension({
    name: "worldlabs.viewer.embedded",
    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        // Add viewer button to panorama and viewer nodes
        const viewerNodes = [
            "WorldLabsDownloadPano",
            "WorldLabsHTMLViewer",
            "WorldLabsVirtualCamera",
        ];
        if (!viewerNodes.includes(nodeData?.name)) return;

        const origOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (output) {
            origOnExecuted?.apply(this, arguments);

            // Store pano URL from output for viewer button
            if (output?.pano_url?.[0]) {
                this._wl_pano_url = output.pano_url[0];
            }
        };

        const origGetExtraMenuOptions = nodeType.prototype.getExtraMenuOptions;
        nodeType.prototype.getExtraMenuOptions = function (_, options) {
            origGetExtraMenuOptions?.apply(this, arguments);

            options.unshift({
                content: "🌍 Open 360° Viewer",
                callback: () => {
                    const url = this._wl_pano_url;
                    if (url) {
                        openPanoViewer(url);
                    } else {
                        alert("No panorama URL available. Run the node first.");
                    }
                },
            });
        };
    },
});

// Also expose globally so nodes can trigger it
window.worldLabsOpenViewer = openPanoViewer;
