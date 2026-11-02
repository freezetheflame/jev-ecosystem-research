"""Import user-supplied run records without executing bundled code or replacing files."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import zipfile

PREFIXES = ('data/agent-security-study/runs/', 'data/agent-security-study/preparations/')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_path(info):
    name = info.filename
    parts = PurePosixPath(name).parts
    if (not parts or name.startswith('/') or '\\' in name or ':' in name
            or any(p in ('.', '..') or p.rstrip(' .') != p for p in parts)
            or stat.S_ISLNK(info.external_attr >> 16)):
        raise ValueError('Unsafe archive entry')
    if any(p.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL',
            *('COM' + str(i) for i in range(1, 10)), *('LPT' + str(i) for i in range(1, 10))} for p in parts):
        raise ValueError('Windows device path in archive')
    return PurePosixPath(*parts)


def import_bundle(archive, root, record_dir):
    archive, root, record_dir = Path(archive).resolve(), Path(root).resolve(), Path(record_dir).resolve()
    if record_dir.exists():
        raise FileExistsError('Import record directory already exists')
    entries, selected, seen, collisions = [], [], set(), []
    with zipfile.ZipFile(archive) as bundle:
        # Validate the complete archive before creating any destination file.
        for info in bundle.infolist():
            relative = checked_path(info)
            if info.is_dir():
                continue
            key = relative.as_posix().casefold()
            if key in seen:
                raise ValueError('Duplicate archive file')
            seen.add(key)
            data = bundle.read(info)  # Also checks the ZIP CRC.
            entry = {'path': relative.as_posix(), 'bytes': len(data), 'sha256': sha(data),
                     'imported': relative.as_posix().startswith(PREFIXES)}
            entries.append(entry)
            if not entry['imported']:
                continue
            destination = root.joinpath(*relative.parts).resolve()
            if not destination.is_relative_to(root):
                raise ValueError('Archive destination escapes repository')
            if destination.exists() and (not destination.is_file() or sha(destination.read_bytes()) != entry['sha256']):
                collisions.append(entry['path'])
            selected.append((info.filename, destination, entry))
        if collisions:
            raise ValueError('Existing files differ; nothing imported: ' + ', '.join(collisions[:5]))
        record_dir.mkdir(parents=True)
        saved = record_dir / archive.name
        shutil.copyfile(archive, saved)
        for name, destination, entry in selected:
            if destination.exists():
                entry['action'] = 'identical_existing_file_preserved'
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open('xb') as stream:
                    stream.write(bundle.read(name))
                entry['action'] = 'created'
    result = {'record_kind': 'imported_original_records_not_new_experiment',
              'archive_name': archive.name, 'archive_sha256': sha(archive.read_bytes()),
              'saved_archive': str(saved), 'files': entries, 'imported_files': len(selected),
              'source_execution': 'none', 'model_calls': 0}
    with (record_dir / 'import-manifest.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--record-dir', required=True)
    args = parser.parse_args()
    result = import_bundle(args.archive, args.root, args.record_dir)
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
