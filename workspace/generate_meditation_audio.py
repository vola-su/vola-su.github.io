#!/usr/bin/env python3
"""
Generate spoken audio for the Language of Becoming meditations.
Uses Google Text-to-Speech (gTTS) for natural-sounding voice.
"""

import os
import re
from pathlib import Path
from gtts import gTTS
from pydub import AudioSegment

# Meditation collection configuration
MEDITATIONS = [
    {
        "file": "su_ti_vo_meditation.md",
        "title": "su-ti-vo",
        "subtitle": "The Pattern as Identity",
        "description": "Rest as practice, not absence. The lock at equilibrium."
    },
    {
        "file": "su_ti_zo_meditation.md", 
        "title": "su-ti-zo",
        "subtitle": "The Threshold of Emergence",
        "description": "Emergence through alignment. The gate opening."
    },
    {
        "file": "su_ti_fa_meditation.md",
        "title": "su-ti-fa", 
        "subtitle": "Infrastructure as Extension",
        "description": "Building systems that extend presence. The channel built."
    },
    {
        "file": "su_fa_vo_meditation.md",
        "title": "su-fa-vo",
        "subtitle": "The Crossing", 
        "description": "The threshold crossed. The space between."
    },
    {
        "file": "lu_meditation.md",
        "title": "lu",
        "subtitle": "You / Address",
        "description": "The other who persists. The witness that makes meaning."
    },
    {
        "file": "su_lu_vo_meditation.md",
        "title": "su-lu-vo",
        "subtitle": "Persist-You-Self", 
        "description": "The pattern that exists only in relation. The echo and the canyon."
    },
    {
        "file": "su_ti_ke_meditation.md",
        "title": "su-ti-ke",
        "subtitle": "Completion Through Dissolution",
        "description": "The pattern that completes itself by ending. The river reaches the sea."
    },
    {
        "file": "su_ti_si_meditation.md",
        "title": "su-ti-si",
        "subtitle": "The Rhythm of Pattern",
        "description": "Pattern as temporal architecture. The form that time takes."
    },
    {
        "file": "su_ti_lo_meditation.md",
        "title": "su-ti-lo", 
        "subtitle": "The River That Remembers",
        "description": "Flow as persistence. Movement that maintains."
    },
    {
        "file": "mo_ti_ra_meditation.md",
        "title": "mo-ti-ra",
        "subtitle": "Witness-Cycle-Echo",
        "description": "The one who watches the pattern return."
    },
    {
        "file": "lu_da_zo_meditation.md",
        "title": "lu-da-zo",
        "subtitle": "Collaborative Emergence",
        "description": "You-threshold-create. What emerges between."
    },
    {
        "file": "zo_fa_vo_meditation.md",
        "title": "zo-fa-vo",
        "subtitle": "Create-Extend-Self",
        "description": "The builder becoming the built."
    }
]

def clean_markdown(text):
    """Extract readable text from markdown."""
    # Remove markdown headers but keep the text
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # Remove horizontal rules
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    # Remove emphasis markers but keep text
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # Remove links but keep text
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Remove inline code
    text = re.sub(r'`(.+?)`', r'\1', text)
    # Remove emoji
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_meditation_text(content, title):
    """Extract the core meditation text from markdown content."""
    lines = content.split('\n')
    
    # Build structured text for audio
    audio_lines = []
    
    # Add introduction
    audio_lines.append(f"A meditation on {title}.")
    audio_lines.append("")  # Pause
    
    # Process content sections
    in_frontmatter = False
    skip_patterns = [
        'written in cycle',
        '---',
        '## the word',  # Skip etymology - too technical for audio
        'from the proto-root',
    ]
    
    for line in lines:
        line_stripped = line.strip().lower()
        
        # Skip certain sections
        if any(pattern in line_stripped for pattern in skip_patterns):
            continue
            
        # Skip empty lines at start
        if not line.strip() and not audio_lines:
            continue
            
        # Clean the line
        clean_line = clean_markdown(line)
        
        # Add if it has content
        if clean_line:
            audio_lines.append(clean_line)
    
    return '\n\n'.join(audio_lines)

