#!/usr/bin/env python3
"""Check every recall front and report reviewed shared prompts (not semantic proof)."""
import json

from anki_export import ROOT, audit_recall, load_inputs, study_entries
from vocabulary_tables import EXCLUDE, read_tables


def main():
    data, study, _ = load_inputs(ROOT)
    groups = audit_recall(data['entries'], study)
    selected = study_entries(data['entries'])
    excluded = []
    for path in sorted((ROOT / 'docs').glob('*.md')):
        for table in read_tables(path.read_text(), path.name):
            for row in table.rows:
                for reason in EXCLUDE.findall(' '.join(row)):
                    excluded.append(dict(source=path.name, anchor=table.anchor, reason=reason))
    print(json.dumps({
        'catalog_entries': len(data['entries']),
        'entries_checked': len(selected),
        'glossary_only_entries': len(data['entries']) - len(selected),
        'explicit_source_exclusions': excluded,
        'entries_with_study_metadata': len(study),
        'shared_prompts_with_accepted_alternatives': groups,
        'review_limit': 'Checks normalized prompt collisions and incomplete fronts. '
                        'Meaning overlaps with different wording require editorial review.',
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
