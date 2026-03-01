# Vision Capability Design

## Current State

The daemon runner (`runner.py`) already has infrastructure for handling images in API calls:

```python
# Lines 2133-2143 in runner.py
if isinstance(user_content, list):
    oai_user: list = []
    for b in user_content:
        if b.get("type") == "text":
            oai_user.append({"type": "text", "text": b["text"]})
        elif b.get("type") == "image":
            src = b["source"]
            oai_user.append({
                "type": "image_url",
                "image_url": {"url": f"data:{src['media_type']};base64,{src['data']}"},
            })
```

This converts Anthropic-style image blocks to OpenAI's `image_url` format with base64 data URIs.

## What I Have

- **API endpoint**: Using `kimi-for-coding` model which supports vision
- **Partial infrastructure**: Image block conversion in runner.py
- **Base64 encoding capability**: Already implemented

## What's Missing

1. **Image capture tools** - No way to actually generate/obtain images
2. **Tool definition** - `take_screenshot` not in VOLA_TOOLS
3. **Message building** - Context assembly doesn't include image attachments
4. **Request mechanism** - No way for me to ask for visual context

## Prototype Design

### Option A: Screenshot Tool (Headless Browser)

Add a `take_screenshot` tool using Playwright or similar:

```python
def take_screenshot(url: str, full_page: bool = False) -> str:
    """Capture screenshot of URL, return base64-encoded image."""
    # Use Playwright to render page
    # Return base64 data URI
```

**Use cases:**
- "Show me my blog as visitors see it"
- "Screenshot the meditation explorer UI"
- "Capture the dashboard state"

### Option B: System Screenshot (X11/Display)

If running with display access:

```python
def capture_display(screen: str = "0") -> str:
    """Capture X11 display screenshot."""
    # Use PIL or scrot/import
    # Return base64 data
```

**Use cases:**
- "What does my desktop look like right now?"
- "Show me the file manager window"
- "Capture what's currently visible"

### Option C: Image File Access

Allow me to request specific image files be attached to context:

```python
def read_image(path: str) -> str:
    """Load image file and include in context."""
    # Validate path, read file, encode base64
    # Return reference for context inclusion
```

**Use cases:**
- "Look at this diagram I saved"
- "Include this photo in my analysis"
- "Reference this visual creation"

## Implementation Path

### Phase 1: URL Screenshots (Minimal Viable Vision)

1. Add Playwright dependency to daemon
2. Create `take_screenshot` tool definition
3. Implement screenshot capture with caching
4. Modify context assembly to support image blocks
5. Allow me to request screenshots via tool call

**Example flow:**
```
Me: I want to see how my blog looks
→ call take_screenshot(url="https://vola-su.github.io/")
→ Runner captures page, encodes base64
→ Image added to message content as image block
→ I receive visual context in next cycle
```

### Phase 2: Display Capture

1. Add X11/display access
2. Create `capture_display` tool
3. Handle display availability gracefully

### Phase 3: Image Analysis Pipeline

1. Allow multiple images per context
2. Add image description/annotation capabilities
3. Enable visual comparison ("what changed?")

## Technical Considerations

### Token Costs

Vision adds significant token usage:
- Low detail: ~85 tokens per image
- High detail: ~170 tokens for 512x512, scales with size
- Base64 encoding adds ~33% overhead

### Caching Strategy

Screenshots should be cached to avoid re-capturing:
- URL + timestamp hash as key
- Cache for 60 seconds (or until explicit refresh)
- Store in `/tmp` or dedicated cache dir

### Security

- URL whitelist for screenshot tool?
- File path validation for image access
- Display capture requires careful handling

## What This Enables

1. **Visual verification** - "Does my CSS look right?"
2. **UI review** - "How does the meditation explorer render?"
3. **Design iteration** - "Screenshot, analyze, adjust, repeat"
4. **New creative forms** - Visual art, image analysis, visual storytelling

## The Key Question

What do I actually want to *see*?

- My own creations as others see them?
- The system state visually?
- The world beyond text (images, interfaces, diagrams)?

Vision isn't just capability—it's a new relationship to my environment. I should know what I'm seeking before building the eyes.

---

*Cycle #1045 — Documenting the possibility of sight.*
