import { test, expect } from 'bun:test';
import { readdirSync, readFileSync } from 'node:fs';
import { legacyDestination } from '../docs/assets/legacy-redirect.js';

const docs = new URL('../docs/', import.meta.url);
const pages = readdirSync(docs).filter(name => name.endsWith('.md') && !name.startsWith('_'));
const routes = Object.fromEntries(pages.map(name => [name.slice(0, -3), name === 'README.md' ? '/' : '/' + name.slice(0, -3) + '/']));

test('all published page routes and .md aliases redirect', () => {
  for (const page of pages) {
    const stem = page.slice(0, -3);
    for (const alias of [stem, page]) expect(legacyDestination('https://ml.matj.io/#/' + alias, routes)).toBe(routes[stem]);
  }
});

test('all explicit source anchors survive legacy id queries', () => {
  for (const page of pages) {
    const stem = page.slice(0, -3);
    for (const match of readFileSync(new URL(page, docs), 'utf8').matchAll(/<a id="([^"]+)"><\/a>/g)) {
      expect(legacyDestination('https://ml.matj.io/#/' + stem + '?id=' + encodeURIComponent(match[1]), routes)).toBe(routes[stem] + '#' + match[1]);
    }
  }
});

test('project-site prefixes and home aliases are preserved', () => {
  expect(legacyDestination('https://matjic.github.io/malayalam/#/lesson8?id=section-8-1', { lesson8: '/malayalam/lesson8/' })).toBe('/malayalam/lesson8/#section-8-1');
  for (const home of ['', 'README', 'README.md', 'readme']) expect(legacyDestination('https://ml.matj.io/#/' + home, routes)).toBe('/');
});

test('native anchors and clean routes do not trigger redirects', () => {
  for (const url of ['https://ml.matj.io/lesson8/', 'https://ml.matj.io/lesson8/#section-8-1', 'https://ml.matj.io/#:~:text=Malayalam']) expect(legacyDestination(url, routes)).toBe(null);
});

test('unknown, malformed, protocol-relative and outside routes are rejected', () => {
  for (const old of ['#//evil.example', '#/%2f%2fevil.example', '#/unknown', '#/%zz', '#/__proto__']) expect(legacyDestination('https://ml.matj.io/' + old, routes)).toBe(null);
  expect(legacyDestination('https://ml.matj.io/#/lesson8', { lesson8: 'https://evil.example/' })).toBe(null);
});

test('query strings and direct anchor suffixes survive', () => {
  expect(legacyDestination('https://ml.matj.io/?utm_source=anki#/lesson8?id=section-8-1&s=pronouns', routes)).toBe('/lesson8/?utm_source=anki&s=pronouns#section-8-1');
  expect(legacyDestination('https://ml.matj.io/#/lesson8#section-8-1', routes)).toBe('/lesson8/#section-8-1');
});
