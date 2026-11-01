/* Fragment routes are visible only to the browser. No legacy router is needed. */
export function legacyDestination(input, routes) {
  const current = new URL(input);
  if (!current.hash.startsWith('#/')) return null;
  const old = new URL(current.hash.slice(1), 'https://legacy.invalid');
  if (old.origin !== 'https://legacy.invalid') return null;
  let stem;
  try { stem = decodeURIComponent(old.pathname).replace(/^\//, '').replace(/\/$/, '').replace(/\.md$/, ''); }
  catch (_) { return null; }
  if (!stem || stem.toLowerCase() === 'readme') stem = 'README';
  if (!Object.hasOwn(routes, stem)) return null;
  const target = new URL(routes[stem], current.origin);
  if (target.origin !== current.origin) return null;
  for (const [key, value] of current.searchParams) target.searchParams.append(key, value);
  for (const [key, value] of old.searchParams) if (key !== 'id') target.searchParams.append(key, value);
  target.hash = old.hash || (old.searchParams.get('id') ? '#' + old.searchParams.get('id') : '');
  return target.pathname + target.search + target.hash;
}

if (typeof document !== 'undefined') {
  const routes = JSON.parse(document.getElementById('site-routes').textContent);
  function redirect() {
    const target = legacyDestination(location.href, routes);
    if (target) location.replace(target);
  }
  redirect();
  addEventListener('hashchange', redirect);
}