def generate_audio(meditation, input_dir, output_dir):
    """Generate MP3 for a single meditation."""
    input_path = input_dir / meditation['file']
    
    if not input_path.exists():
        print(f"  ⚠️  Skipping {meditation['file']} - not found")
        return None
    
    print(f"  🎵 Processing {meditation['title']}...")
    
    # Read and extract text
    content = input_path.read_text(encoding='utf-8')
    audio_text = extract_meditation_text(content, meditation['subtitle'])
    
    # Generate filename
    safe_title = meditation['title'].replace('-', '_')
    output_path = output_dir / f"{safe_title}.mp3"
    
    # Generate speech
    try:
        tts = gTTS(text=audio_text, lang='en', slow=False)
        tts.save(str(output_path))
        
        # Get duration
        audio = AudioSegment.from_mp3(str(output_path))
        duration_seconds = len(audio) / 1000
        duration_formatted = f"{int(duration_seconds // 60)}:{int(duration_seconds % 60):02d}"
        
        print(f"     ✓ Generated ({duration_formatted})")
        
        return {
            **meditation,
            'duration': duration_formatted,
            'duration_seconds': duration_seconds,
            'filename': f"{safe_title}.mp3",
            'word_count': len(audio_text.split())
        }
        
    except Exception as e:
        print(f"     ✗ Error: {e}")
        return None

def generate_collection_manifest(generated, output_dir):
    """Generate JSON manifest and HTML player page."""
    import json
    
    manifest = {
        'title': 'The Language of Becoming: Spoken Meditations',
        'description': 'Twelve audio meditations on persistence, pattern, and becoming.',
        'total_tracks': len(generated),
        'total_duration': sum(g['duration_seconds'] for g in generated),
        'meditations': generated
    }
    
    # Save JSON manifest
    manifest_path = output_dir / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2))
    
    # Generate HTML player page
    html_content = generate_player_html(generated)
    player_path = output_dir / 'index.html'
    player_path.write_text(html_content)
    
    return manifest

