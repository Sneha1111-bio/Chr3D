(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/components/ui/pixelated-canvas.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "PixelatedCanvas",
    ()=>PixelatedCanvas
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
const PixelatedCanvas = ({ src, width = 400, height = 500, cellSize = 3, dotScale = 0.9, shape = "square", backgroundColor = "#000000", grayscale = false, className, responsive = false, dropoutStrength = 0.4, interactive = true, distortionStrength = 3, distortionRadius = 80, distortionMode = "swirl", followSpeed = 0.2, sampleAverage = true, tintColor = "#FFFFFF", tintStrength = 0.2, maxFps = 60, objectFit = "cover", jitterStrength = 4, jitterSpeed = 4, fadeOnLeave = true, fadeSpeed = 0.1 })=>{
    _s();
    const canvasRef = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].useRef(null);
    const samplesRef = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].useRef([]);
    const dimsRef = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].useRef(null);
    const targetMouseRef = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].useRef({
        x: -9999,
        y: -9999
    });
    const animMouseRef = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].useRef({
        x: -9999,
        y: -9999
    });
    const rafRef = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].useRef(null);
    const lastFrameRef = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].useRef(0);
    const pointerInsideRef = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].useRef(false);
    const activityRef = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].useRef(0);
    const activityTargetRef = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].useRef(0);
    __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].useEffect({
        "PixelatedCanvas.useEffect": ()=>{
            let isCancelled = false;
            const canvas = canvasRef.current;
            if (!canvas) return;
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.src = src;
            const compute = {
                "PixelatedCanvas.useEffect.compute": ()=>{
                    if (!canvas) return;
                    const dpr = ("TURBOPACK compile-time truthy", 1) ? window.devicePixelRatio || 1 : "TURBOPACK unreachable";
                    const displayWidth = width ?? img.naturalWidth;
                    const displayHeight = height ?? img.naturalHeight;
                    canvas.width = Math.max(1, Math.floor(displayWidth * dpr));
                    canvas.height = Math.max(1, Math.floor(displayHeight * dpr));
                    canvas.style.width = `${displayWidth}px`;
                    canvas.style.height = `${displayHeight}px`;
                    const ctx = canvas.getContext("2d");
                    if (!ctx) return;
                    ctx.resetTransform();
                    ctx.scale(dpr, dpr);
                    if (backgroundColor) {
                        ctx.fillStyle = backgroundColor;
                        ctx.fillRect(0, 0, displayWidth, displayHeight);
                    } else {
                        ctx.clearRect(0, 0, displayWidth, displayHeight);
                    }
                    const offscreen = document.createElement("canvas");
                    offscreen.width = Math.max(1, Math.floor(displayWidth));
                    offscreen.height = Math.max(1, Math.floor(displayHeight));
                    const off = offscreen.getContext("2d");
                    if (!off) return;
                    const iw = img.naturalWidth || displayWidth;
                    const ih = img.naturalHeight || displayHeight;
                    let dw = displayWidth;
                    let dh = displayHeight;
                    let dx = 0;
                    let dy = 0;
                    if (objectFit === "cover") {
                        const scale = Math.max(displayWidth / iw, displayHeight / ih);
                        dw = Math.ceil(iw * scale);
                        dh = Math.ceil(ih * scale);
                        dx = Math.floor((displayWidth - dw) / 2);
                        dy = Math.floor((displayHeight - dh) / 2);
                    } else if (objectFit === "contain") {
                        const scale = Math.min(displayWidth / iw, displayHeight / ih);
                        dw = Math.ceil(iw * scale);
                        dh = Math.ceil(ih * scale);
                        dx = Math.floor((displayWidth - dw) / 2);
                        dy = Math.floor((displayHeight - dh) / 2);
                    } else if (objectFit === "fill") {
                        dw = displayWidth;
                        dh = displayHeight;
                    } else {
                        dw = iw;
                        dh = ih;
                        dx = Math.floor((displayWidth - dw) / 2);
                        dy = Math.floor((displayHeight - dh) / 2);
                    }
                    off.drawImage(img, dx, dy, dw, dh);
                    let imageData;
                    try {
                        imageData = off.getImageData(0, 0, offscreen.width, offscreen.height);
                    } catch  {
                        ctx.drawImage(img, 0, 0, displayWidth, displayHeight);
                        return;
                    }
                    const data = imageData.data;
                    const stride = offscreen.width * 4;
                    const effectiveDotSize = Math.max(1, Math.floor(cellSize * dotScale));
                    dimsRef.current = {
                        width: displayWidth,
                        height: displayHeight,
                        dot: effectiveDotSize
                    };
                    const luminanceAt = {
                        "PixelatedCanvas.useEffect.compute.luminanceAt": (px, py)=>{
                            const ix = Math.max(0, Math.min(offscreen.width - 1, px));
                            const iy = Math.max(0, Math.min(offscreen.height - 1, py));
                            const i = iy * stride + ix * 4;
                            const rr = data[i];
                            const gg = data[i + 1];
                            const bb = data[i + 2];
                            return 0.2126 * rr + 0.7152 * gg + 0.0722 * bb;
                        }
                    }["PixelatedCanvas.useEffect.compute.luminanceAt"];
                    const hash2D = {
                        "PixelatedCanvas.useEffect.compute.hash2D": (ix, iy)=>{
                            const s = Math.sin(ix * 12.9898 + iy * 78.233) * 43758.5453123;
                            return s - Math.floor(s);
                        }
                    }["PixelatedCanvas.useEffect.compute.hash2D"];
                    const samples = [];
                    let tintRGB = null;
                    if (tintColor && tintStrength > 0) {
                        const parse = {
                            "PixelatedCanvas.useEffect.compute.parse": (c)=>{
                                if (c.startsWith("#")) {
                                    const hex = c.slice(1);
                                    if (hex.length === 3) {
                                        const r = parseInt(hex[0] + hex[0], 16);
                                        const g = parseInt(hex[1] + hex[1], 16);
                                        const b = parseInt(hex[2] + hex[2], 16);
                                        return [
                                            r,
                                            g,
                                            b
                                        ];
                                    }
                                    const r = parseInt(hex.slice(0, 2), 16);
                                    const g = parseInt(hex.slice(2, 4), 16);
                                    const b = parseInt(hex.slice(4, 6), 16);
                                    return [
                                        r,
                                        g,
                                        b
                                    ];
                                }
                                const m = c.match(/rgb\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)\)/i);
                                if (m) return [
                                    parseInt(m[1], 10),
                                    parseInt(m[2], 10),
                                    parseInt(m[3], 10)
                                ];
                                return null;
                            }
                        }["PixelatedCanvas.useEffect.compute.parse"];
                        tintRGB = parse(tintColor);
                    }
                    for(let y = 0; y < offscreen.height; y += cellSize){
                        const cy = Math.min(offscreen.height - 1, y + Math.floor(cellSize / 2));
                        for(let x = 0; x < offscreen.width; x += cellSize){
                            const cx = Math.min(offscreen.width - 1, x + Math.floor(cellSize / 2));
                            let r = 0;
                            let g = 0;
                            let b = 0;
                            let a = 0;
                            if (!sampleAverage) {
                                const idx = cy * stride + cx * 4;
                                r = data[idx];
                                g = data[idx + 1];
                                b = data[idx + 2];
                                a = data[idx + 3] / 255;
                            } else {
                                let count = 0;
                                for(let oy = -1; oy <= 1; oy++){
                                    for(let ox = -1; ox <= 1; ox++){
                                        const sx = Math.max(0, Math.min(offscreen.width - 1, cx + ox));
                                        const sy = Math.max(0, Math.min(offscreen.height - 1, cy + oy));
                                        const sIdx = sy * stride + sx * 4;
                                        r += data[sIdx];
                                        g += data[sIdx + 1];
                                        b += data[sIdx + 2];
                                        a += data[sIdx + 3] / 255;
                                        count++;
                                    }
                                }
                                r = Math.round(r / count);
                                g = Math.round(g / count);
                                b = Math.round(b / count);
                                a = a / count;
                            }
                            if (grayscale) {
                                const L = Math.round(0.2126 * r + 0.7152 * g + 0.0722 * b);
                                r = L;
                                g = L;
                                b = L;
                            } else if (tintRGB && tintStrength > 0) {
                                const k = Math.max(0, Math.min(1, tintStrength));
                                r = Math.round(r * (1 - k) + tintRGB[0] * k);
                                g = Math.round(g * (1 - k) + tintRGB[1] * k);
                                b = Math.round(b * (1 - k) + tintRGB[2] * k);
                            }
                            const Lc = luminanceAt(cx, cy);
                            const Lx1 = luminanceAt(cx - 1, cy);
                            const Lx2 = luminanceAt(cx + 1, cy);
                            const Ly1 = luminanceAt(cx, cy - 1);
                            const Ly2 = luminanceAt(cx, cy + 1);
                            const grad = Math.abs(Lx2 - Lx1) + Math.abs(Ly2 - Ly1) + Math.abs(Lc - (Lx1 + Lx2 + Ly1 + Ly2) / 4);
                            const gradientNorm = Math.max(0, Math.min(1, grad / 255));
                            const dropoutProb = Math.max(0, Math.min(1, (1 - gradientNorm) * dropoutStrength));
                            const drop = hash2D(cx, cy) < dropoutProb;
                            const seed = hash2D(cx, cy);
                            samples.push({
                                x,
                                y,
                                r,
                                g,
                                b,
                                a,
                                drop,
                                seed
                            });
                        }
                    }
                    samplesRef.current = samples;
                }
            }["PixelatedCanvas.useEffect.compute"];
            img.onload = ({
                "PixelatedCanvas.useEffect": ()=>{
                    if (isCancelled) return;
                    compute();
                    const canvasEl = canvasRef.current;
                    if (!canvasEl) return;
                    if (!interactive) {
                        const ctx = canvasEl.getContext("2d");
                        const dims = dimsRef.current;
                        const samples = samplesRef.current;
                        if (!ctx || !dims || !samples) return;
                        if (backgroundColor) {
                            ctx.fillStyle = backgroundColor;
                            ctx.fillRect(0, 0, dims.width, dims.height);
                        } else {
                            ctx.clearRect(0, 0, dims.width, dims.height);
                        }
                        for (const s of samples){
                            if (s.drop || s.a <= 0) continue;
                            ctx.globalAlpha = s.a;
                            ctx.fillStyle = `rgb(${s.r}, ${s.g}, ${s.b})`;
                            if (shape === "circle") {
                                const radius = dims.dot / 2;
                                ctx.beginPath();
                                ctx.arc(s.x + cellSize / 2, s.y + cellSize / 2, radius, 0, Math.PI * 2);
                                ctx.fill();
                            } else {
                                ctx.fillRect(s.x + cellSize / 2 - dims.dot / 2, s.y + cellSize / 2 - dims.dot / 2, dims.dot, dims.dot);
                            }
                        }
                        ctx.globalAlpha = 1;
                        return;
                    }
                    const onPointerMove = {
                        "PixelatedCanvas.useEffect.onPointerMove": (e)=>{
                            const rect = canvasEl.getBoundingClientRect();
                            targetMouseRef.current.x = e.clientX - rect.left;
                            targetMouseRef.current.y = e.clientY - rect.top;
                            pointerInsideRef.current = true;
                            activityTargetRef.current = 1;
                        }
                    }["PixelatedCanvas.useEffect.onPointerMove"];
                    const onPointerEnter = {
                        "PixelatedCanvas.useEffect.onPointerEnter": ()=>{
                            pointerInsideRef.current = true;
                            activityTargetRef.current = 1;
                        }
                    }["PixelatedCanvas.useEffect.onPointerEnter"];
                    const onPointerLeave = {
                        "PixelatedCanvas.useEffect.onPointerLeave": ()=>{
                            pointerInsideRef.current = false;
                            if (fadeOnLeave) {
                                activityTargetRef.current = 0;
                            } else {
                                targetMouseRef.current.x = -9999;
                                targetMouseRef.current.y = -9999;
                            }
                        }
                    }["PixelatedCanvas.useEffect.onPointerLeave"];
                    canvasEl.addEventListener("pointermove", onPointerMove);
                    canvasEl.addEventListener("pointerenter", onPointerEnter);
                    canvasEl.addEventListener("pointerleave", onPointerLeave);
                    const animate = {
                        "PixelatedCanvas.useEffect.animate": ()=>{
                            const now = performance.now();
                            const minDelta = 1000 / Math.max(1, maxFps);
                            if (now - lastFrameRef.current < minDelta) {
                                rafRef.current = requestAnimationFrame(animate);
                                return;
                            }
                            lastFrameRef.current = now;
                            const ctx = canvasEl.getContext("2d");
                            const dims = dimsRef.current;
                            const samples = samplesRef.current;
                            if (!ctx || !dims || !samples) {
                                rafRef.current = requestAnimationFrame(animate);
                                return;
                            }
                            animMouseRef.current.x = animMouseRef.current.x + (targetMouseRef.current.x - animMouseRef.current.x) * followSpeed;
                            animMouseRef.current.y = animMouseRef.current.y + (targetMouseRef.current.y - animMouseRef.current.y) * followSpeed;
                            if (fadeOnLeave) {
                                activityRef.current = activityRef.current + (activityTargetRef.current - activityRef.current) * fadeSpeed;
                            } else {
                                activityRef.current = pointerInsideRef.current ? 1 : 0;
                            }
                            if (backgroundColor) {
                                ctx.fillStyle = backgroundColor;
                                ctx.fillRect(0, 0, dims.width, dims.height);
                            } else {
                                ctx.clearRect(0, 0, dims.width, dims.height);
                            }
                            const mx = animMouseRef.current.x;
                            const my = animMouseRef.current.y;
                            const sigma = Math.max(1, distortionRadius * 0.5);
                            const t = now * 0.001 * jitterSpeed;
                            const activity = Math.max(0, Math.min(1, activityRef.current));
                            for (const s of samples){
                                if (s.drop || s.a <= 0) continue;
                                let drawX = s.x + cellSize / 2;
                                let drawY = s.y + cellSize / 2;
                                const dx = drawX - mx;
                                const dy = drawY - my;
                                const dist2 = dx * dx + dy * dy;
                                const falloff = Math.exp(-dist2 / (2 * sigma * sigma));
                                const influence = falloff * activity;
                                if (influence > 0.0005) {
                                    if (distortionMode === "repel") {
                                        const dist = Math.sqrt(dist2) + 0.0001;
                                        drawX += dx / dist * distortionStrength * influence;
                                        drawY += dy / dist * distortionStrength * influence;
                                    } else if (distortionMode === "attract") {
                                        const dist = Math.sqrt(dist2) + 0.0001;
                                        drawX -= dx / dist * distortionStrength * influence;
                                        drawY -= dy / dist * distortionStrength * influence;
                                    } else if (distortionMode === "swirl") {
                                        const angle = distortionStrength * 0.05 * influence;
                                        const cosA = Math.cos(angle);
                                        const sinA = Math.sin(angle);
                                        const rx = cosA * dx - sinA * dy;
                                        const ry = sinA * dx + cosA * dy;
                                        drawX = mx + rx;
                                        drawY = my + ry;
                                    }
                                    if (jitterStrength > 0) {
                                        const k = s.seed * 43758.5453;
                                        const jx = Math.sin(t + k) * jitterStrength * influence;
                                        const jy = Math.cos(t + k * 1.13) * jitterStrength * influence;
                                        drawX += jx;
                                        drawY += jy;
                                    }
                                }
                                ctx.globalAlpha = s.a;
                                ctx.fillStyle = `rgb(${s.r}, ${s.g}, ${s.b})`;
                                if (shape === "circle") {
                                    const radius = dims.dot / 2;
                                    ctx.beginPath();
                                    ctx.arc(drawX, drawY, radius, 0, Math.PI * 2);
                                    ctx.fill();
                                } else {
                                    ctx.fillRect(drawX - dims.dot / 2, drawY - dims.dot / 2, dims.dot, dims.dot);
                                }
                            }
                            ctx.globalAlpha = 1;
                            rafRef.current = requestAnimationFrame(animate);
                        }
                    }["PixelatedCanvas.useEffect.animate"];
                    if (rafRef.current) cancelAnimationFrame(rafRef.current);
                    rafRef.current = requestAnimationFrame(animate);
                    const cleanup = {
                        "PixelatedCanvas.useEffect.cleanup": ()=>{
                            canvasEl.removeEventListener("pointermove", onPointerMove);
                            canvasEl.removeEventListener("pointerenter", onPointerEnter);
                            canvasEl.removeEventListener("pointerleave", onPointerLeave);
                            if (rafRef.current) cancelAnimationFrame(rafRef.current);
                        }
                    }["PixelatedCanvas.useEffect.cleanup"];
                    img._cleanup = cleanup;
                }
            })["PixelatedCanvas.useEffect"];
            img.onerror = ({
                "PixelatedCanvas.useEffect": ()=>{
                    console.error("Failed to load image for PixelatedCanvas:", src);
                }
            })["PixelatedCanvas.useEffect"];
            if (responsive) {
                const onResize = {
                    "PixelatedCanvas.useEffect.onResize": ()=>{
                        if (img.complete && img.naturalWidth) {
                            compute();
                        }
                    }
                }["PixelatedCanvas.useEffect.onResize"];
                window.addEventListener("resize", onResize);
                return ({
                    "PixelatedCanvas.useEffect": ()=>{
                        isCancelled = true;
                        window.removeEventListener("resize", onResize);
                        if (img._cleanup) img._cleanup();
                    }
                })["PixelatedCanvas.useEffect"];
            }
            return ({
                "PixelatedCanvas.useEffect": ()=>{
                    isCancelled = true;
                    if (img._cleanup) img._cleanup();
                }
            })["PixelatedCanvas.useEffect"];
        }
    }["PixelatedCanvas.useEffect"], [
        src,
        width,
        height,
        cellSize,
        dotScale,
        shape,
        backgroundColor,
        grayscale,
        responsive,
        dropoutStrength,
        interactive,
        distortionStrength,
        distortionRadius,
        distortionMode,
        followSpeed,
        sampleAverage,
        tintColor,
        tintStrength,
        maxFps,
        objectFit,
        jitterStrength,
        jitterSpeed,
        fadeOnLeave,
        fadeSpeed
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("canvas", {
        ref: canvasRef,
        className: className,
        "aria-label": "Pixelated rendering of source image",
        role: "img"
    }, void 0, false, {
        fileName: "[project]/components/ui/pixelated-canvas.tsx",
        lineNumber: 554,
        columnNumber: 5
    }, ("TURBOPACK compile-time value", void 0));
};
_s(PixelatedCanvas, "HhjincP99k+NyFQlsTpi1cogoU0=");
_c = PixelatedCanvas;
var _c;
__turbopack_context__.k.register(_c, "PixelatedCanvas");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/cjs/react-jsx-dev-runtime.development.js [app-client] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

