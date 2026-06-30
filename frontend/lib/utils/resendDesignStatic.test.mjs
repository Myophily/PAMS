import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(dirname, "../..");

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), "utf8");
}

const globals = read("app/globals.css");
const layout = read("app/layout.tsx");
const navigation = read("components/Navigation.tsx");
const card = read("components/ui/Card.tsx");
const button = read("components/ui/Button.tsx");
const input = read("components/ui/Input.tsx");
const select = read("components/ui/Select.tsx");
const modal = read("components/ui/Modal.tsx");
const dashboard = read("app/page.tsx");

assert.match(globals, /--canvas:\s*#000000/);
assert.match(globals, /--surface-card:\s*#0a0a0c/);
assert.match(
  globals,
  /--hairline-strong:\s*rgba\(255,\s*255,\s*255,\s*0\.14\)/,
);
assert.match(globals, /--accent-green:\s*#11ff99/);

assert.ok(layout.includes("bg-[var(--canvas)]"));
assert.ok(navigation.includes("border-[var(--hairline)]"));
assert.ok(card.includes("bg-[var(--surface-card)]"));
assert.ok(card.includes("rounded-xl"));
assert.ok(button.includes("bg-[var(--primary)]"));
assert.ok(button.includes("text-[var(--primary-on)]"));
assert.ok(input.includes("bg-[var(--surface-card)]"));
assert.ok(select.includes("bg-[var(--surface-card)]"));
assert.ok(modal.includes("bg-[var(--surface-card)]"));
assert.ok(dashboard.includes("tracking-[0]"));

console.log("Resend design static checks passed");
