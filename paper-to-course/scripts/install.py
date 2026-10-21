"""Copy this complete skill into any agent's chosen skills directory."""
import argparse
from pathlib import Path
import shutil
import uuid

SKILL_ROOT = Path(__file__).resolve().parents[1]
NAME = 'paper-to-course'


def install(destination, *, replace=False, dry_run=False):
    root = Path(destination).expanduser().resolve()
    target = root / NAME
    if target.is_symlink():
        raise ValueError('Destination skill is a symlink; choose a different directory.')
    if target == SKILL_ROOT or SKILL_ROOT in target.parents or target in SKILL_ROOT.parents:
        raise ValueError('Destination must be outside the source skill directory.')
    if target.exists() and (not target.is_dir() or not replace):
        raise FileExistsError('Destination exists. Use --replace to keep a backup and install anew.')
    if not (SKILL_ROOT / 'SKILL.md').is_file():
        raise ValueError('Complete source skill not found.')
    if dry_run:
        return target, None
    root.mkdir(parents=True, exist_ok=True)
    stage = root / ('.paper-to-course-stage-' + uuid.uuid4().hex)
    # All writes stay under the explicitly chosen root; no recursive deletion.
    shutil.copytree(SKILL_ROOT, stage, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    backup = None
    if target.exists():
        backup = root / (NAME + '.backup-' + uuid.uuid4().hex)
        target.rename(backup)
    try:
        stage.rename(target)
    except OSError:
        if backup is not None and not target.exists():
            backup.rename(target)
        raise
    return target, backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--to', required=True, type=Path, help='Agent skills directory; paper-to-course is added below it')
    parser.add_argument('--replace', action='store_true', help='Keep the existing installation as a sibling backup')
    parser.add_argument('--dry-run', action='store_true', help='Show destination without writing files')
    args = parser.parse_args()
    try:
        target, backup = install(args.to, replace=args.replace, dry_run=args.dry_run)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Cannot install: {error}\n')
    print(f'{"Would install" if args.dry_run else "Installed"}: {target}')
    if backup:
        print(f'Previous installation retained: {backup}')
    if not args.dry_run:
        print('Load SKILL.md through your agent. Installation alone does not verify PDF/tool support.')


if __name__ == '__main__':
    main()
