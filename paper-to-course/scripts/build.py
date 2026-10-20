"""Validate a lesson and render a dependency-free, offline reading handout."""
import argparse
import base64
import binascii
import hashlib
import html
import json
import re
import struct
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def validate(data):
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    def string(obj, key):
        require(isinstance(obj, dict) and isinstance(obj.get(key), str)
                and bool(obj[key].strip()), f'{key}: expected nonempty text')

    def items(obj, key, minimum=1):
        require(isinstance(obj, dict) and isinstance(obj.get(key), list)
                and len(obj[key]) >= minimum, f'{key}: expected a nonempty list')
        return obj[key]

    def url(value):
        require(isinstance(value, str), 'url: expected text')
        if value:
            parsed = urlsplit(value)
            require(parsed.scheme in ('https', 'http') and bool(parsed.hostname)
                    and not parsed.username and not parsed.password,
                    'url: only http/https links without credentials are allowed')

    require(isinstance(data, dict) and type(data.get('schema_version')) is int
            and data['schema_version'] in (1, 2), 'schema_version must be 1 or 2')
    v2 = data['schema_version'] == 2
    paper = data.get('paper')
    for key in ('id', 'title', 'subtitle', 'coverage', 'audience'):
        string(paper, key)
    url(paper.get('url'))
    string(data, 'intro')
    sources = items(data, 'sources')
    source_ids = set()
    source_kinds = {}
    for source in sources:
        for key in ('id', 'label', 'locator', 'note'):
            string(source, key)
        require(source['id'] not in source_ids, 'duplicate source id')
        source_ids.add(source['id'])
        url(source.get('url'))
        if v2:
            require(source.get('kind') in ('primary', 'background'), 'source kind must be primary/background')
            string(source, 'authority')
            source_kinds[source['id']] = source['kind']

    def references(item):
        refs = items(item, 'source_ids')
        require(all(isinstance(ref, str) and ref in source_ids for ref in refs),
                'source_ids: unresolved reference')

    for prerequisite in items(data, 'prerequisites', 0):
        for key in ('term', 'explanation'):
            string(prerequisite, key)
        if v2:
            string(prerequisite, 'role')
            require(prerequisite.get('verification') in ('verified', 'paper_defined', 'unverified'),
                    'prerequisite verification must be explicit')
            if prerequisite['verification'] != 'unverified':
                references(prerequisite)
                expected = 'background' if prerequisite['verification'] == 'verified' else 'primary'
                require(any(source_kinds[ref] == expected for ref in prerequisite['source_ids']),
                        'background verification status does not match its source kind')
            else:
                require(prerequisite.get('source_ids') == [], 'unverified background must not fabricate references')
    seen_lessons = set()
    for lesson in items(data, 'lessons'):
        for key in ('id', 'title', 'body', 'caution'):
            string(lesson, key)
        require(isinstance(lesson.get('example', ''), str), 'example: expected text')
        if 'output' in lesson:
            string(lesson, 'output')
        require(lesson.get('step_layout', 'sequence') in ('sequence', 'parallel'),
                'step_layout must be sequence/parallel')
        if 'steps' in lesson:
            steps = items(lesson, 'steps', 2)
            for step in steps:
                for key in ('label', 'text'):
                    string(step, key)
        for key in ('formula', 'formula_note'):
            if key in lesson:
                string(lesson, key)
        require(lesson['id'] not in seen_lessons, 'duplicate lesson id')
        seen_lessons.add(lesson['id'])
        references(lesson)
    for evidence in items(data, 'evidence'):
        for key in ('claim', 'observation', 'boundary'):
            string(evidence, key)
        references(evidence)
        if v2:
            require(any(source_kinds[ref] == 'primary' for ref in evidence['source_ids']),
                    'paper evidence must cite the paper')
    question_ids = set()
    for question in items(data, 'questions'):
        for key in ('id', 'prompt', 'explanation'):
            string(question, key)
        require(question['id'] not in question_ids, 'duplicate question id')
        question_ids.add(question['id'])
        choices = items(question, 'choices', 2)
        require(all(isinstance(choice, str) and bool(choice.strip()) for choice in choices),
                'choices: expected nonempty text')
        require(len(set(choices)) == len(choices), 'choices: duplicate choice')
        require(type(question.get('answer')) is int and 0 <= question['answer'] < len(choices),
                'answer: invalid choice index')
        references(question)
    teach_back = data.get('teach_back')
    string(teach_back, 'prompt')
    require(all(isinstance(point, str) and bool(point.strip())
                for point in items(teach_back, 'checkpoints')), 'checkpoints: expected text')
    for key in ('problem', 'move', 'evidence', 'boundary', 'tomorrow'):
        string(data.get('recap'), key)
    if v2:
        require(paper.get('access') in ('full', 'partial', 'abstract'), 'paper access must be explicit')
        for conclusion in items(data, 'conclusions'):
            string(conclusion, 'text')
            references(conclusion)
            require(any(source_kinds[ref] == 'primary' for ref in conclusion['source_ids']),
                    'paper conclusions must cite the paper')
        topics = set()
        for coverage in items(data, 'coverage_audit'):
            string(coverage, 'topic')
            require(coverage['topic'] not in topics, 'duplicate coverage topic')
            topics.add(coverage['topic'])
            require(coverage.get('status') in ('covered', 'partial', 'unavailable', 'not_applicable'),
                    'invalid coverage status')
            string(coverage, 'note')
            if coverage['status'] in ('covered', 'partial'):
                references(coverage)
            else:
                require(coverage.get('source_ids') == [], 'unavailable/not_applicable must use empty source_ids')
        require(topics == {'problem', 'method', 'results', 'robustness', 'conclusions', 'limitations', 'use'},
                'coverage_audit must explicitly account for all seven topics')
        require(all(isinstance(value, str) and value.strip()
                    for value in items(data, 'return_to_original')), 'return_to_original must contain text')
        if paper['access'] == 'abstract':
            require(not any(c['status'] == 'covered' and c['topic'] in ('method', 'robustness')
                            for c in data['coverage_audit']), 'abstract access cannot claim full methods/robustness coverage')
    figures = data.get('figures', [])
    require(isinstance(figures, list), 'figures must be a list')
    figure_ids, total_bytes = set(), 0
    for figure in figures:
        for key in ('id', 'title', 'alt', 'caption', 'reading', 'boundary', 'image'):
            string(figure, key)
        require(figure['id'] not in figure_ids, 'duplicate figure id')
        figure_ids.add(figure['id'])
        require(figure.get('kind') in ('original', 'teaching', 'redrawn_data'), 'invalid figure kind')
        require(type(figure.get('collapsed', False)) is bool, 'figure collapsed must be boolean')
        references(figure)
        if v2 and figure['kind'] in ('original', 'redrawn_data'):
            require(any(source_kinds[ref] == 'primary' for ref in figure['source_ids']), 'paper figure must cite primary evidence')
        require(figure['image'].startswith('data:image/png;base64,'), 'figure image must be an embedded PNG')
        require(len(figure['image']) <= 12 * 1024 * 1024, 'figure image too large')
        try:
            raw = base64.b64decode(figure['image'].split(',', 1)[1], validate=True)
        except (ValueError, binascii.Error):
            raise ValueError('invalid figure encoding') from None
        require(len(raw) >= 33 and raw[:8] == b'\x89PNG\r\n\x1a\n' and raw[12:16] == b'IHDR', 'invalid PNG header')
        width, height = struct.unpack('>II', raw[16:24])
        require(1 <= width <= 10000 and 1 <= height <= 10000 and width * height <= 35000000,
                'figure dimensions exceed limit')
        total_bytes += len(raw)
    require(total_bytes <= 20 * 1024 * 1024, 'embedded figures exceed total limit')
    placed = set()
    for item in data['lessons'] + data['evidence']:
        links = item.get('figure_ids', [])
        require(isinstance(links, list) and all(isinstance(ref, str) and ref in figure_ids for ref in links),
                'figure_ids: unresolved figure')
        require(len(links) == len(set(links)), 'duplicate figure placement')
        placed.update(links)
    require(placed == figure_ids, 'every figure must appear beside a lesson or evidence')
    if 'overview' in data:
        overview = data['overview']
        for key in ('question', 'method', 'result', 'boundary'):
            string(overview, key)
        references(overview)
        for key in ('method_figure_ids', 'result_figure_ids'):
            refs = overview.get(key, [])
            require(isinstance(refs, list) and all(isinstance(ref, str) and ref in figure_ids for ref in refs),
                    'overview figures: unresolved reference')
        for key in ('formula', 'formula_note'):
            if key in overview:
                string(overview, key)


