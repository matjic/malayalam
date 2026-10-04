"""Check the authored diagrams against coverage and movement counts in Moag.

Counts below were read from PDF pp. 27–46, independently of generated SVGs.
The bare-consonant examples on p. 43 have no numbered directions in the source.
"""

from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'
EXPECTED = {
    27: [('vowel-a', 8), ('vowel-aa', 9), ('vowel-i', 5), ('vowel-ii', 7), ('vowel-u', 3), ('vowel-uu', 5)],
    28: [('vowel-r', 5), ('vowel-e', 6), ('vowel-ee', 7), ('vowel-ai', 8), ('vowel-o', 3), ('vowel-oo', 4)],
    29: [('vowel-au', 5), ('vowel-am', 9), ('vowel-ah', 10)],
    30: [('sign-aa', 1), ('sign-i', 1), ('sign-ii', 2)],
    31: [('sign-u', 3), ('sign-uu', 4), ('sign-r', 2)],
    32: [('sign-e', 2), ('sign-ee', 3), ('sign-ai', 4)],
    33: [('sign-o', 3), ('sign-oo', 4), ('sign-au', 2)],
    34: [('sign-am', 1), ('sign-ah', 2)],
    35: [('ka', 7), ('kha', 4), ('ga', 3), ('gha', 6), ('nga', 5)],
    36: [('cha', 4), ('chha', 5), ('ja', 6), ('jha', 7), ('nya', 7)],
    37: [('tta', 2), ('ttha', 1), ('dda', 5), ('ddha', 6), ('nna', 7)],
    38: [('tha', 4), ('thha', 3), ('da', 3), ('dha', 4), ('na', 4)],
    39: [('pa', 3), ('pha', 3), ('ba', 7), ('bha', 4), ('ma', 4)],
    40: [('ya', 4), ('ra', 3), ('la', 5), ('va', 3), ('sha', 4), ('ssa', 6)],
    41: [('sa', 5), ('ha', 3), ('lla', 4), ('zha', 3), ('rra', 1)],
    42: [('chillu-nn', 9), ('chillu-n', 6), ('chillu-r', 4)],
    43: [('chillu-l', 6), ('chillu-ll', 4), ('bare-ka', 0), ('bare-cha', 0), ('bare-tta', 0), ('bare-tha', 0), ('bare-pa', 0)],
    44: [('double-ka', 6), ('double-nga', 7), ('double-cha', 7), ('double-tha', 8), ('double-tta', 3), ('double-nna', 11), ('double-na', 6), ('double-ba', 7)],
    45: [('double-ma', 7), ('double-ya', 7), ('double-la', 7), ('double-va', 6), ('double-pa', 6), ('double-lla', 8)],
    46: [('join-ya', 1), ('join-ra', 1), ('join-la', 3), ('join-va', 2)],
}


def main():
    chapter = (ROOT / 'docs/symbols.md').read_text()
    expected_ids = {key for entries in EXPECTED.values() for key, _ in entries}
    actual_ids = set(re.findall(r'data-writing-symbol="([^"]+)"', chapter))
    errors = []
    if actual_ids != expected_ids:
        errors.append(f'Chapter coverage mismatch: {actual_ids ^ expected_ids}')
    for page, entries in EXPECTED.items():
        for key, count in entries:
            path = ROOT / f'docs/assets/writing/symbols/{key}.svg'
            root = ET.parse(path).getroot()
            if root.get('data-source-page') != str(page):
                errors.append(f'{key}: wrong source page')
            if root.findall(f'.//{SVG}image') or root.findall(f'.//{SVG}script'):
                errors.append(f'{key}: raster or script in symbol')
            layers = {g.get('class'): g for g in root.findall(f'.//{SVG}g') if g.get('class')}
            if set(layers) != {'writing-ink', 'writing-guides', 'writing-labels'}:
                errors.append(f'{key}: missing independent layer')
                continue
            numbers = [p.get('data-movement') for p in layers['writing-ink'].findall(f'{SVG}path')
                       if p.get('data-movement')]
            if numbers != list(map(str, range(1, count + 1))):
                errors.append(f'{key}: expected {count} source movements, got {numbers}')
            if len(layers['writing-labels'].findall(f'.//{SVG}text')) != count:
                errors.append(f'{key}: labels do not match movements')
            if len(layers['writing-guides'].findall(f'.//{SVG}path[@marker-end]')) != count:
                errors.append(f'{key}: direction arrows do not match movements')
            for path in layers['writing-ink'].findall(f'{SVG}path'):
                if not path.get('data-part') or not path.get('d', '').startswith('M'):
                    errors.append(f'{key}: unnamed or missing centerline')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Checked {len(expected_ids)} symbol models against 20 source tables: coverage, movements, layers, and raster-free assets passed.')


if __name__ == '__main__':
    main()
