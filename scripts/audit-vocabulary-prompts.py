#!/usr/bin/env python3
"""Check every recall front and report reviewed shared prompts (not semantic proof)."""
import json

from anki_export import ROOT, audit_recall, load_inputs


def main():
    data, study, _ = load_inputs(ROOT)
    groups = audit_recall(data['entries'], study)
    print(json.dumps({
        'entries_checked': len(data['entries']),
        'entries_with_study_metadata': len(study),
        'shared_prompts_with_accepted_alternatives': groups,
        'review_limit': 'Checks normalized prompt collisions and incomplete fronts. '
                        'Meaning overlaps with different wording require editorial review.',
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