def validate_library(library):
    if not isinstance(library, list):
        raise ValueError('library must be a list')
    ids, files = set(), set()
    for item in library:
        if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip()
                                            for k in ('id', 'title', 'subtitle', 'href', 'access')):
            raise ValueError('invalid library item')
        filename = item['href']
        if (any(c in filename for c in '/\\:#?%') or filename in ('.', '..')
                or not filename.endswith('.html') or item['access'] not in ('full', 'partial', 'abstract')):
            raise ValueError('library href must be a local HTML filename')
        if item['id'] in ids or filename.casefold() in files:
            raise ValueError('duplicate library paper or filename')
        ids.add(item['id'])
        files.add(filename.casefold())


def render(data, previous_keys=None, library=None):
    validate(data)
    library = [] if library is None else library
    validate_library(library)
    library_payload = json.dumps(library, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    # A JSON script element is still terminated by </script> in the HTML parser.
    payload = payload.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = (ROOT / 'assets' / 'reader.html').read_text(encoding='utf-8')
    math_root = ROOT / 'assets' / 'math'
    css = (math_root / 'katex.inline.css').read_text(encoding='utf-8')
    scripts = [(math_root / name).read_text(encoding='utf-8').replace('</script', '<\\/script')
               for name in ('katex.min.js', 'auto-render.min.js')]
    math_assets = '<style>' + css + '</style>' + ''.join('<script>'+code+'</script>' for code in scripts)
    quiz_identity = json.dumps([data['paper']['id'], data['questions'], data['teach_back']], ensure_ascii=False, sort_keys=True)
    fingerprint = hashlib.sha256(quiz_identity.encode('utf-8')).hexdigest()[:20]
    aliases = [key for key in (previous_keys or []) if re.fullmatch(r'paper-to-course:[a-f0-9]{20}', key)]
    return template.replace('__PAPER_TITLE__', html.escape(data['paper']['title'])) \
                   .replace('__LESSON_KEY__', fingerprint).replace('__LESSON_DATA__', payload) \
                   .replace('__PAPER_LIBRARY__', library_payload) \
                   .replace('__READER_STYLE__', (ROOT / 'assets' / 'reader.css').read_text(encoding='utf-8')).replace('__MATH_ASSETS__', math_assets).replace('__STATE_ALIASES__', json.dumps(aliases))


def build_file(data, output, library=None):
    """Preserve compatible quiz state and an existing offline paper menu."""
    output = Path(output)
    previous_keys = []
    if output.exists():
        previous = output.read_text(encoding='utf-8')
        old_payload = re.search(r'<script type="application/json" id="lesson-data">(.*?)</script>', previous, re.S)
        old_key = re.search(r"KEY='(paper-to-course:[a-f0-9]{20})'", previous)
        if old_payload and old_key:
            try:
                old_data = json.loads(old_payload.group(1))
                if (old_data.get('paper', {}).get('id') == data['paper']['id']
                        and old_data.get('questions') == data['questions']
                        and old_data.get('teach_back') == data['teach_back']):
                    previous_keys.append(old_key.group(1))
            except json.JSONDecodeError:
                pass
        if library is None:
            old_library = re.search(r'<script type="application/json" id="paper-library">(.*?)</script>', previous, re.S)
            if old_library:
                library = json.loads(old_library.group(1))
    result = render(data, previous_keys=previous_keys, library=library)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lesson', type=Path)
    parser.add_argument('--out', type=Path, default=Path('论文讲义.html'))
    parser.add_argument('--check', action='store_true', help='Validate without rendering')
    args = parser.parse_args()
    try:
        data = json.loads(args.lesson.read_text(encoding='utf-8-sig'))
        validate(data)
        if not args.check:
            build_file(data, args.out)
        print('Lesson validated.' if args.check else f'Created: {args.out.resolve()}')
    except (ValueError, OSError, TypeError) as exc:
        parser.exit(1, f'Cannot build lesson: {exc}\n')


if __name__ == '__main__':
    main()
