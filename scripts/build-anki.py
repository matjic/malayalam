#!/usr/bin/env python3
"""Build a chapter-organized Anki package from the shared vocabulary catalog."""
import argparse
import json
from pathlib import Path

from anki_export import ROOT, build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/anki')
    parser.add_argument('--no-site-copy', action='store_true',
                        help='Build only in the output directory, without updating the site download')
    args = parser.parse_args()
    summary = build(args.output, site_package=None if args.no_site_copy else ROOT / 'docs/assets/decks/malayalam-moag.apkg')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
