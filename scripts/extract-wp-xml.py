#!/usr/bin/env python3
"""
Extract WordPress content from XML export file.
Outputs posts/pages as Markdown files for Hugo.
"""

import xml.etree.ElementTree as ET
import re
import os
import html
from datetime import datetime

XML_FILE = "/Users/monique/Projecten/carottesgrillees/reference/carottesgrilles.WordPress.2025-12-06.xml"
OUTPUT_DIR = "/Users/monique/Projecten/carottesgrillees/content-export"

# WordPress XML namespaces
NAMESPACES = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'wp': 'http://wordpress.org/export/1.2/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    'dc': 'http://purl.org/dc/elements/1.1/',
}

def get_text(element, path, default=''):
    """Get text from an element, handling CDATA."""
    el = element.find(path, NAMESPACES)
    if el is not None and el.text:
        return el.text.strip()
    return default

def html_to_markdown(html_content):
    """Convert HTML to Markdown."""
    if not html_content:
        return ""

    content = html_content

    # Paragraphs
    content = re.sub(r'<p[^>]*>', '\n\n', content)
    content = re.sub(r'</p>', '', content)

    # Line breaks
    content = re.sub(r'<br\s*/?>', '\n', content)

    # Headers
    for i in range(6, 0, -1):
        content = re.sub(f'<h{i}[^>]*>', '\n\n' + '#' * i + ' ', content)
        content = re.sub(f'</h{i}>', '\n\n', content)

    # Images - extract and simplify URLs (do this BEFORE italic/em to avoid <img matching <i)
    from urllib.parse import unquote

    def fix_image_url(match):
        full_tag = match.group(0)
        # Extract src - try both quote styles
        src_match = re.search(r'src="([^"]*)"', full_tag)
        if not src_match:
            src_match = re.search(r"src='([^']*)'", full_tag)
        if not src_match:
            return ''
        url = src_match.group(1)
        # URL decode the filename, then re-encode spaces for markdown
        filename = unquote(url.split('/')[-1])
        # Replace spaces with %20 for valid URLs in markdown
        filename_encoded = filename.replace(' ', '%20')
        # Extract alt if present
        alt_match = re.search(r'alt="([^"]*)"', full_tag)
        if not alt_match:
            alt_match = re.search(r"alt='([^']*)'", full_tag)
        alt = alt_match.group(1) if alt_match else ''
        return f'![{alt}](/images/{filename_encoded})'

    # Match img tags - both self-closing and not
    content = re.sub(r'<img[^>]*/>', fix_image_url, content)
    content = re.sub(r'<img[^>]*>', fix_image_url, content)

    # Bold/Strong
    content = re.sub(r'<(strong|b)[^>]*>', '**', content)
    content = re.sub(r'</(strong|b)>', '**', content)

    # Italic/Em
    content = re.sub(r'<(em|i)[^>]*>', '*', content)
    content = re.sub(r'</(em|i)>', '*', content)

    # Links
    content = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>', r'[\2](\1)', content)

    # Lists
    content = re.sub(r'<ul[^>]*>', '\n', content)
    content = re.sub(r'</ul>', '\n', content)
    content = re.sub(r'<ol[^>]*>', '\n', content)
    content = re.sub(r'</ol>', '\n', content)
    content = re.sub(r'<li[^>]*>', '- ', content)
    content = re.sub(r'</li>', '\n', content)

    # Blockquote
    content = re.sub(r'<blockquote[^>]*>', '\n> ', content)
    content = re.sub(r'</blockquote>', '\n', content)

    # Pre/Code
    content = re.sub(r'<pre[^>]*>', '\n```\n', content)
    content = re.sub(r'</pre>', '\n```\n', content)
    content = re.sub(r'<code[^>]*>', '`', content)
    content = re.sub(r'</code>', '`', content)

    # Divs and spans (remove)
    content = re.sub(r'<div[^>]*>', '\n', content)
    content = re.sub(r'</div>', '\n', content)
    content = re.sub(r'<span[^>]*>', '', content)
    content = re.sub(r'</span>', '', content)

    # Non-breaking space
    content = content.replace('&nbsp;', ' ')

    # Decode HTML entities
    content = html.unescape(content)

    # Remove remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Clean up whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()

    return content

def sanitize_filename(s):
    """Create a safe filename from a string."""
    s = re.sub(r'[<>:"/\\|?*]', '', s)
    s = re.sub(r'\s+', '-', s)
    s = s.lower()
    s = re.sub(r'-+', '-', s)
    s = s.strip('-')
    return s[:50]

def create_markdown_file(item, output_dir):
    """Create a Markdown file from a WordPress item."""

    title = get_text(item, 'title')
    content = get_text(item, 'content:encoded')
    slug = get_text(item, 'wp:post_name')
    date_str = get_text(item, 'wp:post_date')
    status = get_text(item, 'wp:status')
    post_type = get_text(item, 'wp:post_type')
    post_id = get_text(item, 'wp:post_id')

    # Skip if no content
    if not content and not title:
        return None

    # Parse date
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        date_formatted = date.strftime('%Y-%m-%d')
    except:
        date_formatted = '2010-01-01'

    # Create slug if missing
    if not slug:
        slug = sanitize_filename(title) if title else f'post-{post_id}'

    # Convert content
    markdown_content = html_to_markdown(content)

    # Determine if this is a poem (short lines, specific formatting)
    is_poem = False
    if markdown_content:
        lines = markdown_content.split('\n')
        non_empty = [l for l in lines if l.strip()]
        if non_empty:
            avg_line_length = sum(len(l) for l in non_empty) / len(non_empty)
            if avg_line_length < 60 and len(non_empty) > 3:
                is_poem = True

    # Create frontmatter
    safe_title = (title or 'Untitled').replace('"', '\\"').replace('\n', ' ')

    frontmatter = f"""---
title: "{safe_title}"
date: {date_str}
slug: "{slug}"
draft: {str(status != 'publish').lower()}
original_id: {post_id}
type: "{'poem' if is_poem else 'prose'}"
---

{markdown_content}
"""

    # Create filename
    filename = f"{date_formatted}-{slug}.md"

    # Determine subdirectory
    subdir = 'page' if post_type == 'page' else 'post'

    full_dir = os.path.join(output_dir, subdir)
    os.makedirs(full_dir, exist_ok=True)

    filepath = os.path.join(full_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter)

    return filepath, title, is_poem

def main():
    print("Parsing WordPress XML export...")

    tree = ET.parse(XML_FILE)
    root = tree.getroot()

    channel = root.find('channel')
    items = channel.findall('item')

    print(f"Found {len(items)} items")

    # Count by type
    types = {}
    for item in items:
        t = get_text(item, 'wp:post_type')
        types[t] = types.get(t, 0) + 1
    print(f"By type: {types}")

    # Process pages (the actual content)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    created = 0
    poems = 0
    prose = 0

    for item in items:
        post_type = get_text(item, 'wp:post_type')
        status = get_text(item, 'wp:status')

        # Only process published pages
        if post_type != 'page':
            continue

        result = create_markdown_file(item, OUTPUT_DIR)
        if result:
            filepath, title, is_poem = result
            created += 1
            if is_poem:
                poems += 1
            else:
                prose += 1
            indicator = "📜" if is_poem else "📖"
            title_short = (title or 'Untitled')[:40]
            print(f"  {indicator} {os.path.basename(filepath)}: {title_short}")

    print(f"\n✅ Done!")
    print(f"   Created: {created} markdown files")
    print(f"   Poems: {poems}")
    print(f"   Prose: {prose}")
    print(f"   Location: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
