#!/usr/bin/env python3
"""Emoji picker and reversible Niri binding; uses only Python's standard library."""
import datetime, fcntl, json, os, re, shutil, subprocess, sys, tempfile
from xml.sax.saxutils import escape
from pathlib import Path

DATA = Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share'))) / 'angelos-emoji-picker'
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config'))) / 'niri'
TOKEN = '// angelos-emoji-picker'
BIND = re.compile(r'^([ \t]*)(?:Mod|Super|Meta)\+Period[ \t]*(?:[^\n{]*)\{[^\n]*\}[ \t]*$', re.M)


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.'+path.name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(name, path.stat().st_mode & 0o777 if path.exists() else 0o600)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def configs(root):
    seen = set()
    def visit(path):
        path = path.resolve()
        if path in seen or not path.is_file(): return
        if not path.is_relative_to(CONFIG.resolve()):
            raise ValueError('Niri includes outside its config directory are not supported')
        seen.add(path)
        yield path
        for rel in re.findall(r'^\s*include\s+"([^"\n]+)"', path.read_text(), re.M):
            yield from visit(path.parent / rel)
    return list(visit(root))


def validated_write(path, content):
    # Validate the entire include tree in a separate directory before touching live files.
    with tempfile.TemporaryDirectory(prefix='emoji-niri-') as tmp:
        clone = Path(tmp)/'niri'
        shutil.copytree(CONFIG, clone)
        candidate = clone/path.relative_to(CONFIG.resolve())
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text(content)
        result = subprocess.run(['niri', 'validate', '-c', str(clone/'config.kdl')], capture_output=True, text=True)
        if result.returncode:
            raise ValueError('Niri config validation failed: '+result.stderr[-2000:])
    atomic(path, content)


def enable(token):
    for command in ('niri', 'fuzzel', 'wl-copy'):
        if not shutil.which(command): raise ValueError('Required command missing: '+command)
    source = Path(__file__).resolve().parent
    if source != DATA.resolve():
        atomic(DATA/'picker.py', (source/'picker.py').read_text())
        atomic(DATA/'emoji.json', (source/'data/emoji.json').read_text())
        shutil.copytree(source/'fonts', DATA/'fonts', dirs_exist_ok=True)
    state_path = DATA/'binding.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else None
    if state and Path(state['path']).exists() and state['line'] in Path(state['path']).read_text():
        state['token'] = token
        atomic(state_path, json.dumps(state))
        print('Meta + .: ready; select an emoji, then paste with Ctrl + V')
        return
    root = (CONFIG/'config.kdl').resolve()
    paths = configs(root)
    matches = [(p, m) for p in paths for m in BIND.finditer(p.read_text())]
    if len(matches) > 1: raise ValueError('Multiple Meta + . bindings; resolve them first')
    command = json.dumps(str(DATA/'picker.py'), ensure_ascii=False)
    action = f'Mod+Period {{ spawn "python3" {command} "launch"; }} {TOKEN}'
    if matches:
        path, match = matches[0]
        content = path.read_text()
        old = match.group(0)
        line = match.group(1)+action
        updated = content[:match.start()]+line+content[match.end():]
    else:
        # Add a separate binds block; removing it later does not affect other configuration.
        path, old = root, ''
        line = '\nbinds {\n    '+action+'\n}\n'
        updated = root.read_text()+line
    validated_write(path, updated)
    state = {'path': str(path), 'before': old, 'line': line, 'token': token}
    try:
        atomic(state_path, json.dumps(state))
    except OSError:
        atomic(path, updated.replace(line, old, 1))
        raise
    print('Meta + .: ready; select an emoji, then paste with Ctrl + V')


def disable(token):
    file = DATA/'binding.json'
    if not file.exists(): return
    state = json.loads(file.read_text())
    if state['token'] != token: return  # an older shell instance cannot unbind a newer one
    path = Path(state['path'])
    if path.exists():
        content = path.read_text()
        if state['line'] in content:
            validated_write(path, content.replace(state['line'], state['before'], 1))
    file.unlink()


PALETTES = {
    'dark': ('1e1e2eff', 'cdd6f4ff', 'cba6f7ff'),
    'light': ('eff1f5ff', '4c4f69ff', '8839efff'),
    'rose': ('2a2032ff', 'f9e9f0ff', 'f5a9c8ff'),
}

def preferences():
    file = CONFIG.parent/'angelos/settings.json'
    try:
        config = json.loads(file.read_text())
        values = config.get('plugins', {}).get('data', {}).get('emoji-picker', {})
        if not isinstance(values, dict): return {}
        values = dict(values)
        a = config.get('appearance', {})
        values['_accent'] = a.get('customAccent', '#c77dff')
        values['_mode'] = a.get('mode', 'dark')
        return values
    except (OSError, ValueError, AttributeError): return {}


