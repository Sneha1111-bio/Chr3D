module.exports = [
"[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/fetch-IBTWQCJR.js [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "fetchDocs",
    ()=>fetchDocs
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f2e$pnpm$2f$fumadocs$2d$core$40$16$2e$4$2e$1_$40$types$2b$react$40$19$2e$2$2e$7_lucide$2d$react$40$0$2e$561$2e$0_react$40$19$2e$2$2e$3_$5f$next$40$16$2e$0$2e$1_89243a64ce2b04975633f8c9425c641f$2f$node_modules$2f$fumadocs$2d$core$2f$dist$2f$chunk$2d$U67V476Y$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/.pnpm/fumadocs-core@16.4.1_@types+react@19.2.7_lucide-react@0.561.0_react@19.2.3__next@16.0.1_89243a64ce2b04975633f8c9425c641f/node_modules/fumadocs-core/dist/chunk-U67V476Y.js [app-ssr] (ecmascript)");
;
// src/search/client/fetch.ts
var cache = /* @__PURE__ */ new Map();
async function fetchDocs(query, { api = "/api/search", locale, tag }) {
    const url = new URL(api, window.location.origin);
    url.searchParams.set("query", query);
    if (locale) url.searchParams.set("locale", locale);
    if (tag) url.searchParams.set("tag", Array.isArray(tag) ? tag.join(",") : tag);
    const key = url.toString();
    const cached = cache.get(key);
    if (cached) return cached;
    const res = await fetch(url);
    if (!res.ok) throw new Error(await res.text());
    const result = await res.json();
    cache.set(key, result);
    return result;
}
;
}),
];

//# sourceMappingURL=7fbdc_fumadocs-core_dist_fetch-IBTWQCJR_e4509057.js.map