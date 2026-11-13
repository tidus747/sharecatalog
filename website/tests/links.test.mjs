import assert from 'node:assert/strict';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const root = path.resolve('dist');
const base = (process.env.SITE_BASE || '/sharecatalog').replace(/\/$/, '');
const files = readdirSync(root, { recursive: true }).filter(file => String(file).endsWith('.html'));

test('every built page has a title, one primary heading, and no template branding', () => {
  assert.ok(files.length >= 14, 'Expected home, documentation index, guides, and 404');
  for (const file of files) {
    const html = readFileSync(path.join(root, file), 'utf8');
    assert.match(html, /<title>[^<]*ShareCatalog[^<]*<\/title>/, file);
    assert.equal((html.match(/<h1(?:\s|>)/g) || []).length, 1, `${file}: one h1`);
    assert.ok(!html.includes('Noir CLI'), `${file}: starter content removed`);
  }
});

test('every internal link and asset resolves under the Pages base', () => {
  for (const file of files) {
    const html = readFileSync(path.join(root, file), 'utf8');
    for (const match of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
      const href = match[1].replaceAll('&amp;', '&');
      if (/^(?:https?:|mailto:|data:|tel:)/.test(href)) continue;
      const current = new URL(`${base}/${String(file).replaceAll('\\', '/')}`, 'https://example.test');
      const target = new URL(href, current);
      assert.ok(target.pathname === base || target.pathname.startsWith(`${base}/`), `${file}: missing base in ${href}`);
      let destination = path.join(root, decodeURIComponent(target.pathname.slice(base.length)));
      if (target.pathname.endsWith('/') || !path.extname(destination))
        destination = path.join(destination, 'index.html');
      assert.ok(existsSync(destination), `${file}: unresolved ${href}`);
      if (target.hash && destination.endsWith('.html')) {
        const fragment = decodeURIComponent(target.hash.slice(1));
        assert.ok(readFileSync(destination, 'utf8').includes(`id="${fragment}"`), `${file}: missing anchor ${href}`);
      }
    }
  }
});

test('the sitemap and robots file use the deployment prefix', () => {
  const robots = readFileSync(path.join(root, 'robots.txt'), 'utf8');
  assert.match(robots, new RegExp(`${base}/sitemap-index\\.xml`));
  const sitemap = readFileSync(path.join(root, 'sitemap-0.xml'), 'utf8');
  assert.ok(sitemap.includes(`${base}/docs/getting-started/`));
});
