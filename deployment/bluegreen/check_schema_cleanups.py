"""Report tracked schema retirement work; never authorize or perform deletion."""
import json
import os
from pathlib import Path
import sys


def report(backend):
    path = Path(backend) / 'prisma' / 'schema-cleanups.json'
    if not path.exists():
        raise RuntimeError('Backend schema cleanup register is missing')
    entries = json.loads(path.read_text(encoding='utf-8'))
    lines = ['## Pending database cleanup', '']
    seen = set()
    for entry in entries:
        if entry['id'] in seen or entry['status'] not in ('pending', 'complete'):
            raise ValueError('Invalid cleanup ID or status')
        seen.add(entry['id'])
        if entry['status'] == 'complete':
            if not entry.get('deletionMigration') or not entry.get('reviewEvidence'):
                raise ValueError('Completed cleanup requires migration and review evidence')
            continue
        name = entry['table'] + '.' + entry['column']
        print(f'::warning title=Pending database cleanup::{name} remains retained. Review required; deletion is not automatic.')
        lines.extend([f"### {entry['id']}", '', f"Column: `{name}`", '', entry['reason'], '',
                      'Required evidence (not verified by this reminder):', ''])
        lines.extend('- ' + item for item in entry['requiredEvidence'])
        lines.append('')
    summary = '\n'.join(lines) + '\n'
    print(summary)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write(summary)


if __name__ == '__main__':
    report(sys.argv[1])