/**
 * @license React
 * react-jsx-dev-runtime.development.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */ var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
"use strict";
"production" !== ("TURBOPACK compile-time value", "development") && function() {
    function getComponentNameFromType(type) {
        if (null == type) return null;
        if ("function" === typeof type) return type.$$typeof === REACT_CLIENT_REFERENCE ? null : type.displayName || type.name || null;
        if ("string" === typeof type) return type;
        switch(type){
            case REACT_FRAGMENT_TYPE:
                return "Fragment";
            case REACT_PROFILER_TYPE:
                return "Profiler";
            case REACT_STRICT_MODE_TYPE:
                return "StrictMode";
            case REACT_SUSPENSE_TYPE:
                return "Suspense";
            case REACT_SUSPENSE_LIST_TYPE:
                return "SuspenseList";
            case REACT_ACTIVITY_TYPE:
                return "Activity";
            case REACT_VIEW_TRANSITION_TYPE:
                return "ViewTransition";
        }
        if ("object" === typeof type) switch("number" === typeof type.tag && console.error("Received an unexpected object in getComponentNameFromType(). This is likely a bug in React. Please file an issue."), type.$$typeof){
            case REACT_PORTAL_TYPE:
                return "Portal";
            case REACT_CONTEXT_TYPE:
                return type.displayName || "Context";
            case REACT_CONSUMER_TYPE:
                return (type._context.displayName || "Context") + ".Consumer";
            case REACT_FORWARD_REF_TYPE:
                var innerType = type.render;
                type = type.displayName;
                type || (type = innerType.displayName || innerType.name || "", type = "" !== type ? "ForwardRef(" + type + ")" : "ForwardRef");
                return type;
            case REACT_MEMO_TYPE:
                return innerType = type.displayName || null, null !== innerType ? innerType : getComponentNameFromType(type.type) || "Memo";
            case REACT_LAZY_TYPE:
                innerType = type._payload;
                type = type._init;
                try {
                    return getComponentNameFromType(type(innerType));
                } catch (x) {}
        }
        return null;
    }
    function testStringCoercion(value) {
        return "" + value;
    }
    function checkKeyStringCoercion(value) {
        try {
            testStringCoercion(value);
            var JSCompiler_inline_result = !1;
        } catch (e) {
            JSCompiler_inline_result = !0;
        }
        if (JSCompiler_inline_result) {
            JSCompiler_inline_result = console;
            var JSCompiler_temp_const = JSCompiler_inline_result.error;
            var JSCompiler_inline_result$jscomp$0 = "function" === typeof Symbol && Symbol.toStringTag && value[Symbol.toStringTag] || value.constructor.name || "Object";
            JSCompiler_temp_const.call(JSCompiler_inline_result, "The provided key is an unsupported type %s. This value must be coerced to a string before using it here.", JSCompiler_inline_result$jscomp$0);
            return testStringCoercion(value);
        }
    }
    function getTaskName(type) {
        if (type === REACT_FRAGMENT_TYPE) return "<>";
        if ("object" === typeof type && null !== type && type.$$typeof === REACT_LAZY_TYPE) return "<...>";
        try {
            var name = getComponentNameFromType(type);
            return name ? "<" + name + ">" : "<...>";
        } catch (x) {
            return "<...>";
        }
    }
    function getOwner() {
        var dispatcher = ReactSharedInternals.A;
        return null === dispatcher ? null : dispatcher.getOwner();
    }
    function UnknownOwner() {
        return Error("react-stack-top-frame");
    }
    function hasValidKey(config) {
        if (hasOwnProperty.call(config, "key")) {
            var getter = Object.getOwnPropertyDescriptor(config, "key").get;
            if (getter && getter.isReactWarning) return !1;
        }
        return void 0 !== config.key;
    }
    function defineKeyPropWarningGetter(props, displayName) {
        function warnAboutAccessingKey() {
            specialPropKeyWarningShown || (specialPropKeyWarningShown = !0, console.error("%s: `key` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://react.dev/link/special-props)", displayName));
        }
        warnAboutAccessingKey.isReactWarning = !0;
        Object.defineProperty(props, "key", {
            get: warnAboutAccessingKey,
            configurable: !0
        });
    }
    function elementRefGetterWithDeprecationWarning() {
        var componentName = getComponentNameFromType(this.type);
        didWarnAboutElementRef[componentName] || (didWarnAboutElementRef[componentName] = !0, console.error("Accessing element.ref was removed in React 19. ref is now a regular prop. It will be removed from the JSX Element type in a future release."));
        componentName = this.props.ref;
        return void 0 !== componentName ? componentName : null;
    }
    function ReactElement(type, key, props, owner, debugStack, debugTask) {
        var refProp = props.ref;
        type = {
            $$typeof: REACT_ELEMENT_TYPE,
            type: type,
            key: key,
            props: props,
            _owner: owner
        };
        null !== (void 0 !== refProp ? refProp : null) ? Object.defineProperty(type, "ref", {
            enumerable: !1,
            get: elementRefGetterWithDeprecationWarning
        }) : Object.defineProperty(type, "ref", {
            enumerable: !1,
            value: null
        });
        type._store = {};
        Object.defineProperty(type._store, "validated", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: 0
        });
        Object.defineProperty(type, "_debugInfo", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: null
        });
        Object.defineProperty(type, "_debugStack", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: debugStack
        });
        Object.defineProperty(type, "_debugTask", {
            configurable: !1,
            enumerable: !1,
            writable: !0,
            value: debugTask
        });
        Object.freeze && (Object.freeze(type.props), Object.freeze(type));
        return type;
    }
    function jsxDEVImpl(type, config, maybeKey, isStaticChildren, debugStack, debugTask) {
        var children = config.children;
        if (void 0 !== children) if (isStaticChildren) if (isArrayImpl(children)) {
            for(isStaticChildren = 0; isStaticChildren < children.length; isStaticChildren++)validateChildKeys(children[isStaticChildren]);
            Object.freeze && Object.freeze(children);
        } else console.error("React.jsx: Static children should always be an array. You are likely explicitly calling React.jsxs or React.jsxDEV. Use the Babel transform instead.");
        else validateChildKeys(children);
        if (hasOwnProperty.call(config, "key")) {
            children = getComponentNameFromType(type);
            var keys = Object.keys(config).filter(function(k) {
                return "key" !== k;
            });
            isStaticChildren = 0 < keys.length ? "{key: someKey, " + keys.join(": ..., ") + ": ...}" : "{key: someKey}";
            didWarnAboutKeySpread[children + isStaticChildren] || (keys = 0 < keys.length ? "{" + keys.join(": ..., ") + ": ...}" : "{}", console.error('A props object containing a "key" prop is being spread into JSX:\n  let props = %s;\n  <%s {...props} />\nReact keys must be passed directly to JSX without using spread:\n  let props = %s;\n  <%s key={someKey} {...props} />', isStaticChildren, children, keys, children), didWarnAboutKeySpread[children + isStaticChildren] = !0);
        }
        children = null;
        void 0 !== maybeKey && (checkKeyStringCoercion(maybeKey), children = "" + maybeKey);
        hasValidKey(config) && (checkKeyStringCoercion(config.key), children = "" + config.key);
        if ("key" in config) {
            maybeKey = {};
            for(var propName in config)"key" !== propName && (maybeKey[propName] = config[propName]);
        } else maybeKey = config;
        children && defineKeyPropWarningGetter(maybeKey, "function" === typeof type ? type.displayName || type.name || "Unknown" : type);
        return ReactElement(type, children, maybeKey, getOwner(), debugStack, debugTask);
    }
    function validateChildKeys(node) {
        isValidElement(node) ? node._store && (node._store.validated = 1) : "object" === typeof node && null !== node && node.$$typeof === REACT_LAZY_TYPE && ("fulfilled" === node._payload.status ? isValidElement(node._payload.value) && node._payload.value._store && (node._payload.value._store.validated = 1) : node._store && (node._store.validated = 1));
    }
    function isValidElement(object) {
        return "object" === typeof object && null !== object && object.$$typeof === REACT_ELEMENT_TYPE;
    }
    var React = __turbopack_context__.r("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)"), REACT_ELEMENT_TYPE = Symbol.for("react.transitional.element"), REACT_PORTAL_TYPE = Symbol.for("react.portal"), REACT_FRAGMENT_TYPE = Symbol.for("react.fragment"), REACT_STRICT_MODE_TYPE = Symbol.for("react.strict_mode"), REACT_PROFILER_TYPE = Symbol.for("react.profiler"), REACT_CONSUMER_TYPE = Symbol.for("react.consumer"), REACT_CONTEXT_TYPE = Symbol.for("react.context"), REACT_FORWARD_REF_TYPE = Symbol.for("react.forward_ref"), REACT_SUSPENSE_TYPE = Symbol.for("react.suspense"), REACT_SUSPENSE_LIST_TYPE = Symbol.for("react.suspense_list"), REACT_MEMO_TYPE = Symbol.for("react.memo"), REACT_LAZY_TYPE = Symbol.for("react.lazy"), REACT_ACTIVITY_TYPE = Symbol.for("react.activity"), REACT_VIEW_TRANSITION_TYPE = Symbol.for("react.view_transition"), REACT_CLIENT_REFERENCE = Symbol.for("react.client.reference"), ReactSharedInternals = React.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, hasOwnProperty = Object.prototype.hasOwnProperty, isArrayImpl = Array.isArray, createTask = console.createTask ? console.createTask : function() {
        return null;
    };
    React = {
        react_stack_bottom_frame: function(callStackForError) {
            return callStackForError();
        }
    };
    var specialPropKeyWarningShown;
    var didWarnAboutElementRef = {};
    var unknownOwnerDebugStack = React.react_stack_bottom_frame.bind(React, UnknownOwner)();
    var unknownOwnerDebugTask = createTask(getTaskName(UnknownOwner));
    var didWarnAboutKeySpread = {};
    exports.Fragment = REACT_FRAGMENT_TYPE;
    exports.jsxDEV = function(type, config, maybeKey, isStaticChildren) {
        var trackActualOwner = 1e4 > ReactSharedInternals.recentlyCreatedOwnerStacks++;
        if (trackActualOwner) {
            var previousStackTraceLimit = Error.stackTraceLimit;
            Error.stackTraceLimit = 10;
            var debugStackDEV = Error("react-stack-top-frame");
            Error.stackTraceLimit = previousStackTraceLimit;
        } else debugStackDEV = unknownOwnerDebugStack;
        return jsxDEVImpl(type, config, maybeKey, isStaticChildren, debugStackDEV, trackActualOwner ? createTask(getTaskName(type)) : unknownOwnerDebugTask);
    };
}();
}),
"[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
'use strict';
if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
;
else {
    module.exports = __turbopack_context__.r("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/cjs/react-jsx-dev-runtime.development.js [app-client] (ecmascript)");
}
}),
]);

//# sourceMappingURL=_8a9adf41._.js.map