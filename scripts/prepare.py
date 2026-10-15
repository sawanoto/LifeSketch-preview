"""Publish public PR snapshots as static files; never execute PR code."""
import html
import io
import json
import os
import re
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request
from datetime import datetime, timezone

SOURCE = 'sawanoto/LifeSketch'
PUBLIC = 'https://sawanoto.github.io/LifeSketch-preview/'
OUT = Path('site')
VERSION = 2


def bust_asset_cache(document, sha):
    """Keep relative paths, but force browsers to fetch each PR revision's assets."""
    pattern = r'''(<(?:script|link)\b[^>]*?\b(?:src|href)\s*=\s*)(["'])([^"']*)(\2)'''
    def replace(match):
        url = match.group(3)
        if not url or url.startswith(('#', '//')) or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', url):
            return match.group(0)
        path, separator, fragment = url.partition('#')
        path += ('&amp;' if '?' in path else '?') + 'preview_sha=' + sha
        if separator:
            path += '#' + fragment
        return match.group(1) + match.group(2) + path + match.group(4)
    return re.sub(pattern, replace, document, flags=re.IGNORECASE)


def api(path):
    request = urllib.request.Request('https://api.github.com/' + path, headers={
        'User-Agent': 'LifeSketch-preview',
        'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
        'Accept': 'application/vnd.github+json',
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main():
    prs = []
    page = 1
    while True:
        batch = api(f'repos/{SOURCE}/pulls?state=open&per_page=100&page={page}')
        prs.extend(p for p in batch if p['head']['repo'] and p['head']['repo']['full_name'] == SOURCE)
        if len(batch) < 100:
            break
        page += 1
    manifest = {'version': VERSION, 'prs': [
        {'number': p['number'], 'sha': p['head']['sha'], 'title': p['title']}
        for p in sorted(prs, key=lambda p: p['number'])
    ]}
    previous = None
    try:
        with urllib.request.urlopen(PUBLIC + 'manifest.json', timeout=20) as response:
            previous = json.load(response)
    except Exception:
        pass
    changed = previous != manifest or os.getenv('FORCE_REFRESH') == 'true'
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write(f'changed={str(changed).lower()}\n')
    if not changed:
        print('PR snapshots unchanged; no deployment needed.')
        return
    OUT.mkdir(exist_ok=True)
    rows = []
    for pr in manifest['prs']:
        target = OUT / f"pr-{pr['number']}"
        target.mkdir()
        # Public codeload endpoint: no credentials are sent to PR content.
        url = f"https://codeload.github.com/{SOURCE}/tar.gz/{pr['sha']}"
        with urllib.request.urlopen(url, timeout=120) as response:
            archive_data = response.read(150_000_001)
        if len(archive_data) > 150_000_000:
            raise ValueError('Snapshot archive exceeds size limit')
        total = 0
        with tarfile.open(fileobj=io.BytesIO(archive_data), mode='r:gz') as archive:
            for member in archive:
                parts = PurePosixPath(member.name).parts[1:]
                if not parts or not member.isfile() or any(p in {'.', '..', '.git', '.github'} for p in parts):
                    continue
                relative = Path(*parts)
                destination = target / relative
                if not destination.resolve().is_relative_to(target.resolve()):
                    raise ValueError('Unsafe archive path')
                total += member.size
                if total > 400_000_000:
                    raise ValueError('Expanded snapshot exceeds size limit')
                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source:
                    destination.write_bytes(source.read())
        (target / 'preview-info.json').write_text(json.dumps(pr, ensure_ascii=False), encoding='utf-8')
        for document in target.rglob('*.html'):
            text = document.read_text(encoding='utf-8')
            document.write_text(bust_asset_cache(text, pr['sha']), encoding='utf-8')
        title = html.escape(pr['title'])
        short = pr['sha'][:7]
        links = []
        for path, label in [('', 'LifeSketch Gallery'), ('001_doremi-pipes/', 'ドレミパイプを遊ぶ')]:
            if (target / path / 'index.html').is_file():
                links.append(f'<a href="pr-{pr["number"]}/{path}">{label}</a>')
        rows.append(f'<li><h2><a href="pr-{pr["number"]}/">PR #{pr["number"]} · {title}</a></h2><p>commit {short}</p><p>' + ' · '.join(links) + '</p></li>')
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / '.nojekyll').touch()
    updated = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    (OUT / 'index.html').write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>LifeSketch PR previews</title><style>body{font:16px system-ui;max-width:850px;margin:40px auto;padding:0 20px;line-height:1.7;background:#f5f4ef;color:#283140}li{padding:20px;background:white;margin:20px 0;border-radius:16px}ul{list-style:none;padding:0}a{color:#235e70}h2{font-size:1.2rem}</style><h1>LifeSketch PR previews</h1><p>マージ前の確認用です。公開中の作品とは異なる場合があります。</p><p>更新: ' + updated + '</p><ul>' + ''.join(rows) + '</ul><p>PR更新を約5分間隔で確認します。GitHubの混雑時は反映が遅れる場合があります。</p></html>', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == '__main__':
    main()