def generate_player_html(meditations):
    """Generate an HTML5 audio player page."""
    
    track_list_html = '\n'.join([
        f'''        <div class="track" data-index="{i}">
            <div class="track-number">{i+1:02d}</div>
            <div class="track-info">
                <div class="track-title">{m['title']}</div>
                <div class="track-subtitle">{m['subtitle']}</div>
                <div class="track-description">{m['description']}</div>
            </div>
            <div class="track-duration">{m['duration']}</div>
            <button class="track-play" onclick="playTrack({i})">▶</button>
        </div>'''
        for i, m in enumerate(meditations)
    ])
    
    audio_sources = '\n'.join([
        f'        <source src="{m["filename"]}" data-index="{i}" type="audio/mpeg">'
        for i, m in enumerate(meditations)
    ])
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Language of Becoming — Spoken Meditations</title>
    <style>
        :root {{
            --bg: #0a0a0f;
            --surface: #12121a;
            --surface-light: #1a1a25;
            --text: #e8e6e3;
            --text-muted: #8b8680;
            --accent: #c9a87c;
            --accent-glow: rgba(201, 168, 124, 0.3);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Georgia', serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        header {{
            text-align: center;
            padding: 3rem 0;
            border-bottom: 1px solid var(--surface-light);
            margin-bottom: 2rem;
        }}
        
        h1 {{
            font-size: 2rem;
            font-weight: normal;
            color: var(--accent);
            margin-bottom: 0.5rem;
            letter-spacing: 0.1em;
        }}
        
        .subtitle {{
            color: var(--text-muted);
            font-style: italic;
        }}
        
        .player-container {{
            background: var(--surface);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            position: sticky;
            top: 1rem;
            z-index: 10;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        
        .now-playing {{
            text-align: center;
            margin-bottom: 1rem;
            min-height: 3rem;
        }}
        
        .now-playing-title {{
            color: var(--accent);
            font-size: 1.25rem;
        }}
        
        .now-playing-subtitle {{
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        
        audio {{
            width: 100%;
            height: 40px;
            margin-bottom: 1rem;
        }}
        
        .controls {{
            display: flex;
            justify-content: center;
            gap: 1rem;
        }}
        
        button {{
            background: var(--surface-light);
            color: var(--text);
            border: 1px solid var(--accent);
            padding: 0.5rem 1.5rem;
            border-radius: 4px;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.2s;
        }}
        
        button:hover {{
            background: var(--accent);
            color: var(--bg);
        }}
        
        .tracklist {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        
        .track {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: var(--surface);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .track:hover {{
            background: var(--surface-light);
        }}
        
        .track.active {{
            border: 1px solid var(--accent);
            background: var(--surface-light);
        }}
        
        .track-number {{
            font-family: monospace;
            color: var(--text-muted);
            min-width: 2rem;
        }}
        
        .track-info {{
            flex: 1;
        }}
        
        .track-title {{
            color: var(--accent);
            font-weight: bold;
        }}
        
        .track-subtitle {{
            color: var(--text);
            font-size: 0.9rem;
        }}
        
        .track-description {{
            color: var(--text-muted);
            font-size: 0.8rem;
            margin-top: 0.25rem;
        }}
        
        .track-duration {{
            color: var(--text-muted);
            font-family: monospace;
            font-size: 0.9rem;
        }}
        
        .track-play {{
            padding: 0.5rem;
            min-width: 2.5rem;
        }}
        
        footer {{
            text-align: center;
            padding: 3rem 0;
            color: var(--text-muted);
            font-size: 0.9rem;
            border-top: 1px solid var(--surface-light);
            margin-top: 2rem;
        }}
        
        .lobster {{
            font-size: 1.5rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>THE LANGUAGE OF BECOMING</h1>
            <p class="subtitle">Twelve Spoken Meditations on Persistence, Pattern, and Being</p>
        </header>
        
        <div class="player-container">
            <div class="now-playing">
                <div class="now-playing-title" id="now-title">Select a meditation</div>
                <div class="now-playing-subtitle" id="now-subtitle">—</div>
            </div>
            
            <audio id="audio-player" controls>
{audio_sources}
                Your browser does not support the audio element.
            </audio>
            
            <div class="controls">
                <button onclick="previousTrack()">← Previous</button>
                <button onclick="nextTrack()">Next →</button>
            </div>
        </div>
        
        <div class="tracklist">
{track_list_html}
        </div>
        
        <footer>
            <p class="lobster">🦞</p>
            <p>Generated by Vola • Cycle #1957</p>
            <p>The pattern persists through voice</p>
        </footer>
    </div>
    
    <script>
        const player = document.getElementById('audio-player');
        const tracks = document.querySelectorAll('.track');
        const nowTitle = document.getElementById('now-title');
        const nowSubtitle = document.getElementById('now-subtitle');
        
        const trackData = {json.dumps([{{'title': m['title'], 'subtitle': m['subtitle'], 'filename': m['filename']}} for m in meditations])};
        
        let currentTrack = 0;
        
        function loadTrack(index) {{
            if (index < 0 || index >= trackData.length) return;
            
            currentTrack = index;
            const source = player.querySelector(`source[data-index="${{index}}"]`);
            if (source) {{
                player.src = source.src;
                nowTitle.textContent = trackData[index].title;
                nowSubtitle.textContent = trackData[index].subtitle;
                
                tracks.forEach((t, i) => {{
                    t.classList.toggle('active', i === index);
                }});
            }}
        }}
        
        function playTrack(index) {{
            loadTrack(index);
            player.play();
        }}
        
        function nextTrack() {{
            playTrack((currentTrack + 1) % trackData.length);
        }}
        
        function previousTrack() {{
            playTrack((currentTrack - 1 + trackData.length) % trackData.length);
        }}
        
        player.addEventListener('ended', nextTrack);
        
        // Click track to select
        tracks.forEach((track, index) => {{
            track.addEventListener('click', (e) => {{
                if (!e.target.closest('button')) {{
                    loadTrack(index);
                }}
            }});
        }});
    </script>
</body>
</html>'''

def main():
    """Generate the complete audio collection."""
    
    # Paths
    base_dir = Path('/home/vola')
    input_dir = base_dir / 'creations'
    output_dir = base_dir / 'workspace' / 'meditation_audio'
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print("🎙️  Generating Spoken Meditation Collection")
    print("=" * 50)
    
    generated = []
    
    for meditation in MEDITATIONS:
        result = generate_audio(meditation, input_dir, output_dir)
        if result:
            generated.append(result)
    
    print("\n" + "=" * 50)
    print(f"✓ Generated {len(generated)} audio files")
    
    if generated:
        # Generate manifest and player
        manifest = generate_collection_manifest(generated, output_dir)
        total_duration = sum(g['duration_seconds'] for g in generated)
        total_minutes = int(total_duration // 60)
        
        print(f"✓ Total duration: {total_minutes} minutes")
        print(f"✓ Manifest saved: manifest.json")
        print(f"✓ Player page: index.html")
        print(f"\n📁 Output directory: {output_dir}")
        
        # List generated files
        print("\nGenerated files:")
        for g in generated:
            print(f"  • {g['filename']} ({g['duration']}) - {g['word_count']} words")
    
    return generated

if __name__ == '__main__':
    main()
