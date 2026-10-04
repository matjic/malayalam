"""Render the hand-authored writing models; no image tools are required.

Run with --check to verify generated SVGs and chapter grids without writing.
"""

import argparse
import html
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from writing_shapes import SHAPES, TABLES

ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NAMESPACE)


def tag(parent, name, attributes=None, text=None):
    element = ET.SubElement(parent, f'{{{NAMESPACE}}}{name}', attributes or {})
    element.text = text
    return element


def draw(parent, key):
    shape = SHAPES[key]
    group = tag(parent, 'g', {'data-symbol': key})
    ink = tag(group, 'g', {'class': 'writing-ink', 'fill': 'none',
                         'stroke': 'currentColor', 'stroke-width': '8',
                         'stroke-linecap': 'round', 'stroke-linejoin': 'round',
                         'style': 'stroke-width:var(--writing-stroke-width,8)'})
    guides = tag(group, 'g', {'class': 'writing-guides', 'fill': 'none',
                            'stroke': '#557467', 'stroke-width': '1.6',
                            'stroke-linecap': 'round', 'stroke-linejoin': 'round',
                            'style': 'stroke:var(--writing-guide-ink,#557467)'})
    labels = tag(group, 'g', {'class': 'writing-labels', 'font-family': 'sans-serif',
                            'font-size': '13', 'text-anchor': 'middle',
                            'fill': '#557467',
                            'style': 'fill:var(--writing-guide-ink,#557467)'})
    defs = tag(guides, 'defs')
    marker = tag(defs, 'marker', {'id': f'{key}-arrow', 'markerUnits': 'userSpaceOnUse',
                                'viewBox': '0 0 10 10', 'refX': '8', 'refY': '5',
                                'markerWidth': '10', 'markerHeight': '10', 'orient': 'auto'})
    tag(marker, 'path', {'d': 'M1 1 L8 5 L1 9', 'fill': 'none', 'stroke': '#557467',
                        'stroke-width': '1.6', 'style': 'stroke:var(--writing-guide-ink,#557467)'})
    number = 0
    for index, stroke in enumerate(shape['strokes']):
        attrs = {'d': stroke['path'], 'data-part': stroke['name']}
        transform = {'transform': stroke['transform']} if stroke.get('transform') else {}
        attrs.update(transform)
        if stroke['guide']:
            number += 1
            attrs['data-movement'] = str(number)
        tag(ink, 'path', attrs)
        if not stroke['guide']:
            continue
        arrow_id = f'{key}-arrow'
        if stroke.get('arrow_size'):
            arrow_id = f'{key}-arrow-{index}'
            small_marker = ET.SubElement(defs, marker.tag, dict(marker.attrib, id=arrow_id,
                markerWidth=str(stroke['arrow_size']), markerHeight=str(stroke['arrow_size'])))
            for child in marker:
                ET.SubElement(small_marker, child.tag, child.attrib)
        guide = tag(guides, 'g', dict(transform, **{'data-movement': str(number)}))
        tag(guide, 'path', {'d': stroke['guide'], 'marker-end': f'url(#{arrow_id})'})
        label = tag(labels, 'g', dict(transform, **{'data-movement': str(number)}))
        x, y = stroke['label']
        tag(label, 'text', {'x': str(x), 'y': str(y + 4),
                            'paint-order': 'stroke fill', 'stroke': '#fff',
                            'stroke-width': '3', 'stroke-linejoin': 'round',
                            'style': 'stroke:var(--writing-background,#fff)'}, str(number))


def svg(key):
    shape = SHAPES[key]
    top = shape.get('viewTop', -55)
    root = ET.Element(f'{{{NAMESPACE}}}svg', {
        'viewBox': f'-55 {top} {shape["width"] + 110} {shape["height"] + 55 - top}',
        'role': 'img', 'aria-labelledby': f'{key}-title {key}-description',
        'data-source-page': str(shape['page']),
    })
    tag(root, 'title', {'id': f'{key}-title'}, f'{shape["symbol"]} — writing diagram')
    reference = (f'Modern form of {shape["symbol"]}, with editorial drawing movements. '
                 f'Moag PDF page {shape["page"]} contains an older form.'
                 if shape.get('form') == 'modern' else f'Redrawn from Moag, PDF page {shape["page"]}.')
    if shape.get('form'):
        root.set('data-form', shape['form'])
    tag(root, 'desc', {'id': f'{key}-description'},
        reference + ' Separate centerline paths '
        'represent the letter; thin arrows and numbers show writing movements.')
    draw(root, key)
    ET.indent(root)
    return ET.tostring(root, encoding='unicode') + '\n'


