#!/usr/bin/env python3
"""Find numbered paragraphs that fell out of lists during book preparation."""
import json
import re
import subprocess
from book_export import book_paths, prepare


def plain(value):
    if isinstance(value, dict):
        if value.get('t') == 'Str':
            return value['c'] + ' '
        if value.get('t') in {'SoftBreak', 'LineBreak'}:
            return '\n'
        return plain(value.get('c', []))
    if isinstance(value, list):
        return ''.join(plain(child) for child in value)
    return ''


def inspect(value, findings):
    if isinstance(value, dict):
        if value.get('t') in {'Table', 'CodeBlock', 'RawBlock'}:
            return
        if value.get('t') == 'Para':
            content = value['c']
            # Bold exercise labels are intentionally paragraphs, not list items.
            if content and content[0].get('t') != 'Strong':
                text = plain(content)
                if re.search(r'(?:^|\n)\s*\d+\.\s', text):
                    findings.append(text.strip()[:160])
        inspect(value.get('c'), findings)
    elif isinstance(value, list):
        for child in value:
            inspect(child, findings)


def main():
    paths = book_paths()
    chapters = {path.name for path in paths}
    errors = []
    for path in paths:
        ast = json.loads(subprocess.check_output(
            ['pandoc', '-f', 'markdown-auto_identifiers', '-t', 'json'],
            input=prepare(path, chapters).encode()))
        findings = []
        inspect(ast['blocks'], findings)
        errors.extend(f'{path.name}: numbered text outside a list: {text}' for text in findings)
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Checked numbered-list structure in {len(paths)} book documents; no orphaned numbered paragraphs.')


if __name__ == '__main__':
    main()
