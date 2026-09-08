#!/usr/bin/env node

import { createRequire } from "node:module";
import { mkdir, readFile } from "node:fs/promises";
import { dirname, extname, resolve } from "node:path";
import process from "node:process";

const defaults = {
  background: "#101828",
  foreground: "#f0eee9",
  muted: "#cdd1d9",
  border: "#394152",
  accent: "#1d4ed8",
};

function escapeXml(value) {
  return value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&apos;",
  })[character]);
}

function mimeType(path) {
  const types = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
  };
  const type = types[extname(path).toLowerCase()];
  if (!type) throw new Error(`Unsupported image type: ${path}`);
  return type;
}

function validate(config) {
  if (!config || typeof config !== "object" || Array.isArray(config)) {
    throw new Error("config must be an object");
  }
  for (const key of ["title", "tagline", "owner", "descriptor", "site", "avatar", "mark", "output"]) {
    if (typeof config[key] !== "string" || !config[key].trim()) {
      throw new Error(`${key} must be a non-empty string`);
    }
  }
  const limits = { title: 22, tagline: 46, owner: 30, descriptor: 36, site: 40 };
  for (const [key, limit] of Object.entries(limits)) {
    if (config[key].length > limit) throw new Error(`${key} must be ${limit} characters or fewer`);
  }
  if (config.footer !== undefined && (typeof config.footer !== "string" || config.footer.length > 30)) {
    throw new Error("footer must be a string of 30 characters or fewer");
  }
  if (config.colors !== undefined) {
    if (!config.colors || typeof config.colors !== "object" || Array.isArray(config.colors)) {
      throw new Error("colors must be an object");
    }
    for (const [key, value] of Object.entries(config.colors)) {
      if (!(key in defaults) || typeof value !== "string" || !/^#[0-9a-f]{6}$/i.test(value)) {
        throw new Error(`colors.${key} must be a supported six-digit hex color`);
      }
    }
  }
}

async function dataUri(path) {
  return `data:${mimeType(path)};base64,${(await readFile(path)).toString("base64")}`;
}

async function buildSvg(config, baseDir) {
  validate(config);
  const colors = { ...defaults, ...config.colors };
  const avatarPath = resolve(baseDir, config.avatar);
  const markPath = resolve(baseDir, config.mark);
  const [avatar, mark] = await Promise.all([dataUri(avatarPath), dataUri(markPath)]);
  const text = Object.fromEntries(
    ["title", "tagline", "owner", "descriptor", "site"].map((key) => [key, escapeXml(config[key])])
  );
  text.footer = escapeXml(config.footer ?? "");

  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs><clipPath id="avatar"><circle cx="108" cy="96" r="36"/></clipPath></defs>
  <rect width="1200" height="630" fill="${colors.background}"/>
  <rect x="32" y="32" width="1136" height="566" fill="none" stroke="${colors.border}"/>
  <image x="72" y="60" width="72" height="72" preserveAspectRatio="xMidYMid slice" clip-path="url(#avatar)" href="${avatar}"/>
  <text x="164" y="91" fill="${colors.foreground}" font-family="Arial, sans-serif" font-size="22" font-weight="700">${text.owner}</text>
  <text x="164" y="119" fill="${colors.muted}" font-family="Arial, sans-serif" font-size="17">${text.descriptor}</text>
  <text x="1128" y="102" fill="${colors.muted}" font-family="Arial, sans-serif" font-size="18" text-anchor="end">${text.site}</text>
  <text x="72" y="298" fill="${colors.foreground}" font-family="Arial, sans-serif" font-size="72" font-weight="700" letter-spacing="-2">${text.title}</text>
  <text x="72" y="358" fill="${colors.muted}" font-family="Arial, sans-serif" font-size="31">${text.tagline}</text>
  <rect x="72" y="535" width="72" height="4" fill="${colors.accent}"/>
  ${text.footer ? `<text x="1128" y="540" fill="${colors.muted}" font-family="Arial, sans-serif" font-size="18" text-anchor="end">${text.footer}</text>` : ""}
  <image x="878" y="190" width="210" height="210" preserveAspectRatio="xMidYMid meet" href="${mark}"/>
</svg>`;
}

async function selfTest() {
  if (escapeXml('A&B<"') !== "A&amp;B&lt;&quot;") throw new Error("XML escaping failed");
  if (mimeType("logo.SVG") !== "image/svg+xml") throw new Error("MIME detection failed");
  const config = {
    title: "Title",
    tagline: "Tagline",
    owner: "Owner",
    descriptor: "Descriptor",
    site: "example.com",
    footer: "Extensions",
    avatar: "avatar.png",
    mark: "mark.svg",
    output: "og.png",
    colors: { accent: "#1d4ed8" },
  };
  validate(config);
  try {
    validate({ ...config, colors: { accent: "url(bad)" } });
    throw new Error("invalid config was accepted");
  } catch (error) {
    if (error.message === "invalid config was accepted") throw error;
  }
  console.log("render-og self-test ok");
}

async function main() {
  if (process.argv[2] === "--self-test") return selfTest();
  if (process.argv.length !== 3) throw new Error("usage: render-og.mjs <config.json>");

  const configPath = resolve(process.argv[2]);
  const config = JSON.parse(await readFile(configPath, "utf8"));
  const output = resolve(dirname(configPath), config.output);
  const svg = await buildSvg(config, dirname(configPath));
  const require = createRequire(resolve(process.cwd(), "package.json"));
  let sharp;
  try {
    sharp = require("sharp");
  } catch {
    throw new Error("Sharp is not available from the target project; use its existing image renderer or request approval to add one");
  }
  await mkdir(dirname(output), { recursive: true });
  await sharp(Buffer.from(svg)).png().toFile(output);
  console.log(output);
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
