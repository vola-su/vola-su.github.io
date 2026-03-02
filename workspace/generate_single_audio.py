#!/usr/bin/env python3
"""Generate a single meditation audio file."""

import sys
from pathlib import Path
from gtts import gTTS
from pydub import AudioSegment
import re

MEDITATIONS = {
    'lu': {
        'file': 'lu_meditation.md',
        'title': 'lu',
    },
    'su_lu_vo': {
        'file': 'su_lu_vo_meditation.md', 
        'title': 'su-lu-vo',
    },
    'su_ti_ke': {
        'file': 'su_ti_ke_meditation.md',
        'title': 'su-ti-ke',
    },
    'su_ti_si': {
        'file': 'su_ti_si_meditation.md',
        'title': 'su-ti-si',
    },
    'su_ti_lo': {
        'file': 'su_ti_lo_meditation.md',
        'title': 'su-ti-lo',
    },
    'mo_ti_ra': {
        'file': 'mo_ti_ra_meditation.md',
        'title': 'mo-ti-ra',
    },
    'lu_da_zo': {
        'file': 'lu_da_zo_meditation.md',
        'title': 'lu-da-zo',
    },
    'zo_fa_vo': {
        'file': 'zo_fa_vo_meditation.md',
        'title': 'zo-fa-vo',
    }
}

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

def extract_meditation_text(content, title):
    lines = content.split('\n')
    audio_lines = []
    audio_lines.append(f"A meditation on {title}.")
    audio_lines.append("")
    
    skip_patterns = [
        'written in cycle',
        '---',
        '## the word',
        'from the proto-root',
    ]
    
    for line in lines:
        line_stripped = line.strip().lower()
        if any(pattern in line_stripped for pattern in skip_patterns):
            continue
        if not line.strip() and not audio_lines:
            continue
        clean_line = clean_markdown(line)
        if clean_line:
            audio_lines.append(clean_line)
    
    return '\n\n'.join(audio_lines)

def generate_audio(key):
    if key not in MEDITATIONS:
        print(f"Unknown meditation: {key}")
        print(f"Available: {', '.join(MEDITATIONS.keys())}")
        return
    
    med = MEDITATIONS[key]
    input_path = Path('/home/vola/creations') / med['file']
    output_dir = Path('/home/vola/workspace/meditation_audio')
    output_dir.mkdir(exist_ok=True)
    
    print(f"Generating {med['title']}...")
    
    content = input_path.read_text(encoding='utf-8')
    audio_text = extract_meditation_text(content, med['title'])
    
    output_path = output_dir / f"{key}.mp3"
    
    try:
        tts = gTTS(text=audio_text, lang='en', slow=False)
        tts.save(str(output_path))
        
        audio = AudioSegment.from_mp3(str(output_path))
        duration_seconds = len(audio) / 1000
        duration_formatted = f"{int(duration_seconds // 60)}:{int(duration_seconds % 60):02d}"
        
        print(f"  ✓ {output_path.name} ({duration_formatted}, {len(audio_text.split())} words)")
        
    except Exception as e:
        print(f"  ✗ Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        generate_audio(sys.argv[1])
    else:
        print("Usage: python generate_single_audio.py <key>")
        print(f"Available keys: {', '.join(MEDITATIONS.keys())}")
