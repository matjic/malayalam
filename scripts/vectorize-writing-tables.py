"""Rebuild standalone vector writing tables with ImageMagick and Potrace.

The scans remain archival inputs; the site only loads the generated SVGs.
Paths preserve the source handwriting, stroke numbers, and direction arrows.
"""

from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG_NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG_NS)


def main():
    for command in ('magick', 'potrace'):
        if not shutil.which(command):
            raise SystemExit(f'Install {command} before rebuilding writing tables.')
    output = ROOT / 'docs/assets/writing'
    output.mkdir(parents=True, exist_ok=True)
    markdown = (ROOT / 'docs/symbols.md').read_text()
    descriptions = {name: description for description, name in re.findall(
        r'!\[([^\]]+)\]\(assets/(?:images|writing)/(front-writing-\d+)\.(?:jpg|svg)\)',
        markdown)}
    with tempfile.TemporaryDirectory() as temporary:
        for page in range(27, 47):
            name = f'front-writing-{page:03}'
            source = ROOT / f'docs/assets/images/{name}.jpg'
            width, height = map(int, subprocess.check_output([
                'magick', 'identify', '-format', '%w %h', str(source)
            ], text=True).split())
            # Exclude the printed heading, folio, and outer scanning margins.
            top = .15 if page == 46 else .13
            crop = f'{round(width * .80)}x{round(height * (.91 - top))}+{round(width * .10)}+{round(height * top)}'
            bitmap = Path(temporary) / 'table.pbm'
            traced = Path(temporary) / 'table.svg'
            subprocess.run([
                'magick', str(source), '-crop', crop, '+repage',
                '-colorspace', 'Gray', '-threshold', '65%', str(bitmap)
            ], check=True)
            subprocess.run([
                'potrace', str(bitmap), '--svg', '--tight', '--turdsize', '6',
                '--opttolerance', '0.2', '--output', str(traced)
            ], check=True)
            svg = ET.parse(traced).getroot()
            x, y, w, h = map(float, svg.get('viewBox').split())
            svg.set('viewBox', f'{x - 16:g} {y - 16:g} {w + 32:g} {h + 32:g}')
            for attribute in ('width', 'height', 'version'):
                svg.attrib.pop(attribute, None)
            svg.set('role', 'img')
            svg.set('aria-labelledby', f'{name}-title')
            title = ET.Element(f'{{{SVG_NS}}}title', {'id': f'{name}-title'})
            title.text = descriptions.get(name, 'Malayalam writing diagram')
            svg.insert(0, title)
            for element in list(svg):
                if element.tag == f'{{{SVG_NS}}}metadata':
                    svg.remove(element)
            for group in svg.iter(f'{{{SVG_NS}}}g'):
                if 'fill' in group.attrib:
                    group.set('fill', 'currentColor')
            ET.indent(svg)
            ET.ElementTree(svg).write(output / f'{name}.svg', encoding='unicode')
    print('Generated 20 vector writing tables.')


if __name__ == '__main__':
    main()
