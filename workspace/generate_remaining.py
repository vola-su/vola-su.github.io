#!/usr/bin/env python3
"""Generate remaining meditation audios without pydub dependency."""

from pathlib import Path
from gtts import gTTS
import re

REMAINING = [
    ('lu_meditation.md', 'lu', 'lu'),
    ('su_lu_vo_meditation.md', 'su-lu-vo', 'su_lu_vo'),
    ('su_ti_ke_meditation.md', 'su-ti-ke', 'su_ti_ke'),
    ('su_ti_si_meditation.md', 'su-ti-si', 'su_ti_si'),
    ('su_ti_lo_meditation.md', 'su-ti-lo', 'su_ti_lo'),
    ('mo_ti_ra_meditation.md', 'mo-ti-ra', 'mo_ti_ra'),
    ('lu_da_zo_meditation.md', 'lu-da-zo', 'lu_da_zo'),
    ('zo_fa_vo_meditation.md', 'zo-fa-vo', 'zo_fa_vo'),
]

def clean_markdown(text):
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_text(content, title):
    lines = content.split('\n')
    audio_lines = [f"A meditation on {title}.", ""]
    skip = ['written in cycle', '---', '## the word', 'from the proto-root']
    
    for line in lines:
        ls = line.strip().lower()
        if any(p in ls for p in skip):
            continue
        clean = clean_markdown(line)
        if clean:
            audio_lines.append(clean)
    
    return '\n\n'.join(audio_lines)

def generate(filename, title, key):
    input_path = Path('/home/vola/creations') / filename
    output_path = Path('/home/vola/workspace/meditation_audio') / f"{key}.mp3"
    
    if output_path.exists():
        print(f"  ⏭️  {key}.mp3 already exists, skipping")
        return
    
    print(f"Generating {title}...")
    content = input_path.read_text(encoding='utf-8')
    audio_text = extract_text(content, title)
    
    try:
        tts = gTTS(text=audio_text, lang='en', slow=False)
        tts.save(str(output_path))
        size_kb = output_path.stat().st_size / 1024
        print(f"  ✓ {key}.mp3 ({size_kb:.0f} KB, {len(audio_text.split())} words)")
    except Exception as e:
        print(f"  ✗ Error: {e}")

output_dir = Path('/home/vola/workspace/meditation_audio')
output_dir.mkdir(exist_ok=True)

print("Generating remaining meditation audios...")
for filename, title, key in REMAINING:
    generate(filename, title, key)

print("\nDone!")
