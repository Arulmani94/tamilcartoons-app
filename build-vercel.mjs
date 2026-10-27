import { cpSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url));
const output = join(root, 'vercel-static');
const required = ['index.html', 'anime.html', 'player.html', 'admin.html', 'assets'];
for (const name of required) {
  if (!existsSync(join(root, name))) throw new Error(`Missing website file: ${name}. Set Root Directory to the repository root.`);
}
rmSync(output, { recursive: true, force: true });
mkdirSync(output, { recursive: true });
for (const name of [...required, 'manifest.webmanifest', 'sw.js', 'offline.html', 'ads.txt', 'app-ads.txt']) {
  if (existsSync(join(root, name))) cpSync(join(root, name), join(output, name), { recursive: true });
}
console.log('Static website ready in vercel-static. Telegram backend stays on Render.');
