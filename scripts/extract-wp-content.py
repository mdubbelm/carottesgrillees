#!/usr/bin/env python3
"""
Extract WordPress content from SQL dump file.
Outputs posts/pages as Markdown files for Hugo.
"""

import re
import os
import html
from datetime import datetime

SQL_FILE = "/Users/monique/Local Sites/carottesgrillees/app/sql/local.sql"
OUTPUT_DIR = "/Users/monique/Projecten/carottesgrillees/content-export"

def unescape_sql_string(s):
    """Unescape SQL string content."""
    if not s:
        return ""
    # Remove surrounding quotes if present
    s = s.strip()
    if s.startswith("'") and s.endswith("'"):
        s = s[1:-1]
    # Unescape common sequences
    s = s.replace("\\'", "'")
    s = s.replace('\\"', '"')
    s = s.replace("\\n", "\n")
    s = s.replace("\\r", "")
    s = s.replace("\\t", "\t")
    s = s.replace("\\\\", "\\")
    # Decode HTML entities
    s = html.unescape(s)
    return s

def parse_wp_posts_line(line):
    """Parse a single INSERT INTO wp_posts VALUES line."""
    # Extract the values part
    match = re.search(r"INSERT INTO `wp_posts` VALUES \((.+)\);?$", line)
    if not match:
        return None

    values = match.group(1)

    # Parse fields - this is tricky due to escaped quotes in content
    fields = []
    current = ""
    in_string = False
    i = 0

    while i < len(values):
        char = values[i]

        # Handle escape sequences
        if char == '\\' and i + 1 < len(values):
            current += char + values[i + 1]
            i += 2
            continue

        # Handle string boundaries
        if char == "'":
            if not in_string:
                in_string = True
                i += 1
                continue
            else:
                # Check if this is end of string or escaped quote
                if i + 1 < len(values) and values[i + 1] == "'":
                    # Escaped quote ''
                    current += "'"
                    i += 2
                    continue
                else:
                    in_string = False
                    i += 1
                    continue

        # Handle field separator
        if char == ',' and not in_string:
            fields.append(current)
            current = ""
            i += 1
            continue

        current += char
        i += 1

    # Don't forget the last field
    fields.append(current)

    # WordPress wp_posts columns:
    # 0: ID, 1: post_author, 2: post_date, 3: post_date_gmt,
    # 4: post_content, 5: post_title, 6: post_excerpt, 7: post_status,
    # 8: comment_status, 9: ping_status, 10: post_password, 11: post_name (slug),
    # 12: to_ping, 13: pinged, 14: post_modified, 15: post_modified_gmt,
    # 16: post_content_filtered, 17: post_parent, 18: guid, 19: menu_order,
    # 20: post_type, 21: post_mime_type, 22: comment_count

    if len(fields) < 21:
        return None

    return {
        'id': fields[0],
        'author': fields[1],
        'date': unescape_sql_string(fields[2]),
        'date_gmt': unescape_sql_string(fields[3]),
        'content': unescape_sql_string(fields[4]),
        'title': unescape_sql_string(fields[5]),
        'excerpt': unescape_sql_string(fields[6]),
        'status': unescape_sql_string(fields[7]),
        'slug': unescape_sql_string(fields[11]),
        'post_parent': fields[17],
        'post_type': unescape_sql_string(fields[20]),
    }

def html_to_markdown(html_content):
    """Basic HTML to Markdown conversion."""
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

    # Bold/Strong
    content = re.sub(r'<(strong|b)[^>]*>', '**', content)
    content = re.sub(r'</(strong|b)>', '**', content)

    # Italic/Em
    content = re.sub(r'<(em|i)[^>]*>', '*', content)
    content = re.sub(r'</(em|i)>', '*', content)

    # Links
    content = re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>', r'[\2](\1)', content)

    # Images
    content = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>', r'![\2](\1)', content)
    content = re.sub(r'<img[^>]*src=["\']([^"\']*)["\'][^>]*/?>', r'![](\1)', content)

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

    # Remove remaining HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Clean up whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()

    return content

def sanitize_filename(s):
    """Create a safe filename from a string."""
    # Remove/replace problematic characters
    s = re.sub(r'[<>:"/\\|?*]', '', s)
    s = re.sub(r'\s+', '-', s)
    s = s.lower()
    s = re.sub(r'-+', '-', s)
    s = s.strip('-')
    return s[:50]  # Limit length

def create_markdown_file(post, output_dir):
    """Create a Markdown file for a post."""

    # Skip if no title and no content
    if not post['title'] and not post['content']:
        return None

    title = post['title'] if post['title'] else 'Untitled'

    # Parse date
    try:
        date = datetime.strptime(post['date'], '%Y-%m-%d %H:%M:%S')
        date_str = date.strftime('%Y-%m-%d')
    except:
        date_str = '2010-01-01'

    # Create slug
    slug = post['slug'] if post['slug'] else sanitize_filename(title)

    # Filename
    filename = f"{date_str}-{slug}.md"

    # Convert content
    content = html_to_markdown(post['content'])

    # Create frontmatter
    safe_title = title.replace('"', '\\"').replace('\n', ' ')
    frontmatter = f"""---
title: "{safe_title}"
date: {post['date']}
slug: "{slug}"
draft: false
original_id: {post['id']}
---

{content}
"""

    # Determine subdirectory based on post type
    subdir = post['post_type'] if post['post_type'] in ['post', 'page'] else 'other'

    # Create directory
    full_dir = os.path.join(output_dir, subdir)
    os.makedirs(full_dir, exist_ok=True)

    # Write file
    filepath = os.path.join(full_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter)

    return filepath

def main():
    print("Reading SQL file...")

    posts = []

    with open(SQL_FILE, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if "INSERT INTO `wp_posts` VALUES" in line:
                post = parse_wp_posts_line(line.strip())
                if post:
                    posts.append(post)

    print(f"Found {len(posts)} records")

    # Show post type distribution
    types = {}
    for p in posts:
        t = p['post_type']
        types[t] = types.get(t, 0) + 1
    print(f"Post types: {types}")

    # Filter for published posts and pages
    published = [p for p in posts if p['status'] == 'publish' and p['post_type'] in ['post', 'page']]
    print(f"Published posts/pages: {len(published)}")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Export each post
    created = 0
    for post in published:
        filepath = create_markdown_file(post, OUTPUT_DIR)
        if filepath:
            created += 1
            title_preview = post['title'][:50] if post['title'] else '(no title)'
            print(f"  {os.path.basename(filepath)}: {title_preview}")

    print(f"\nDone! Created {created} markdown files in {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
