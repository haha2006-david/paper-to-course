"""Connect existing lessons with a small offline paper-selection dialog."""
import argparse
import json
from pathlib import Path

from build import build_file, validate, validate_library


def build_library(manifest, output):
    manifest, output = Path(manifest).resolve(), Path(output).resolve()
    rows = json.loads(manifest.read_text(encoding='utf-8-sig'))
    if not isinstance(rows, list) or not rows:
        raise ValueError('batch needs at least one existing lesson')
    lessons, catalog = [], []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('lesson'), str):
            raise ValueError('each library row needs a lesson path and file')
        data = json.loads((manifest.parent / row['lesson']).read_text(encoding='utf-8-sig'))
        validate(data)
        paper = data['paper']
        catalog.append(dict(id=paper['id'], title=paper['title'], subtitle=paper['subtitle'],
                            access=paper.get('access', 'partial'), href=row.get('file')))
        lessons.append(data)
    # Validate all inputs and destinations before changing any reader.
    validate_library(catalog)
    for data, item in zip(lessons, catalog):
        build_file(data, output / item['href'], library=catalog)
    return catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        catalog = build_library(args.manifest, args.out)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f'Cannot build library: {exc}\n')
    print(f'Connected {len(catalog)} readers in {args.out.resolve()}')


if __name__ == '__main__':
    main()
