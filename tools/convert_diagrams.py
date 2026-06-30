#!/usr/bin/env python3
"""Convert Mermaid .mmd files to PNG using Playwright."""
import asyncio
import re
from pathlib import Path
from playwright.async_api import async_playwright

def extract_mermaid(text: str) -> str:
    """Extract mermaid content from markdown file."""
    match = re.search(r'```mermaid\n(.*?)```', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    lines = text.split('\n')
    start = 0
    for i, line in enumerate(lines):
        if line.startswith('```mermaid'):
            start = i + 1
            break
    if start > 0:
        return '\n'.join(lines[start:]).strip()
    return text

def make_html(mmd_content: str) -> str:
    """Create standalone HTML with Mermaid."""
    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False)
    tmp.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body>
<pre class="mermaid">{mmd_content}</pre>
<script>
mermaid.initialize({{startOnLoad: true}});
</script>
</body>
</html>
""")
    tmp.close()
    return tmp.name

async def convert_mmd_to_png(mmd_path: Path, png_path: Path):
    """Convert a single .mmd file to PNG."""
    content = mmd_path.read_text()
    mermaid_content = extract_mermaid(content)
    
    tmp_html_path = make_html(mermaid_content)
    tmp_html = Path(tmp_html_path)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 1000})
        await page.goto(f"file://{tmp_html.resolve()}")
        await page.wait_for_timeout(5000)
        await page.screenshot(path=str(png_path), full_page=False)
        await browser.close()
    
    tmp_html.unlink()
    return png_path

async def convert_all_diagrams(diagrams_dir: Path):
    """Convert all .mmd files in a directory to PNG."""
    results = {}
    for mmd_file in diagrams_dir.glob("*.mmd"):
        png_path = mmd_file.with_suffix('.png')
        try:
            await convert_mmd_to_png(mmd_file, png_path)
            results[mmd_file.stem] = str(png_path)
            print(f"  ✓ {mmd_file.name} → {png_path.name}")
        except Exception as e:
            print(f"  ✗ {mmd_file.name}: {e}")
            results[mmd_file.stem] = None
    return results

if __name__ == "__main__":
    import sys, os
    diagrams_dir = Path(sys.argv[1])
    
    results = {}
    for mmd_file in diagrams_dir.glob("*.mmd"):
        png_path = diagrams_dir / f"{mmd_file.stem}.png"
        try:
            asyncio.run(convert_mmd_to_png(mmd_file, png_path))
            results[mmd_file.stem] = str(png_path)
            print(f"  ✓ {mmd_file.name} → {png_path.name}")
        except PermissionError:
            # Root-owned dir — write to user temp instead
            import tempfile
            tmp_dir = Path(tempfile.mkdtemp())
            tmp_png = tmp_dir / f"{mmd_file.stem}.png"
            asyncio.run(convert_mmd_to_png(mmd_file, tmp_png))
            print(f"  ⚠ {mmd_file.name} → {tmp_png.name} (temp, root-owned dir)")
            results[mmd_file.stem] = str(tmp_png)
        except Exception as e:
            print(f"  ✗ {mmd_file.name}: {e}")
            results[mmd_file.stem] = None
    print(f"\nConverted {sum(1 for v in results.values() if v)}/{len(results)}")