def appearance(values, source):
    args = []
    theme = values.get('theme', 'system')
    if not isinstance(theme, str): theme = 'system'
    if theme == 'wallpaper':
        accent = values.get('_accent', '#c77dff')
        if not isinstance(accent, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', accent): accent = '#c77dff'
        light = values.get('_mode') == 'light'
        seed = [int(accent[i:i+2],16) for i in (1,3,5)]
        bg = ''.join(f'{round((245 if light else 20)*0.90+c*0.10):02x}' for c in seed)+'ff'
        fg = '202126ff' if light else 'fafafaff'
        tone = ''.join(f'{round(c*0.70+(20 if light else 255)*0.30):02x}' for c in seed)+'ff'
        values = dict(values, background='#'+bg[:6], foreground='#'+fg[:6], accent='#'+tone[:6])
        theme = 'custom'
    if theme in PALETTES or theme == 'custom':
        colors = PALETTES.get(theme, PALETTES['dark'])
        if theme == 'custom':
            colors = tuple((values.get(key, '')[1:]+'ff') if isinstance(values.get(key), str) and re.fullmatch(r'#[0-9a-fA-F]{6}', values[key]) else fallback for key, fallback in zip(('background', 'foreground', 'accent'), colors))
        bg, fg, accent = colors
        contrast = '161622ff' if sum(int(accent[i:i+2],16)*weight for i,weight in [(0,0.299),(2,0.587),(4,0.114)]) > 150 else 'ffffffff'
        for key, color in [('background',bg),('text',fg),('prompt',fg),('input',fg),('match',accent),('selection',accent),('selection-text',contrast),('selection-match',contrast),('border',accent)]:
            args += ['--'+key+'-color', color]
        args += ['--border-radius', '12', '--border-width', '2']
    style = values.get('emojiStyle', 'system')
    if not isinstance(style, str): style = 'system'
    font = {'google': 'Noto Color Emoji', 'twemoji': 'Twemoji Mozilla'}.get(style, '')
    if style == 'custom':
        custom = values.get('emojiFont', '')
        if isinstance(custom, str) and re.fullmatch(r'[\w ()-]{1,80}', custom): font = custom
    size = values.get('fontSize',16)
    if size not in (12,16,20): size = 16
    if font: args += ['--override', 'main.font=monospace,'+font+':size='+str(size)]
    elif size != 16: args += ['--override', 'main.font=monospace:size='+str(size)]
    env = os.environ.copy()
    fonts = source/'fonts'
    if fonts.is_dir():
        config = DATA/'fonts.conf'
        atomic(config, '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir>'+escape(str(fonts))+'</dir></fontconfig>')
        env['FONTCONFIG_FILE'] = str(config)
    return args, env


def launch():
    source = Path(__file__).resolve().parent
    file = source/'emoji.json' if (source/'emoji.json').exists() else source/'data/emoji.json'
    entries = json.loads(file.read_text())
    text = '\n'.join(e['emoji']+'  '+e['name']+' | '+e['keywords'] for e in entries)
    cache = DATA/'picker.lock'
    DATA.mkdir(parents=True, exist_ok=True)
    with cache.open('w') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return
        args, env = appearance(preferences(), source)
        chosen = subprocess.run(['fuzzel', '--dmenu', '--index', '--prompt', 'Emoji > ', '--width', '65', '--lines', '12'] + args, input=text, text=True, capture_output=True, env=env)
        if chosen.returncode:
            if chosen.returncode not in (1, -15): raise ValueError('Picker failed: '+chosen.stderr.strip())
            return  # Escape does not alter the clipboard
        try:
            index = int(chosen.stdout.strip())
            if not 0 <= index < len(entries): return
            emoji = entries[index]['emoji']
        except (ValueError, IndexError): return
        subprocess.run(['wl-copy', '--type', 'text/plain;charset=utf-8'], input=emoji.encode(), check=True)
        if shutil.which('notify-send'):
            subprocess.run(['notify-send', 'Emoji Picker', emoji+' — скопировано / copied. Ctrl + V'], check=False)


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    action = sys.argv[1] if len(sys.argv)>1 else 'launch'
    if action == 'launch': return launch()
    if action not in ('enable', 'disable') or len(sys.argv) != 3: raise ValueError('Use enable/disable TOKEN or launch')
    with (DATA/'binding.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        (enable if action == 'enable' else disable)(sys.argv[2])

if __name__ == '__main__':
    try: main()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
