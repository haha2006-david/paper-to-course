"""Audit a brief's visible text, figure placement and optional source-map links.

Uses only the standard library. No model calls, network access or PDF inference.
This checks artifact consistency, not scientific correctness or learning outcomes.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from build import validate


def han_count(text):
    return len(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff]', text))


def visible_main_text(data):
    """Mirror the explanatory fields rendered by assets/reader.html.

    Excludes paper metadata, source dialogs, quiz and recap tabs, figure pixels
    and mathematical command names. Includes visible figure titles/guides/tools.
    """
    parts = []
    overview = data.get('overview')
    if overview:
        parts += [overview['question'], overview['result'], overview['boundary']]
        if overview.get('formula'):
            parts += [overview['formula'], overview.get('formula_note', '')]
    else:
        parts += [data['paper']['subtitle'], data['intro']]
    for row in data['lessons']:
        parts += [row['title'], row['body'], row['caution']]
        if row.get('example'):
            parts += [row['example']]
        if row.get('output'):
            parts += [row['output']]
        for step in row.get('steps', []):
            parts += [step['label'], step['text']]
        if row.get('formula'):
            parts += [row['formula'], row.get('formula_note', '')]
    for row in data['evidence']:
        parts += [row['claim'], row['observation'], row['boundary']]
    for row in data['prerequisites']:
        parts += [row['term'], row['explanation'], row.get('role', '')]
    figures = {row['id']: row for row in data.get('figures', [])}
    for row in data['lessons'] + data['evidence']:
        for key in row.get('figure_ids', []):
            fig = figures[key]
            parts += [fig['title'], fig.get('short_reading') or fig['reading'], '放大原图保存原图']
    return '\n'.join(parts)


def audit(data, source_map=None, max_main_han=700):
    report = {
        'errors': [], 'warnings': [], 'measurements': {}, 'source_links': [],
        'scientific_fact_check': 'not_performed',
        'independent_review': False,
        'scope': 'Artifact consistency only. Source-map metadata is not proof '
                 'of PDF reading, claim support or learning effectiveness.',
    }
    errors, warnings = report['errors'], report['warnings']

    def issue(target, code, message):
        target.append({'code': code, 'message': message})

    try:
        validate(data)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        issue(errors, 'invalid_lesson', str(exc))
        return report

    text = visible_main_text(data)
    count = han_count(text)
    report['measurements'] = {
        'main_chinese_characters': count,
        'main_unicode_characters': len(text),
        'main_budget_chinese_characters': max_main_han,
        'figure_count': len(data.get('figures', [])),
        'original_figure_count': sum(f['kind'] == 'original' for f in data.get('figures', [])),
        'quiz_question_count': len(data['questions']),
        'recap_chinese_characters': sum(han_count(s) for s in data['recap'].values()),
        'count_scope': 'Actual main-view explanatory fields, including necessary '
                       'background and figure guides; excludes image pixels, '
                       'source dialogs, quiz, recap and paper metadata. '
                       'Chinese characters are not a reading-time estimate.',
    }
    if count > max_main_han:
        issue(warnings, 'main_text_over_budget',
              f'Main text has {count} Chinese characters; target {max_main_han}. '
              'Compress actual prose. Keep essential evidence; complex papers may justify more.')
    if report['measurements']['recap_chinese_characters'] > 250:
        issue(warnings, 'long_recap', 'Recap exceeds 250 Chinese characters; avoid repeating the brief.')

    # Older schemas retain fields the current main view does not display.
    unused = []
    if data.get('overview'):
        unused += [('intro', data['intro']), ('overview.method', data['overview']['method'])]
    unused += [(f'conclusions[{i}].text', row['text']) for i, row in enumerate(data.get('conclusions', []))]
    long_unused = [name for name, value in unused if han_count(value) > 200]
    report['measurements']['non_rendered_explanatory_chinese_characters'] = sum(han_count(v) for _, v in unused)
    if long_unused or report['measurements']['non_rendered_explanatory_chinese_characters'] > 700:
        issue(warnings, 'long_non_rendered_text',
              'Substantial text exists outside the main view: ' + ', '.join(long_unused or ['multiple fields']) +
              '. Check that this is not a hidden long version or omitted essential content.')

    placements = Counter(key for row in data['lessons'] + data['evidence'] for key in row.get('figure_ids', []))
    for key, n in placements.items():
        if n > 1:
            issue(errors, 'repeated_figure_placement', f'{key} appears {n} times; display each figure once.')
    images = [f['image'] for f in data.get('figures', [])]
    if len(set(images)) < len(images):
        issue(errors, 'duplicate_figure_image', 'Multiple figure IDs embed the same image.')

    anchors = {}
    anchor_groups = {}
    if source_map is not None:
        if not isinstance(source_map, dict) or not isinstance(source_map.get('blocks'), list):
            issue(errors, 'invalid_source_map', 'Source map must contain a blocks array.')
            return report
        title = source_map.get('paper', {}).get('title', '')
        normalize = lambda s: re.sub(r'\W', '', str(s)).casefold()
        if title and normalize(title) != normalize(data['paper']['title']):
            issue(warnings, 'source_title_mismatch', 'Source-map title differs; verify paper identity and version.')
        for group in ('blocks', 'figures', 'tables', 'equations'):
            rows = source_map.get(group, [])
            if not isinstance(rows, list):
                issue(errors, 'invalid_source_map', f'{group} must be an array.')
                continue
            group_ids = set()
            for row in rows:
                if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'].strip():
                    issue(errors, 'invalid_source_anchor', f'Invalid anchor in {group}.')
                    continue
                key = row['id']
                if key in group_ids:
                    issue(errors, 'duplicate_source_anchor', f'Duplicate anchor {key} in {group}.')
                    continue
                group_ids.add(key)
                if key in anchors:
                    # nature-reader can index the same equation in both places.
                    if group == 'equations' and anchor_groups[key] == 'blocks' and anchors[key].get('type') == 'equation':
                        old_page, new_page = anchors[key].get('page'), row.get('page')
                        if old_page is not None and new_page is not None and old_page != new_page:
                            issue(errors, 'conflicting_source_anchor', f'{key}: equation block and index pages disagree.')
                        anchors[key] = {**anchors[key], **row}
                        continue
                    issue(errors, 'duplicate_source_anchor', f'Duplicate anchor {key} across collections.')
                    continue
                anchors[key] = row
                anchor_groups[key] = group

    linked_primary = 0
    for source in data['sources']:
        key = source['id']
        block_ids = source.get('block_ids', [])
        pages = source.get('pdf_pages', [])
        if not isinstance(block_ids, list) or any(not isinstance(v, str) or not v.strip() for v in block_ids):
            issue(errors, 'invalid_block_ids', f'{key}: block_ids must be an array of nonempty strings.')
            continue
        if not isinstance(pages, list) or any(type(v) is not int or v < 1 for v in pages):
            issue(errors, 'invalid_pdf_pages', f'{key}: PDF indices must be positive integers, not printed labels.')
            continue
        if source_map is None or not block_ids:
            report['source_links'].append({'id': key, 'status': 'not_checked', 'reason':
                                          'No source map supplied' if source_map is None else 'No block_ids supplied'})
            if block_ids and source_map is None:
                issue(warnings, 'missing_source_map', f'{key}: anchor references cannot be checked without the map.')
            continue
        missing = [v for v in block_ids if v not in anchors]
        if missing:
            issue(errors, 'unknown_source_anchor', f'{key}: unknown anchors {missing}.')
            continue
        values = [anchors[v].get('page') for v in block_ids]
        located = all(type(v) is int and v > 0 for v in values)
        derived_pages = sorted(set(values)) if located else []
        if pages and (not located or set(pages) != set(derived_pages)):
            issue(errors, 'unsupported_pdf_page_claim', f'{key}: claimed pages are not established by all linked anchors.')
        if not located:
            issue(warnings, 'structure_only_source', f'{key}: use structural anchors; missing/invalid pages must not become page 1.')
        report['source_links'].append({'id': key, 'status': 'page_linked' if located else 'structure_linked',
                                      'block_ids': block_ids, 'pdf_pages': derived_pages})
        if source.get('kind') == 'primary':
            linked_primary += 1
    report['measurements']['map_linked_primary_sources'] = linked_primary
    if source_map is not None and linked_primary == 0:
        issue(warnings, 'no_primary_map_links', 'Map supplied but no primary source is linked; no grounding upgrade claimed.')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lesson', type=Path)
    parser.add_argument('--source-map', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--max-main-han', type=int, default=700)
    args = parser.parse_args()
    if args.max_main_han < 1:
        parser.error('--max-main-han must be positive')
    for source in (args.lesson, args.source_map):
        if source and source.resolve() == args.report.resolve():
            parser.error('Report path must not overwrite either input')
    try:
        data = json.loads(args.lesson.read_text(encoding='utf-8'))
        source_map = json.loads(args.source_map.read_text(encoding='utf-8')) if args.source_map else None
        report = audit(data, source_map, args.max_main_han)
    except (OSError, json.JSONDecodeError, TypeError, KeyError, AttributeError) as exc:
        report = {'errors': [{'code': 'input_error', 'message': str(exc)}], 'warnings': [],
                  'scientific_fact_check': 'not_performed', 'independent_review': False}
    report['input_sha256'] = hashlib.sha256(args.lesson.read_bytes()).hexdigest() if args.lesson.is_file() else None
    if args.source_map and args.source_map.is_file():
        report['source_map_sha256'] = hashlib.sha256(args.source_map.read_bytes()).hexdigest()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(report["errors"])} errors, {len(report["warnings"])} warnings; not a scientific fact check.')
    raise SystemExit(1 if report['errors'] else 0)


if __name__ == '__main__':
    main()