def table_svg(page):
    """Keep the existing table URLs useful, now assembled from real shapes."""
    keys = TABLES[page]
    cell_width, cell_height, columns = 430, 355, 2
    rows = (len(keys) + columns - 1) // columns
    root = ET.Element(f'{{{NAMESPACE}}}svg', {
        'viewBox': f'0 0 {columns * cell_width} {rows * cell_height}', 'role': 'img',
        'aria-label': f'Malayalam writing symbols, Moag PDF page {page}',
    })
    for index, key in enumerate(keys):
        shape = SHAPES[key]
        x, y = (index % columns) * cell_width, (index // columns) * cell_height
        scale = min(1, (cell_width - 50) / (shape['width'] + 110),
                    (cell_height - 60) / (shape['height'] + 110))
        offset_x = x + (cell_width - shape['width'] * scale) / 2
        offset_y = y + 55 + max(0, -55 - shape.get('viewTop', -55)) * scale
        group = tag(root, 'g', {'transform': f'translate({offset_x:g} {offset_y:g}) scale({scale:g})'})
        draw(group, key)
        tag(root, 'text', {'x': str(x + cell_width / 2), 'y': str(y + cell_height - 12),
                           'font-size': '22', 'text-anchor': 'middle'}, shape['caption'])
    ET.indent(root)
    return ET.tostring(root, encoding='unicode') + '\n'


def grid(page):
    lines = [f'<!-- writing-grid:{page} -->', '<div class="writing-grid">']
    for key in TABLES[page]:
        shape = SHAPES[key]
        caption = shape['caption']
        if key.startswith('sign-'):
            caption = '◌' + caption
        lines.append(f'  <figure class="writing-card" data-writing-symbol="{key}">')
        lines.append(f'    <img src="assets/writing/symbols/{key}.svg" '
                     f'alt="Writing movements for {html.escape(shape["symbol"], quote=True)}" '
                     'loading="lazy">')
        lines.append(f'    <figcaption lang="ml">{html.escape(caption)}</figcaption>')
        lines.append('  </figure>')
    lines.extend(['</div>', '<!-- /writing-grid -->'])
    return '\n'.join(lines)


def chapter():
    text = (ROOT / 'docs/symbols.md').read_text()
    for page in TABLES:
        generated = grid(page)
        block = rf'<!-- writing-grid:{page} -->.*?<!-- /writing-grid -->'
        if re.search(block, text, flags=re.S):
            text = re.sub(block, lambda _: generated, text, flags=re.S)
        else:
            image = rf'!\[[^\]]*\]\(assets/writing/front-writing-{page:03}\.svg\)'
            text, count = re.subn(image, lambda _: generated, text)
            if count != 1:
                raise SystemExit(f'Cannot locate writing table {page} in symbols.md')
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = {ROOT / f'docs/assets/writing/symbols/{key}.svg': svg(key) for key in SHAPES}
    files.update({ROOT / f'docs/assets/writing/front-writing-{page:03}.svg': table_svg(page)
                  for page in TABLES})
    files[ROOT / 'docs/symbols.md'] = chapter()
    manifest = [{'id': key, 'symbol': shape['symbol'], 'sourcePage': shape['page'],
                 'movements': sum(bool(s['guide']) for s in shape['strokes'])}
                for key, shape in SHAPES.items()]
    files[ROOT / 'docs/assets/writing/manifest.json'] = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    stale = []
    for path, content in files.items():
        if args.check:
            if not path.exists() or path.read_text() != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    if stale:
        raise SystemExit('Regenerate writing symbols: ' + ', '.join(stale))
    print(f'{"Checked" if args.check else "Built"} {len(SHAPES)} editable symbols and {len(TABLES)} writing grids.')


if __name__ == '__main__':
    main()
