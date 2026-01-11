(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/components/toc/index.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "TOCProvider",
    ()=>TOCProvider,
    "TOCScrollArea",
    ()=>TOCScrollArea,
    "TocThumb",
    ()=>TocThumb,
    "useTOCItems",
    ()=>useTOCItems
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/toc.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$cn$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/lib/cn.ts [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/tailwind-merge@3.4.0/node_modules/tailwind-merge/dist/bundle-mjs.mjs [app-client] (ecmascript) <export twMerge as cn>");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$merge$2d$refs$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/merge-refs.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$utils$2f$use$2d$on$2d$change$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/utils/use-on-change.js [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$chunk$2d$EMWGTXSW$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/chunk-EMWGTXSW.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature(), _s1 = __turbopack_context__.k.signature();
'use client';
;
;
;
;
;
const TOCContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["createContext"])([]);
_c = TOCContext;
function useTOCItems() {
    return (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["use"])(TOCContext);
}
function TOCProvider({ toc, children, ...props }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(TOCContext, {
        value: toc,
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["AnchorProvider"], {
            toc: toc,
            ...props,
            children: children
        }, void 0, false, {
            fileName: "[project]/components/toc/index.tsx",
            lineNumber: 29,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/components/toc/index.tsx",
        lineNumber: 28,
        columnNumber: 5
    }, this);
}
_c1 = TOCProvider;
function TOCScrollArea({ ref, className, ...props }) {
    _s();
    const viewRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        ref: (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$merge$2d$refs$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["mergeRefs"])(viewRef, ref),
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('relative min-h-0 text-sm ms-px overflow-auto [scrollbar-width:none] mask-[linear-gradient(to_bottom,transparent,white_16px,white_calc(100%-16px),transparent)] py-3', className),
        ...props,
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["ScrollProvider"], {
            containerRef: viewRef,
            children: props.children
        }, void 0, false, {
            fileName: "[project]/components/toc/index.tsx",
            lineNumber: 48,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/components/toc/index.tsx",
        lineNumber: 40,
        columnNumber: 5
    }, this);
}
_s(TOCScrollArea, "qwHMyrXaAWluKhqo44G402U7egI=");
_c2 = TOCScrollArea;
function TocThumb({ containerRef, ...props }) {
    _s1();
    const thumbRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const active = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useActiveAnchors"]();
    function update(info) {
        const element = thumbRef.current;
        if (!element) return;
        element.style.setProperty('--fd-top', `${info[0]}px`);
        element.style.setProperty('--fd-height', `${info[1]}px`);
    }
    const onPrint = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffectEvent"])({
        "TocThumb.useEffectEvent[onPrint]": ()=>{
            if (containerRef.current) {
                update(calc(containerRef.current, active));
            }
        }
    }["TocThumb.useEffectEvent[onPrint]"]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "TocThumb.useEffect": ()=>{
            if (!containerRef.current) return;
            const container = containerRef.current;
            const observer = new ResizeObserver(onPrint);
            observer.observe(container);
            return ({
                "TocThumb.useEffect": ()=>{
                    observer.disconnect();
                }
            })["TocThumb.useEffect"];
        }
    }["TocThumb.useEffect"], [
        containerRef
    ]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$chunk$2d$EMWGTXSW$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useOnChange"])(active, {
        "TocThumb.useOnChange": ()=>{
            if (containerRef.current) {
                update(calc(containerRef.current, active));
            }
        }
    }["TocThumb.useOnChange"]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        ref: thumbRef,
        "data-hidden": active.length === 0,
        ...props
    }, void 0, false, {
        fileName: "[project]/components/toc/index.tsx",
        lineNumber: 93,
        columnNumber: 10
    }, this);
}
_s1(TocThumb, "eWvosOu0fLck3++MlRMQNutMYBE=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useActiveAnchors"],
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffectEvent"],
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$chunk$2d$EMWGTXSW$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useOnChange"]
    ];
});
_c3 = TocThumb;
function calc(container, active) {
    if (active.length === 0 || container.clientHeight === 0) {
        return [
            0,
            0
        ];
    }
    let upper = Number.MAX_VALUE, lower = 0;
    for (const item of active){
        const element = container.querySelector(`a[href="#${item}"]`);
        if (!element) continue;
        const styles = getComputedStyle(element);
        upper = Math.min(upper, element.offsetTop + parseFloat(styles.paddingTop));
        lower = Math.max(lower, element.offsetTop + element.clientHeight - parseFloat(styles.paddingBottom));
    }
    return [
        upper,
        lower - upper
    ];
}
var _c, _c1, _c2, _c3;
__turbopack_context__.k.register(_c, "TOCContext");
__turbopack_context__.k.register(_c1, "TOCProvider");
__turbopack_context__.k.register(_c2, "TOCScrollArea");
__turbopack_context__.k.register(_c3, "TocThumb");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/layout/notebook/page/client.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "PageBreadcrumb",
    ()=>PageBreadcrumb,
    "PageFooter",
    ()=>PageFooter,
    "PageLastUpdate",
    ()=>PageLastUpdate,
    "PageTOCPopover",
    ()=>PageTOCPopover,
    "PageTOCPopoverContent",
    ()=>PageTOCPopoverContent,
    "PageTOCPopoverTrigger",
    ()=>PageTOCPopoverTrigger
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$down$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronDown$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/lucide-react@0.561.0_react@19.2.3/node_modules/lucide-react/dist/esm/icons/chevron-down.js [app-client] (ecmascript) <export default as ChevronDown>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$left$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronLeft$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/lucide-react@0.561.0_react@19.2.3/node_modules/lucide-react/dist/esm/icons/chevron-left.js [app-client] (ecmascript) <export default as ChevronLeft>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$right$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronRight$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/lucide-react@0.561.0_react@19.2.3/node_modules/lucide-react/dist/esm/icons/chevron-right.js [app-client] (ecmascript) <export default as ChevronRight>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$link$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/link.js [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$chunk$2d$SH7BNTG7$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__Link__as__default$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/chunk-SH7BNTG7.js [app-client] (ecmascript) <export Link as default>");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$cn$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/lib/cn.ts [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/tailwind-merge@3.4.0/node_modules/tailwind-merge/dist/bundle-mjs.mjs [app-client] (ecmascript) <export twMerge as cn>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$ui$40$16$2e$4$2e$1_$40$types$2b$react$2d$dom$40$19$2e$2$2e$3_$40$types$2b$react$40$19$2e$2$2e$7_$5f40$types$2b$react$40$19$2e$2$2e$7_luc_835047e90086ab73276e037a41041721$2f$node_modules$2f$fumadocs$2d$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-ui@16.4.1_@types+react-dom@19.2.3_@types+react@19.2.7__@types+react@19.2.7_luc_835047e90086ab73276e037a41041721/node_modules/fumadocs-ui/dist/contexts/i18n.js [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/@fumadocs+ui@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.10_474478f74fd1d83762a81a8605ed7a36/node_modules/@fumadocs/ui/dist/contexts/i18n.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$ui$40$16$2e$4$2e$1_$40$types$2b$react$2d$dom$40$19$2e$2$2e$3_$40$types$2b$react$40$19$2e$2$2e$7_$5f40$types$2b$react$40$19$2e$2$2e$7_luc_835047e90086ab73276e037a41041721$2f$node_modules$2f$fumadocs$2d$ui$2f$dist$2f$contexts$2f$tree$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-ui@16.4.1_@types+react-dom@19.2.3_@types+react@19.2.7__@types+react@19.2.7_luc_835047e90086ab73276e037a41041721/node_modules/fumadocs-ui/dist/contexts/tree.js [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$tree$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/@fumadocs+ui@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.10_474478f74fd1d83762a81a8605ed7a36/node_modules/@fumadocs/ui/dist/contexts/tree.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$framework$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/framework/index.js [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$chunk$2d$K4WNLOVQ$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/chunk-K4WNLOVQ.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$breadcrumb$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/breadcrumb.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$urls$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/urls.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$ui$2f$collapsible$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/ui/collapsible.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$toc$2f$index$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/toc/index.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/toc.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$layout$2f$notebook$2f$client$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/layout/notebook/client.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$ui$40$16$2e$4$2e$1_$40$types$2b$react$2d$dom$40$19$2e$2$2e$3_$40$types$2b$react$40$19$2e$2$2e$7_$5f40$types$2b$react$40$19$2e$2$2e$7_luc_835047e90086ab73276e037a41041721$2f$node_modules$2f$fumadocs$2d$ui$2f$dist$2f$utils$2f$use$2d$footer$2d$items$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-ui@16.4.1_@types+react-dom@19.2.3_@types+react@19.2.7__@types+react@19.2.7_luc_835047e90086ab73276e037a41041721/node_modules/fumadocs-ui/dist/utils/use-footer-items.js [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$hooks$2f$use$2d$footer$2d$items$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/@fumadocs+ui@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.10_474478f74fd1d83762a81a8605ed7a36/node_modules/@fumadocs/ui/dist/hooks/use-footer-items.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature(), _s1 = __turbopack_context__.k.signature(), _s2 = __turbopack_context__.k.signature(), _s3 = __turbopack_context__.k.signature(), _s4 = __turbopack_context__.k.signature(), _s5 = __turbopack_context__.k.signature();
'use client';
;
;
;
;
;
;
;
;
;
;
;
;
;
;
const TocPopoverContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["createContext"])(null);
_c = TocPopoverContext;
function PageTOCPopover({ className, children, ...rest }) {
    _s();
    const ref = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const [open, setOpen] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const { isNavTransparent } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["use"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$layout$2f$notebook$2f$client$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["LayoutContext"]);
    const onClick = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffectEvent"])({
        "PageTOCPopover.useEffectEvent[onClick]": (e)=>{
            if (!open) return;
            if (ref.current && !ref.current.contains(e.target)) setOpen(false);
        }
    }["PageTOCPopover.useEffectEvent[onClick]"]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "PageTOCPopover.useEffect": ()=>{
            window.addEventListener('click', onClick);
            return ({
                "PageTOCPopover.useEffect": ()=>{
                    window.removeEventListener('click', onClick);
                }
            })["PageTOCPopover.useEffect"];
        }
    }["PageTOCPopover.useEffect"], []);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(TocPopoverContext, {
        value: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
            "PageTOCPopover.useMemo": ()=>({
                    open,
                    setOpen
                })
        }["PageTOCPopover.useMemo"], [
            setOpen,
            open
        ]),
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$ui$2f$collapsible$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Collapsible"], {
            open: open,
            onOpenChange: setOpen,
            "data-toc-popover": "",
            className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('sticky top-(--fd-docs-row-2) z-10 [grid-area:toc-popover] h-(--fd-toc-popover-height) xl:hidden max-xl:layout:[--fd-toc-popover-height:--spacing(10)]', className),
            ...rest,
            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("header", {
                ref: ref,
                className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('border-b backdrop-blur-sm transition-colors', (!isNavTransparent || open) && 'bg-fd-background/80', open && 'shadow-lg'),
                children: children
            }, void 0, false, {
                fileName: "[project]/components/layout/notebook/page/client.tsx",
                lineNumber: 73,
                columnNumber: 9
            }, this)
        }, void 0, false, {
            fileName: "[project]/components/layout/notebook/page/client.tsx",
            lineNumber: 63,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/components/layout/notebook/page/client.tsx",
        lineNumber: 54,
        columnNumber: 5
    }, this);
}
_s(PageTOCPopover, "ny4gQg2xO1eewNVIwNKE/U989ao=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffectEvent"]
    ];
});
_c1 = PageTOCPopover;
function PageTOCPopoverTrigger({ className, ...props }) {
    _s1();
    const { text } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useI18n"])();
    const { open } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["use"])(TocPopoverContext);
    const items = (0, __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$toc$2f$index$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTOCItems"])();
    const active = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useActiveAnchor"])();
    const selected = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "PageTOCPopoverTrigger.useMemo[selected]": ()=>items.findIndex({
                "PageTOCPopoverTrigger.useMemo[selected]": (item)=>active === item.url.slice(1)
            }["PageTOCPopoverTrigger.useMemo[selected]"])
    }["PageTOCPopoverTrigger.useMemo[selected]"], [
        items,
        active
    ]);
    const path = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$tree$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTreePath"])().at(-1);
    const showItem = selected !== -1 && !open;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$ui$2f$collapsible$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CollapsibleTrigger"], {
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('flex w-full h-10 items-center text-sm text-fd-muted-foreground gap-2.5 px-4 py-2.5 text-start focus-visible:outline-none [&_svg]:size-4 md:px-6', className),
        "data-toc-popover-trigger": "",
        ...props,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(ProgressCircle, {
                value: (selected + 1) / Math.max(1, items.length),
                max: 1,
                className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('shrink-0', open && 'text-fd-primary')
            }, void 0, false, {
                fileName: "[project]/components/layout/notebook/page/client.tsx",
                lineNumber: 109,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "grid flex-1 *:my-auto *:row-start-1 *:col-start-1",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('truncate transition-[opacity,translate,color]', open && 'text-fd-foreground', showItem && 'opacity-0 -translate-y-full pointer-events-none'),
                        children: path?.name ?? text.toc
                    }, void 0, false, {
                        fileName: "[project]/components/layout/notebook/page/client.tsx",
                        lineNumber: 115,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('truncate transition-[opacity,translate]', !showItem && 'opacity-0 translate-y-full pointer-events-none'),
                        children: items[selected]?.title
                    }, void 0, false, {
                        fileName: "[project]/components/layout/notebook/page/client.tsx",
                        lineNumber: 124,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/layout/notebook/page/client.tsx",
                lineNumber: 114,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$down$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronDown$3e$__["ChevronDown"], {
                className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('shrink-0 transition-transform mx-0.5', open && 'rotate-180')
            }, void 0, false, {
                fileName: "[project]/components/layout/notebook/page/client.tsx",
                lineNumber: 133,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/layout/notebook/page/client.tsx",
        lineNumber: 101,
        columnNumber: 5
    }, this);
}
_s1(PageTOCPopoverTrigger, "cmwkbcoz0B6EREDZampIo6YKTkE=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useI18n"],
        __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$toc$2f$index$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTOCItems"],
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useActiveAnchor"],
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$tree$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTreePath"]
    ];
});
_c2 = PageTOCPopoverTrigger;
function clamp(input, min, max) {
    if (input < min) return min;
    if (input > max) return max;
    return input;
}
function ProgressCircle({ value, strokeWidth = 2, size = 24, min = 0, max = 100, ...restSvgProps }) {
    const normalizedValue = clamp(value, min, max);
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const progress = normalizedValue / max * circumference;
    const circleProps = {
        cx: size / 2,
        cy: size / 2,
        r: radius,
        fill: 'none',
        strokeWidth
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
        role: "progressbar",
        viewBox: `0 0 ${size} ${size}`,
        "aria-valuenow": normalizedValue,
        "aria-valuemin": min,
        "aria-valuemax": max,
        ...restSvgProps,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("circle", {
                ...circleProps,
                className: "stroke-current/25"
            }, void 0, false, {
                fileName: "[project]/components/layout/notebook/page/client.tsx",
                lineNumber: 181,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("circle", {
                ...circleProps,
                stroke: "currentColor",
                strokeDasharray: circumference,
                strokeDashoffset: circumference - progress,
                strokeLinecap: "round",
                transform: `rotate(-90 ${size / 2} ${size / 2})`,
                className: "transition-all"
            }, void 0, false, {
                fileName: "[project]/components/layout/notebook/page/client.tsx",
                lineNumber: 182,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/layout/notebook/page/client.tsx",
        lineNumber: 173,
        columnNumber: 5
    }, this);
}
_c3 = ProgressCircle;
function PageTOCPopoverContent(props) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$ui$2f$collapsible$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["CollapsibleContent"], {
        "data-toc-popover-content": "",
        ...props,
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('flex flex-col px-4 max-h-[50vh] md:px-6', props.className),
        children: props.children
    }, void 0, false, {
        fileName: "[project]/components/layout/notebook/page/client.tsx",
        lineNumber: 197,
        columnNumber: 5
    }, this);
}
_c4 = PageTOCPopoverContent;
function PageLastUpdate({ date: value, ...props }) {
    _s2();
    const { text } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useI18n"])();
    const [date, setDate] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])('');
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "PageLastUpdate.useEffect": ()=>{
            // to the timezone of client
            setDate(value.toLocaleDateString());
        }
    }["PageLastUpdate.useEffect"], [
        value
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
        ...props,
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('text-sm text-fd-muted-foreground', props.className),
        children: [
            text.lastUpdate,
            " ",
            date
        ]
    }, void 0, true, {
        fileName: "[project]/components/layout/notebook/page/client.tsx",
        lineNumber: 220,
        columnNumber: 5
    }, this);
}
_s2(PageLastUpdate, "qtJzDeh4E9CHV+mR0CpdD2dJuVA=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useI18n"]
    ];
});
_c5 = PageLastUpdate;
function PageFooter({ items, ...props }) {
    _s3();
    const footerList = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$hooks$2f$use$2d$footer$2d$items$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useFooterItems"])();
    const pathname = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$chunk$2d$K4WNLOVQ$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["usePathname"])();
    const { previous, next } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "PageFooter.useMemo": ()=>{
            if (items) return items;
            const idx = footerList.findIndex({
                "PageFooter.useMemo.idx": (item)=>(0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$urls$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["isActive"])(item.url, pathname, false)
            }["PageFooter.useMemo.idx"]);
            if (idx === -1) return {};
            return {
                previous: footerList[idx - 1],
                next: footerList[idx + 1]
            };
        }
    }["PageFooter.useMemo"], [
        footerList,
        items,
        pathname
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        ...props,
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('@container grid gap-4', previous && next ? 'grid-cols-2' : 'grid-cols-1', props.className),
        children: [
            previous ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(FooterItem, {
                item: previous,
                index: 0
            }, void 0, false, {
                fileName: "[project]/components/layout/notebook/page/client.tsx",
                lineNumber: 261,
                columnNumber: 19
            }, this) : null,
            next ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(FooterItem, {
                item: next,
                index: 1
            }, void 0, false, {
                fileName: "[project]/components/layout/notebook/page/client.tsx",
                lineNumber: 262,
                columnNumber: 15
            }, this) : null
        ]
    }, void 0, true, {
        fileName: "[project]/components/layout/notebook/page/client.tsx",
        lineNumber: 253,
        columnNumber: 5
    }, this);
}
_s3(PageFooter, "Y3/jPVQtSibXkkKR84cAg4a6II0=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$hooks$2f$use$2d$footer$2d$items$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useFooterItems"],
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$chunk$2d$K4WNLOVQ$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["usePathname"]
    ];
});
_c6 = PageFooter;
function FooterItem({ item, index }) {
    _s4();
    const { text } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useI18n"])();
    const Icon = index === 0 ? __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$left$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronLeft$3e$__["ChevronLeft"] : __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$right$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronRight$3e$__["ChevronRight"];
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$chunk$2d$SH7BNTG7$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__Link__as__default$3e$__["default"], {
        href: item.url,
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('flex flex-col gap-2 rounded-lg border p-4 text-sm transition-colors hover:bg-fd-accent/80 hover:text-fd-accent-foreground @max-lg:col-span-full', index === 1 && 'text-end'),
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('inline-flex items-center gap-1.5 font-medium', index === 1 && 'flex-row-reverse'),
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(Icon, {
                        className: "-mx-1 size-4 shrink-0 rtl:rotate-180"
                    }, void 0, false, {
                        fileName: "[project]/components/layout/notebook/page/client.tsx",
                        lineNumber: 285,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        children: item.name
                    }, void 0, false, {
                        fileName: "[project]/components/layout/notebook/page/client.tsx",
                        lineNumber: 286,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/layout/notebook/page/client.tsx",
                lineNumber: 279,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                className: "text-fd-muted-foreground truncate",
                children: item.description ?? (index === 0 ? text.previousPage : text.nextPage)
            }, void 0, false, {
                fileName: "[project]/components/layout/notebook/page/client.tsx",
                lineNumber: 288,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/layout/notebook/page/client.tsx",
        lineNumber: 272,
        columnNumber: 5
    }, this);
}
_s4(FooterItem, "fVtTJA3UcGTa+NW9R3t2qEQsfLQ=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useI18n"]
    ];
});
_c7 = FooterItem;
function PageBreadcrumb({ includeRoot, includeSeparator, includePage, ...props }) {
    _s5();
    const path = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$tree$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTreePath"])();
    const { root } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$tree$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTreeContext"])();
    const items = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "PageBreadcrumb.useMemo[items]": ()=>{
            return (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$breadcrumb$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["getBreadcrumbItemsFromPath"])(root, path, {
                includePage,
                includeSeparator,
                includeRoot
            });
        }
    }["PageBreadcrumb.useMemo[items]"], [
        includePage,
        includeRoot,
        includeSeparator,
        path,
        root
    ]);
    if (items.length === 0) return null;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        ...props,
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('flex items-center gap-1.5 text-sm text-fd-muted-foreground', props.className),
        children: items.map((item, i)=>{
            const className = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('truncate', i === items.length - 1 && 'text-fd-primary font-medium');
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Fragment"], {
                children: [
                    i !== 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3$2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$chevron$2d$right$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ChevronRight$3e$__["ChevronRight"], {
                        className: "size-3.5 shrink-0"
                    }, void 0, false, {
                        fileName: "[project]/components/layout/notebook/page/client.tsx",
                        lineNumber: 325,
                        columnNumber: 25
                    }, this),
                    item.url ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$chunk$2d$SH7BNTG7$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__Link__as__default$3e$__["default"], {
                        href: item.url,
                        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])(className, 'transition-opacity hover:opacity-80'),
                        children: item.name
                    }, void 0, false, {
                        fileName: "[project]/components/layout/notebook/page/client.tsx",
                        lineNumber: 327,
                        columnNumber: 15
                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: className,
                        children: item.name
                    }, void 0, false, {
                        fileName: "[project]/components/layout/notebook/page/client.tsx",
                        lineNumber: 334,
                        columnNumber: 15
                    }, this)
                ]
            }, i, true, {
                fileName: "[project]/components/layout/notebook/page/client.tsx",
                lineNumber: 324,
                columnNumber: 11
            }, this);
        })
    }, void 0, false, {
        fileName: "[project]/components/layout/notebook/page/client.tsx",
        lineNumber: 316,
        columnNumber: 5
    }, this);
}
_s5(PageBreadcrumb, "ACw5PqQ/dWTn2dA+v1txPjwWAm0=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$tree$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTreePath"],
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$tree$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTreeContext"]
    ];
});
_c8 = PageBreadcrumb;
var _c, _c1, _c2, _c3, _c4, _c5, _c6, _c7, _c8;
__turbopack_context__.k.register(_c, "TocPopoverContext");
__turbopack_context__.k.register(_c1, "PageTOCPopover");
__turbopack_context__.k.register(_c2, "PageTOCPopoverTrigger");
__turbopack_context__.k.register(_c3, "ProgressCircle");
__turbopack_context__.k.register(_c4, "PageTOCPopoverContent");
__turbopack_context__.k.register(_c5, "PageLastUpdate");
__turbopack_context__.k.register(_c6, "PageFooter");
__turbopack_context__.k.register(_c7, "FooterItem");
__turbopack_context__.k.register(_c8, "PageBreadcrumb");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/toc/default.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "TOCItems",
    ()=>TOCItems
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$ui$40$16$2e$4$2e$1_$40$types$2b$react$2d$dom$40$19$2e$2$2e$3_$40$types$2b$react$40$19$2e$2$2e$7_$5f40$types$2b$react$40$19$2e$2$2e$7_luc_835047e90086ab73276e037a41041721$2f$node_modules$2f$fumadocs$2d$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-ui@16.4.1_@types+react-dom@19.2.3_@types+react@19.2.7__@types+react@19.2.7_luc_835047e90086ab73276e037a41041721/node_modules/fumadocs-ui/dist/contexts/i18n.js [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/@fumadocs+ui@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.10_474478f74fd1d83762a81a8605ed7a36/node_modules/@fumadocs/ui/dist/contexts/i18n.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$cn$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/lib/cn.ts [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/tailwind-merge@3.4.0/node_modules/tailwind-merge/dist/bundle-mjs.mjs [app-client] (ecmascript) <export twMerge as cn>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$merge$2d$refs$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/merge-refs.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$toc$2f$index$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/toc/index.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/toc.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
'use client';
;
;
;
;
;
;
function TOCItems({ ref, className, ...props }) {
    _s();
    const containerRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const items = (0, __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$toc$2f$index$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTOCItems"])();
    const { text } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useI18n"])();
    if (items.length === 0) return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "rounded-lg border bg-fd-card p-3 text-xs text-fd-muted-foreground",
        children: text.tocNoHeadings
    }, void 0, false, {
        fileName: "[project]/components/toc/default.tsx",
        lineNumber: 16,
        columnNumber: 7
    }, this);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Fragment"], {
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$toc$2f$index$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["TocThumb"], {
                containerRef: containerRef,
                className: "absolute top-(--fd-top) h-(--fd-height) w-0.5 rounded-e-sm bg-fd-primary transition-[top,height] ease-linear duration-250"
            }, void 0, false, {
                fileName: "[project]/components/toc/default.tsx",
                lineNumber: 23,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                ref: (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$merge$2d$refs$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["mergeRefs"])(ref, containerRef),
                className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('flex flex-col border-s border-fd-foreground/10', className),
                ...props,
                children: items.map((item)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(TOCItem, {
                        item: item
                    }, item.url, false, {
                        fileName: "[project]/components/toc/default.tsx",
                        lineNumber: 33,
                        columnNumber: 11
                    }, this))
            }, void 0, false, {
                fileName: "[project]/components/toc/default.tsx",
                lineNumber: 27,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true);
}
_s(TOCItems, "/PTAhWjKZBff6o3X4vQmJ99kaJU=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$toc$2f$index$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTOCItems"],
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useI18n"]
    ];
});
_c = TOCItems;
function TOCItem({ item }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["TOCItem"], {
        href: item.url,
        className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('prose py-1.5 text-sm text-fd-muted-foreground transition-colors wrap-anywhere first:pt-0 last:pb-0 data-[active=true]:text-fd-primary', item.depth <= 2 && 'ps-3', item.depth === 3 && 'ps-6', item.depth >= 4 && 'ps-8'),
        children: item.title
    }, void 0, false, {
        fileName: "[project]/components/toc/default.tsx",
        lineNumber: 42,
        columnNumber: 5
    }, this);
}
_c1 = TOCItem;
var _c, _c1;
__turbopack_context__.k.register(_c, "TOCItems");
__turbopack_context__.k.register(_c1, "TOCItem");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/toc/clerk.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "TOCItems",
    ()=>TOCItems
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/toc.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$cn$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/lib/cn.ts [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/tailwind-merge@3.4.0/node_modules/tailwind-merge/dist/bundle-mjs.mjs [app-client] (ecmascript) <export twMerge as cn>");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$toc$2f$index$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/toc/index.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$merge$2d$refs$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/lib/merge-refs.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$ui$40$16$2e$4$2e$1_$40$types$2b$react$2d$dom$40$19$2e$2$2e$3_$40$types$2b$react$40$19$2e$2$2e$7_$5f40$types$2b$react$40$19$2e$2$2e$7_luc_835047e90086ab73276e037a41041721$2f$node_modules$2f$fumadocs$2d$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-ui@16.4.1_@types+react-dom@19.2.3_@types+react@19.2.7__@types+react@19.2.7_luc_835047e90086ab73276e037a41041721/node_modules/fumadocs-ui/dist/contexts/i18n.js [app-client] (ecmascript) <locals>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/@fumadocs+ui@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.10_474478f74fd1d83762a81a8605ed7a36/node_modules/@fumadocs/ui/dist/contexts/i18n.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
'use client';
;
;
;
;
;
;
function TOCItems({ ref, className, ...props }) {
    _s();
    const containerRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const items = (0, __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$toc$2f$index$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTOCItems"])();
    const { text } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useI18n"])();
    const [svg, setSvg] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])();
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "TOCItems.useEffect": ()=>{
            if (!containerRef.current) return;
            const container = containerRef.current;
            function onResize() {
                if (container.clientHeight === 0) return;
                let w = 0, h = 0;
                const d = [];
                for(let i = 0; i < items.length; i++){
                    const element = container.querySelector(`a[href="#${items[i].url.slice(1)}"]`);
                    if (!element) continue;
                    const styles = getComputedStyle(element);
                    const offset = getLineOffset(items[i].depth) + 1, top = element.offsetTop + parseFloat(styles.paddingTop), bottom = element.offsetTop + element.clientHeight - parseFloat(styles.paddingBottom);
                    w = Math.max(offset, w);
                    h = Math.max(h, bottom);
                    d.push(`${i === 0 ? 'M' : 'L'}${offset} ${top}`);
                    d.push(`L${offset} ${bottom}`);
                }
                setSvg({
                    path: d.join(' '),
                    width: w + 1,
                    height: h
                });
            }
            const observer = new ResizeObserver(onResize);
            onResize();
            observer.observe(container);
            return ({
                "TOCItems.useEffect": ()=>{
                    observer.disconnect();
                }
            })["TOCItems.useEffect"];
        }
    }["TOCItems.useEffect"], [
        items
    ]);
    if (items.length === 0) return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "rounded-lg border bg-fd-card p-3 text-xs text-fd-muted-foreground",
        children: text.tocNoHeadings
    }, void 0, false, {
        fileName: "[project]/components/toc/clerk.tsx",
        lineNumber: 65,
        columnNumber: 7
    }, this);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Fragment"], {
        children: [
            svg && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "absolute start-0 top-0 rtl:-scale-x-100",
                style: {
                    width: svg.width,
                    height: svg.height,
                    maskImage: `url("data:image/svg+xml,${// Inline SVG
                    encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${svg.width} ${svg.height}"><path d="${svg.path}" stroke="black" stroke-width="1" fill="none" /></svg>`)}")`
                },
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$toc$2f$index$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["TocThumb"], {
                    containerRef: containerRef,
                    className: "absolute w-full top-(--fd-top) h-(--fd-height) bg-fd-primary transition-[top,height] ease-linear duration-250"
                }, void 0, false, {
                    fileName: "[project]/components/toc/clerk.tsx",
                    lineNumber: 86,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/toc/clerk.tsx",
                lineNumber: 73,
                columnNumber: 9
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                ref: (0, __TURBOPACK__imported__module__$5b$project$5d2f$lib$2f$merge$2d$refs$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["mergeRefs"])(containerRef, ref),
                className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('flex flex-col', className),
                ...props,
                children: items.map((item, i)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(TOCItem, {
                        item: item,
                        upper: items[i - 1]?.depth,
                        lower: items[i + 1]?.depth
                    }, item.url, false, {
                        fileName: "[project]/components/toc/clerk.tsx",
                        lineNumber: 94,
                        columnNumber: 11
                    }, this))
            }, void 0, false, {
                fileName: "[project]/components/toc/clerk.tsx",
                lineNumber: 92,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true);
}
_s(TOCItems, "i5cwvv120B81Bf0a2F2GemCYdXs=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$toc$2f$index$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTOCItems"],
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f40$fumadocs$2b$ui$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$10_474478f74fd1d83762a81a8605ed7a36$2f$node_modules$2f40$fumadocs$2f$ui$2f$dist$2f$contexts$2f$i18n$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useI18n"]
    ];
});
_c = TOCItems;
function getItemOffset(depth) {
    if (depth <= 2) return 14;
    if (depth === 3) return 26;
    return 36;
}
function getLineOffset(depth) {
    return depth >= 3 ? 10 : 0;
}
function TOCItem({ item, upper = item.depth, lower = item.depth }) {
    const offset = getLineOffset(item.depth), upperOffset = getLineOffset(upper), lowerOffset = getLineOffset(lower);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$toc$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["TOCItem"], {
        href: item.url,
        style: {
            paddingInlineStart: getItemOffset(item.depth)
        },
        className: "prose relative py-1.5 text-sm text-fd-muted-foreground hover:text-fd-accent-foreground transition-colors wrap-anywhere first:pt-0 last:pb-0 data-[active=true]:text-fd-primary",
        children: [
            offset !== upperOffset && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                xmlns: "http://www.w3.org/2000/svg",
                viewBox: "0 0 16 16",
                className: "absolute -top-1.5 start-0 size-4 rtl:-scale-x-100",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("line", {
                    x1: upperOffset,
                    y1: "0",
                    x2: offset,
                    y2: "12",
                    className: "stroke-fd-foreground/10",
                    strokeWidth: "1"
                }, void 0, false, {
                    fileName: "[project]/components/toc/clerk.tsx",
                    lineNumber: 143,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/toc/clerk.tsx",
                lineNumber: 138,
                columnNumber: 9
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$tailwind$2d$merge$40$3$2e$4$2e$0$2f$node_modules$2f$tailwind$2d$merge$2f$dist$2f$bundle$2d$mjs$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__twMerge__as__cn$3e$__["cn"])('absolute inset-y-0 w-px bg-fd-foreground/10', offset !== upperOffset && 'top-1.5', offset !== lowerOffset && 'bottom-1.5'),
                style: {
                    insetInlineStart: offset
                }
            }, void 0, false, {
                fileName: "[project]/components/toc/clerk.tsx",
                lineNumber: 153,
                columnNumber: 7
            }, this),
            item.title
        ]
    }, void 0, true, {
        fileName: "[project]/components/toc/clerk.tsx",
        lineNumber: 130,
        columnNumber: 5
    }, this);
}
_c1 = TOCItem;
var _c, _c1;
__turbopack_context__.k.register(_c, "TOCItems");
__turbopack_context__.k.register(_c1, "TOCItem");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/mdx/mermaid.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "Mermaid",
    ()=>Mermaid
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next@16.0.10_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$2d$themes$40$0$2e$4$2e$6_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2d$themes$2f$dist$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/next-themes@0.4.6_react-dom@19.2.3_react@19.2.3__react@19.2.3/node_modules/next-themes/dist/index.mjs [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature(), _s1 = __turbopack_context__.k.signature();
'use client';
;
;
function Mermaid({ chart }) {
    _s();
    const [mounted, setMounted] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "Mermaid.useEffect": ()=>{
            setMounted(true);
        }
    }["Mermaid.useEffect"], []);
    if (!mounted) return;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(MermaidContent, {
        chart: chart
    }, void 0, false, {
        fileName: "[project]/components/mdx/mermaid.tsx",
        lineNumber: 14,
        columnNumber: 10
    }, this);
}
_s(Mermaid, "LrrVfNW3d1raFE0BNzCTILYmIfo=");
_c = Mermaid;
const cache = new Map();
function cachePromise(key, setPromise) {
    const cached = cache.get(key);
    if (cached) return cached;
    const promise = setPromise();
    cache.set(key, promise);
    return promise;
}
function MermaidContent({ chart }) {
    _s1();
    const id = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useId"])();
    const { resolvedTheme } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$2d$themes$40$0$2e$4$2e$6_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2d$themes$2f$dist$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTheme"])();
    const { default: mermaid } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["use"])(cachePromise('mermaid', {
        "MermaidContent.use": ()=>__turbopack_context__.A("[project]/node_modules/.pnpm/mermaid@11.12.2/node_modules/mermaid/dist/mermaid.core.mjs [app-client] (ecmascript, async loader)")
    }["MermaidContent.use"]));
    mermaid.initialize({
        startOnLoad: false,
        securityLevel: 'loose',
        fontFamily: 'inherit',
        themeCSS: 'margin: 1.5rem auto 0;',
        theme: resolvedTheme === 'dark' ? 'dark' : 'default'
    });
    const { svg, bindFunctions } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["use"])(cachePromise(`${chart}-${resolvedTheme}`, {
        "MermaidContent.use": ()=>{
            return mermaid.render(id, chart.replaceAll('\\n', '\n'));
        }
    }["MermaidContent.use"]));
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        ref: (container)=>{
            if (container) bindFunctions?.(container);
        },
        dangerouslySetInnerHTML: {
            __html: svg
        }
    }, void 0, false, {
        fileName: "[project]/components/mdx/mermaid.tsx",
        lineNumber: 48,
        columnNumber: 5
    }, this);
}
_s1(MermaidContent, "kssakcJwW+rjGNvNKPQbFfspn54=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$40$16$2e$0$2e$10_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useId"],
        __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$next$2d$themes$40$0$2e$4$2e$6_react$2d$dom$40$19$2e$2$2e$3_react$40$19$2e$2$2e$3_$5f$react$40$19$2e$2$2e$3$2f$node_modules$2f$next$2d$themes$2f$dist$2f$index$2e$mjs__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useTheme"]
    ];
});
_c1 = MermaidContent;
var _c, _c1;
__turbopack_context__.k.register(_c, "Mermaid");
__turbopack_context__.k.register(_c1, "MermaidContent");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=components_37f6926c._.js.map