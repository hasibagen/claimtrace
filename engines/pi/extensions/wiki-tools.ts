/**
 * wiki-tools.ts · Wiki Extension(plan_final §3.4)
 *
 * 提供 5 个自定义工具给 pi:
 * - wiki_check_wikilinks: 校验双向链接 + 孤立节点
 * - wiki_match_paperinfo: 匹配 full.md → paperinfo citekey
 * - wiki_zotero_sync: Zotero 增量同步
 * - wiki_emit_progress: 输出进度卡片(sub-agent)
 * - wiki_snapshot: git tag + 写 log
 *
 * 设计原则(plan_final §1.2 铁律):
 * - **不解析 md 正文**(只解析 YAML frontmatter 和文件名)
 * - **不抽语义字段**(scripts 只做机械校验)
 * - **不引数据库**(所有数据来自 .md 文件本身)
 *
 * 加载位置:.pi/extensions/wiki-tools.ts
 * pi 通过 jiti 加载,无需编译
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { exec } from "node:child_process";
import { promisify } from "node:util";
import * as fs from "node:fs/promises";
import * as path from "node:path";

const execAsync = promisify(exec);

const WIKI_ROOT = process.cwd();

/**
 * 工具 1: wiki_check_wikilinks
 * 校验双向链接 + 孤立节点(plan_final §7 L0)
 */
async function checkWikilinks(): Promise<string> {
  const report: string[] = [];
  let brokenCount = 0;
  let orphanCount = 0;

  // 收集所有 wikilink 目标
  const wikilinkRegex = /\[\[([^\]]+)\]\]/g;
  const incomingLinks = new Map<string, string[]>();

  const dirs = ["paperinfo", "papers", "claims", "evidence", "topics", "syntheses"];
  for (const dir of dirs) {
    const fullDir = path.join(WIKI_ROOT, dir);
    try {
      const files = await fs.readdir(fullDir);
      for (const file of files) {
        if (!file.endsWith(".md")) continue;
        const filePath = path.join(fullDir, file);
        const content = await fs.readFile(filePath, "utf-8");

        // 找所有 wikilink
        const matches = [...content.matchAll(wikilinkRegex)];
        for (const match of matches) {
          const target = match[1].trim();
          const source = `${dir}/${file}`;
          if (!incomingLinks.has(target)) incomingLinks.set(target, []);
          incomingLinks.get(target)!.push(source);
        }
      }
    } catch (e) {
      // dir not exist, skip
    }
  }

  // 找 broken wikilink(目标不存在)
  for (const [target, sources] of incomingLinks) {
    const targetPath = path.join(WIKI_ROOT, `${target}.md`);
    try {
      await fs.access(targetPath);
    } catch {
      brokenCount++;
      report.push(`❌ BROKEN: ${sources[0]} → [[${target}]]`);
    }
  }

  // 找 orphan 节点(没有入链的节点)
  for (const dir of dirs) {
    try {
      const files = await fs.readdir(path.join(WIKI_ROOT, dir));
      for (const file of files) {
        if (!file.endsWith(".md")) continue;
        const slug = `${dir}/${file.replace(".md", "")}`;
        if (!incomingLinks.has(slug) && dir !== "paperinfo") {
          orphanCount++;
          report.push(`⚠️ ORPHAN: ${slug}`);
        }
      }
    } catch (e) {}
  }

  report.unshift(`## Wiki Check Wikilinks`);
  report.unshift(`- Broken links: ${brokenCount}`);
  report.unshift(`- Orphan nodes: ${orphanCount}`);
  return report.join("\n");
}

/**
 * 工具 2: wiki_match_paperinfo
 * 从 full.md 路径推断 paperinfo citekey
 */
async function matchPaperinfo(fullMdPath: string): Promise<string> {
  // full.md 路径示例: raw/zhang_2021_fnirs/full.md
  const parts = fullMdPath.split("/");
  const citekey = parts[parts.length - 2]; // 倒数第二个 = citekey
  const paperinfoPath = path.join(WIKI_ROOT, "paperinfo", `${citekey}.md`);

  try {
    await fs.access(paperinfoPath);
    return `✅ Matched: ${paperinfoPath}`;
  } catch {
    return `❌ NOT_FOUND: ${paperinfoPath} — run \`wiki zotero sync --collection <name>\` to create`;
  }
}

/**
 * 工具 3: wiki_zotero_sync
 * 调用 wiki zotero sync 脚本
 */
