"""Explicit, source-local contracts for vocabulary and reference tables.

Only tables immediately following a vocabulary-table JSON comment are read.
This module uses the standard library so source checks do not need Anki.
"""
import html
import json
import re
from dataclasses import dataclass

from audio_tables import TABLE, cells

MARKER = re.compile(r'<!--\s*vocabulary-table:\s*(.*?)\s*-->', re.S)
EXCLUDE = re.compile(r'<!--\s*vocabulary-exclude:\s*(.*?)\s*-->', re.S)
CASES = {'Nominative', 'Possessive', 'Dative', 'Accusative', 'Addressive', 'Locative', 'Instrumental'}


def clean(value):
    value = re.sub(r'<!--.*?-->', '', value, flags=re.S)
    value = re.sub(r'<br\s*/?>', '; ', value)
    value = re.sub(r'<[^>]*>', '', value)
    return html.unescape(value).replace('\\*', '*').replace('\\|', '|').strip()


@dataclass
class VocabularyTable:
    options: dict
    headers: list
    rows: list
    anchor: str
    line: int


def read_tables(text, source):
    tables, groups = [], {}
    # Catch misspelled/malformed marker syntax rather than silently dropping it.
    if len(re.findall(r'<!--\s*vocabulary-table\b', text)) != len(list(MARKER.finditer(text))):
        raise ValueError(f'{source}: malformed vocabulary-table marker')
    for marker in MARKER.finditer(text):
        line = text.count('\n', 0, marker.start()) + 1
        location = f'{source}:{line}'
        try:
            options = json.loads(marker[1])
        except json.JSONDecodeError as error:
            raise ValueError(f'{location}: invalid vocabulary-table JSON') from error
        allowed = {'kind', 'category', 'cards', 'word', 'meaning', 'aliases', 'case', 'group', 'chapter', 'origin'}
        if (not isinstance(options, dict) or set(options) - allowed
                or options.get('kind') not in {'vocabulary', 'reference', 'paradigm'}
                or not isinstance(options.get('category'), str) or not options['category'].strip()):
            raise ValueError(f'{location}: invalid table contract')
        cards = options.get('cards')
        if not (isinstance(cards, bool) or isinstance(cards, list) and cards
                and all(isinstance(w, str) and w.strip() for w in cards)):
            raise ValueError(f'{location}: cards must be a boolean or nonempty list of forms')
        if options['kind'] != 'vocabulary' and cards is not False:
            raise ValueError(f'{location}: reference/paradigm tables cannot generate cards')
        if options.get('aliases') not in (None, 'br'):
            raise ValueError(f'{location}: unsupported aliases rule')
        if options.get('origin', 'textbook') not in {'textbook', 'reference_table'}:
            raise ValueError(f'{location}: unknown vocabulary origin')
        for field in ('word', 'meaning'):
            if field in options and (not isinstance(options[field], str) or not options[field].strip()):
                raise ValueError(f'{location}: {field} must name a column')
        if 'chapter' in options and (type(options['chapter']) is not int or not 1 <= options['chapter'] <= 25):
            raise ValueError(f'{location}: chapter must be a lesson number')
        if 'case' in options:
            if not isinstance(options['case'], str) or options['case'].title() not in CASES | {'Associative'}:
                raise ValueError(f'{location}: unknown case')
            options['case'] = options['case'].lower()
        start = marker.end()
        start += len(text[start:]) - len(text[start:].lstrip())
        match = TABLE.match(text, start)
        if not match:
            raise ValueError(f'{location}: marker must immediately precede a table')
        raw = [cells(row) for row in match[0].splitlines()]
        if len(raw) < 3 or not all(re.fullmatch(r'\s*:?-{3,}:?\s*', c) for c in raw[1]):
            raise ValueError(f'{location}: table needs headers, separator and data')
        headers = [clean(c) for c in raw[0]]
        if not all(headers) or len(set(headers)) != len(headers):
            raise ValueError(f'{location}: table headers must be nonempty and unique')
        if any(len(row) != len(headers) for row in raw[2:]):
            raise ValueError(f'{location}: inconsistent table columns')
        anchors = re.findall(r'<a id="([^"]+)"></a>', text[:marker.start()])
        if not anchors:
            raise ValueError(f'{location}: table needs a source anchor')
        table = VocabularyTable(options, headers, raw[2:], anchors[-1], line)
        if options['kind'] == 'vocabulary':
            list(word_rows(table, source))  # Validate even glossary-only rows.
        else:
            if any(not clean(cell) for row in table.rows for cell in row):
                raise ValueError(f'{location}: empty reference cell')
            if options['kind'] == 'paradigm':
                if headers[0] != 'Case':
                    raise ValueError(f'{location}: paradigm must start with the Case column')
                group = options.get('group')
                if not isinstance(group, str) or not group:
                    raise ValueError(f'{location}: paradigm needs a group')
                found = groups.setdefault(group, [])
                found.extend(clean(row[0]) for row in table.rows)
        tables.append(table)
    for group, found in groups.items():
        if set(found) != CASES or len(found) != len(CASES):
            raise ValueError(f'{source}: paradigm {group} needs each of the seven cases exactly once')
    return tables


def word_rows(table, source):
    options, headers = table.options, table.headers
    location = f'{source}:{table.line}'
    try:
        word_column = headers.index(options.get('word', 'Malayalam'))
        meaning_column = headers.index(options.get('meaning', 'English'))
    except ValueError as error:
        raise ValueError(f'{location}: missing word/meaning column') from error
    available = set()
    for row in table.rows:
        excluded = EXCLUDE.findall(' '.join(row))
        if excluded:
            if len(excluded) != 1 or not excluded[0].strip():
                raise ValueError(f'{location}: excluded row needs one nonempty reason')
            continue
        written, meaning = clean(row[word_column]), clean(row[meaning_column])
        if not written or not meaning or re.fullmatch(r'\(?\s*(?:n|adj|adv|v)\.?\s*\)?', meaning, re.I):
            raise ValueError(f'{location}: incomplete vocabulary meaning for {written!r}')
        notes = re.findall(r'\[([^]]+)\]', written) if options.get('aliases') == 'br' else []
        if options.get('aliases') == 'br':
            raw_word = re.sub(r'<!--.*?-->|\[[^]]*\]', '', row[word_column])
            forms = [clean(f).lstrip('*').strip() for f in re.split(r'<br\s*/?>', raw_word)]
            # Parenthetical conditions qualify the sense, rather than the spelling.
            condition = re.search(r'\s+(\([^)]*\))$', forms[0])
            if condition:
                meaning += ' ' + condition[1]
                forms[0] = forms[0][:condition.start()].rstrip()
            forms = list(dict.fromkeys(f for f in forms if f))
        else:
            forms = [written]
        if not forms or not all(re.search(r'[\u0d00-\u0d7f]', f) for f in forms):
            raise ValueError(f'{location}: vocabulary row needs Malayalam forms')
        available.update(forms)
        cards = options['cards']
        yield dict(malayalam=forms[0], english=meaning, variants=forms[1:],
                   study=cards if isinstance(cards, bool) else bool(set(forms) & set(cards)),
                   notes=notes, row='|'.join(row))
    if isinstance(options['cards'], list) and not set(options['cards']) <= available:
        raise ValueError(f'{location}: selected practice forms disappeared: {set(options["cards"]) - available}')
