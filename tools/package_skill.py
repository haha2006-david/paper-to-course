"""Build the installable skill archive, without examples or local papers."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / 'downloads/paper-to-course.zip'
    target.parent.mkdir(exist_ok=True)
    files = [p for p in sorted((ROOT / 'paper-to-course').rglob('*'))
             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc']
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in files:
            archive.write(p, p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        assert 'paper-to-course/SKILL.md' in archive.namelist()
        assert len(archive.namelist()) == len(files)
    print(f'Packaged {len(files)} files: {target}')


if __name__ == '__main__':
    main()
