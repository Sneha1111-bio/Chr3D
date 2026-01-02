// @ts-nocheck
import * as __fd_glob_25 from "../content/docs/tutorials/index.mdx?collection=docs"
import * as __fd_glob_24 from "../content/docs/tutorials/hichip-tutorial.mdx?collection=docs"
import * as __fd_glob_23 from "../content/docs/tutorials/hic-tutorial.mdx?collection=docs"
import * as __fd_glob_22 from "../content/docs/tutorials/chiapet-tutorial.mdx?collection=docs"
import * as __fd_glob_21 from "../content/docs/guides/restriction-fragments.mdx?collection=docs"
import * as __fd_glob_20 from "../content/docs/guides/quality-control.mdx?collection=docs"
import * as __fd_glob_19 from "../content/docs/guides/matrix-generation.mdx?collection=docs"
import * as __fd_glob_18 from "../content/docs/guides/loop-calling.mdx?collection=docs"
import * as __fd_glob_17 from "../content/docs/getting-started/quickstart.mdx?collection=docs"
import * as __fd_glob_16 from "../content/docs/getting-started/installation.mdx?collection=docs"
import * as __fd_glob_15 from "../content/docs/getting-started/index.mdx?collection=docs"
import * as __fd_glob_14 from "../content/docs/getting-started/concepts.mdx?collection=docs"
import * as __fd_glob_13 from "../content/docs/cli/index.mdx?collection=docs"
import * as __fd_glob_12 from "../content/docs/api/utils.mdx?collection=docs"
import * as __fd_glob_11 from "../content/docs/api/index.mdx?collection=docs"
import * as __fd_glob_10 from "../content/docs/api/hichip.mdx?collection=docs"
import * as __fd_glob_9 from "../content/docs/api/hic.mdx?collection=docs"
import * as __fd_glob_8 from "../content/docs/api/chiapet.mdx?collection=docs"
import * as __fd_glob_7 from "../content/docs/faq.mdx?collection=docs"
import * as __fd_glob_6 from "../content/docs/comparison.mdx?collection=docs"
import * as __fd_glob_5 from "../content/docs/benchmarks.mdx?collection=docs"
import { default as __fd_glob_4 } from "../content/docs/tutorials/meta.json?collection=docs"
import { default as __fd_glob_3 } from "../content/docs/guides/meta.json?collection=docs"
import { default as __fd_glob_2 } from "../content/docs/getting-started/meta.json?collection=docs"
import { default as __fd_glob_1 } from "../content/docs/cli/meta.json?collection=docs"
import { default as __fd_glob_0 } from "../content/docs/api/meta.json?collection=docs"
import { server } from 'fumadocs-mdx/runtime/server';
import type * as Config from '../source.config';

const create = server<typeof Config, import("fumadocs-mdx/runtime/types").InternalTypeConfig & {
  DocData: {
  }
}>({"doc":{"passthroughs":["extractedReferences"]}});

export const docs = await create.docs("docs", "content/docs", {"api/meta.json": __fd_glob_0, "cli/meta.json": __fd_glob_1, "getting-started/meta.json": __fd_glob_2, "guides/meta.json": __fd_glob_3, "tutorials/meta.json": __fd_glob_4, }, {"benchmarks.mdx": __fd_glob_5, "comparison.mdx": __fd_glob_6, "faq.mdx": __fd_glob_7, "api/chiapet.mdx": __fd_glob_8, "api/hic.mdx": __fd_glob_9, "api/hichip.mdx": __fd_glob_10, "api/index.mdx": __fd_glob_11, "api/utils.mdx": __fd_glob_12, "cli/index.mdx": __fd_glob_13, "getting-started/concepts.mdx": __fd_glob_14, "getting-started/index.mdx": __fd_glob_15, "getting-started/installation.mdx": __fd_glob_16, "getting-started/quickstart.mdx": __fd_glob_17, "guides/loop-calling.mdx": __fd_glob_18, "guides/matrix-generation.mdx": __fd_glob_19, "guides/quality-control.mdx": __fd_glob_20, "guides/restriction-fragments.mdx": __fd_glob_21, "tutorials/chiapet-tutorial.mdx": __fd_glob_22, "tutorials/hic-tutorial.mdx": __fd_glob_23, "tutorials/hichip-tutorial.mdx": __fd_glob_24, "tutorials/index.mdx": __fd_glob_25, });