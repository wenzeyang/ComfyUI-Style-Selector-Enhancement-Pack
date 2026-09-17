"""Install the style-selector enhancement without replacing other Easy Use nodes."""
import argparse
import ast
from datetime import datetime
from pathlib import Path
import shutil


def selector(text):
    node = next(n for n in ast.parse(text).body
                if isinstance(n, ast.ClassDef) and n.name == 'stylesPromptSelector')
    return node, ''.join(text.splitlines(keepends=True)[node.lineno - 1:node.end_lineno])


def install(target):
    source = Path(__file__).resolve().parent / 'src'
    backend = target / 'py/nodes/prompt.py'
    frontend = target / 'web_version/v2/style_selection_manager.js'
    original = (source / 'original_selector.py').read_text(encoding='utf-8')
    enhanced = (source / 'enhanced_selector.py').read_text(encoding='utf-8')
    text = backend.read_text(encoding='utf-8')
    node, current = selector(text)
    signature = lambda value: ast.dump(ast.parse(value), include_attributes=False)
    if signature(current) not in (signature(original), signature(enhanced)):
        raise SystemExit('Unsupported selector version; no files changed.')
    if not frontend.parent.is_dir():
        raise SystemExit('Easy Use v2 frontend directory is missing; no files changed.')
    lines = text.splitlines(keepends=True)
    patched = ''.join(lines[:node.lineno - 1]) + enhanced.rstrip() + '\n' + ''.join(lines[node.end_lineno:])
    compile(patched, str(backend), 'exec')
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup = target / 'style-manager-backups' / stamp
    backup.mkdir(parents=True)
    shutil.copy2(backend, backup / 'prompt.py')
    if frontend.exists():
        shutil.copy2(frontend, backup / 'style_selection_manager.js')
    backend.write_text(patched, encoding='utf-8')
    shutil.copy2(source / 'style_selection_manager.js', frontend)
    print('Installed. Restart ComfyUI and refresh the browser.')
    print('Backup:', backup)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('easy_use_directory', type=Path)
    install(parser.parse_args().easy_use_directory.resolve())