async function zoteroSync(collection: string): Promise<string> {
  try {
    const { stdout, stderr } = await execAsync(
      `python3 .skill/scripts/wiki_zotero.py sync --collection "${collection}"`
    );
    return stdout || stderr;
  } catch (e: any) {
    return `❌ Sync failed: ${e.message}`;
  }
}

/**
 * 工具 4: wiki_emit_progress
 * 输出进度卡片(给 sub-agent 用)
 */
function emitProgress(current: number, total: number, message: string): string {
  const percent = Math.floor((current / total) * 100);
  const filled = Math.floor(percent / 10);
  const empty = 10 - filled;
  const bar = "█".repeat(filled) + "░".repeat(empty);
  return `[${bar}] ${percent}% (${current}/${total}) ${message}`;
}

/**
 * 工具 5: wiki_snapshot
 * git tag + 写 log
 */
async function snapshot(tagName: string, message: string): Promise<string> {
  try {
    // git add . && git commit
    await execAsync(`git add -A && git commit -m "snapshot: ${tagName}"`);
    // git tag
    await execAsync(`git tag -a "${tagName}" -m "${message}"`);
    // 写 log(全局日志在 log/ops.md)
    const logPath = path.join(WIKI_ROOT, "log", "ops.md");
    const now = new Date().toISOString().slice(0, 10);
    const logEntry = `\n## [${now}] snapshot | ${tagName}\n\n- ${message}\n`;
    await fs.appendFile(logPath, logEntry);
    return `✅ Snapshot: ${tagName}`;
  } catch (e: any) {
    return `❌ Snapshot failed: ${e.message}`;
  }
}

/**
 * pi Extension 主入口
 */
export default function (pi: ExtensionAPI) {
  // 工具 1: wiki_check_wikilinks
  pi.registerTool({
    name: "wiki_check_wikilinks",
    label: "Wiki Check Wikilinks",
    description:
      "校验 wiki 双向链接 + 孤立节点。L0 Structure 检查(plan_final §7)。不解析 md 正文。",
    parameters: Type.Object({}),
    async execute(_toolCallId, _params, _signal, _onUpdate, _ctx) {
      const result = await checkWikilinks();
      return {
        content: [{ type: "text", text: result }],
        details: {},
      };
    },
  });

  // 工具 2: wiki_match_paperinfo
  pi.registerTool({
    name: "wiki_match_paperinfo",
    label: "Wiki Match Paperinfo",
    description:
      "从 full.md 路径推断 paperinfo citekey,验证 paperinfo 节点存在。",
    parameters: Type.Object({
      fullMdPath: Type.String({
        description: "full.md 的路径,如 raw/zhang_2021_fnirs/full.md",
      }),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
      const result = await matchPaperinfo(params.fullMdPath);
      return {
        content: [{ type: "text", text: result }],
        details: {},
      };
    },
  });

  // 工具 3: wiki_zotero_sync
  pi.registerTool({
    name: "wiki_zotero_sync",
    label: "Wiki Zotero Sync",
    description:
      "增量同步 Zotero library 到 wiki 的 paperinfo/ 目录。走本地 SQLite,不联网。",
    parameters: Type.Object({
      collection: Type.String({
        description: "Zotero collection 名称,如 fNIRS、孪生脑",
      }),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
      const result = await zoteroSync(params.collection);
      return {
        content: [{ type: "text", text: result }],
        details: {},
      };
    },
  });

  // 工具 4: wiki_emit_progress
  pi.registerTool({
    name: "wiki_emit_progress",
    label: "Wiki Emit Progress",
    description: "输出进度卡片(供 sub-agent 在批量模式下展示进度)。",
    parameters: Type.Object({
      current: Type.Number({ description: "当前已完成数" }),
      total: Type.Number({ description: "总数" }),
      message: Type.String({ description: "当前进度描述" }),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
      const result = emitProgress(params.current, params.total, params.message);
      return {
        content: [{ type: "text", text: result }],
        details: {},
      };
    },
  });

  // 工具 5: wiki_snapshot
  pi.registerTool({
    name: "wiki_snapshot",
    label: "Wiki Snapshot",
    description:
      "git add + commit + tag + 写 log.md。在关键节点操作前调用,用于回滚。",
    parameters: Type.Object({
      tagName: Type.String({ description: "git tag 名称,如 wiki-2026-08-24-12-00" }),
      message: Type.String({ description: "snapshot 描述" }),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, _ctx) {
      const result = await snapshot(params.tagName, params.message);
      return {
        content: [{ type: "text", text: result }],
        details: {},
      };
    },
  });
}