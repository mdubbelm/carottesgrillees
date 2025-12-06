#!/usr/bin/env python3
"""Generate Hugo menu config from WordPress XML export."""

import xml.etree.ElementTree as ET
from collections import defaultdict

def extract_menus(xml_file):
    """Extract menu items with parent-child relationships."""
    tree = ET.parse(xml_file)
    root = tree.getroot()

    namespaces = {
        'wp': 'http://wordpress.org/export/1.2/',
    }

    menu_items = {}
    pages = {}

    # Collect pages first
    for item in root.findall('.//item'):
        post_type = item.find('wp:post_type', namespaces)
        if post_type is None or post_type.text != 'page':
            continue
        post_id = item.find('wp:post_id', namespaces)
        title = item.find('title')
        link = item.find('link')
        if post_id is None:
            continue
        pages[post_id.text] = {
            'title': title.text if title is not None else '',
            'url': link.text if link is not None else ''
        }

    # Find all nav_menu_items
    for item in root.findall('.//item'):
        post_type = item.find('wp:post_type', namespaces)
        if post_type is None or post_type.text != 'nav_menu_item':
            continue

        post_id = item.find('wp:post_id', namespaces)
        title = item.find('title')

        if post_id is None:
            continue

        item_id = post_id.text
        item_title = title.text if title is not None and title.text else ""

        item_data = {
            'id': item_id,
            'title': item_title,
            'parent': '0',
            'url': '',
            'object': '',
            'object_id': '',
            'menu_order': 0
        }

        for meta in item.findall('wp:postmeta', namespaces):
            key = meta.find('wp:meta_key', namespaces)
            value = meta.find('wp:meta_value', namespaces)
            if key is None or value is None:
                continue
            key_text = key.text
            value_text = value.text if value.text else ''

            if key_text == '_menu_item_menu_item_parent':
                item_data['parent'] = value_text
            elif key_text == '_menu_item_url':
                item_data['url'] = value_text
            elif key_text == '_menu_item_object':
                item_data['object'] = value_text
            elif key_text == '_menu_item_object_id':
                item_data['object_id'] = value_text

        menu_order = item.find('wp:menu_order', namespaces)
        if menu_order is not None and menu_order.text:
            item_data['menu_order'] = int(menu_order.text)

        # Resolve URL from page if needed
        if not item_data['url'] and item_data['object'] == 'page' and item_data['object_id'] in pages:
            item_data['url'] = pages[item_data['object_id']]['url']

        # Get title from page if empty
        if not item_data['title'] and item_data['object'] == 'page' and item_data['object_id'] in pages:
            item_data['title'] = pages[item_data['object_id']]['title']

        menu_items[item_id] = item_data

    return menu_items

def build_tree(menu_items):
    """Build hierarchical tree."""
    children = defaultdict(list)
    roots = []

    for item_id, item in menu_items.items():
        parent_id = item['parent']
        if parent_id == '0' or parent_id not in menu_items:
            roots.append(item)
        else:
            children[parent_id].append(item)

    roots.sort(key=lambda x: x['menu_order'])
    for parent_id in children:
        children[parent_id].sort(key=lambda x: x['menu_order'])

    return roots, children

def clean_url(url):
    """Clean WordPress URL to relative path."""
    url = url.replace('http://carottesgrillees.local', '')
    url = url.replace('https://carottesgrillees.local', '')
    if not url:
        return '/'
    return url

def generate_toml(roots, children, menu_items):
    """Generate TOML menu config."""

    lines = []
    lines.append("baseURL = 'https://carottesgrillees.nl/'")
    lines.append("languageCode = 'nl'")
    lines.append("title = 'Carottes grillées'")
    lines.append("theme = 'carottes'")
    lines.append("")
    lines.append("# Clean URLs")
    lines.append("[permalinks]")
    lines.append("  page = '/:slug/'")
    lines.append("")
    lines.append("# Hierarchische menu's")
    lines.append("")

    # Define the main menu items we want (based on original)
    main_items = [
        ('begin', '/', None),  # Home
    ]

    weight = 1

    def add_menu_item(item, parent_id=None, level=0):
        nonlocal weight

        title = item['title'] if item['title'] else 'untitled'
        url = clean_url(item['url'])

        if not url or url == '/':
            return

        item_id = item['id']
        lines.append("[[menus.main]]")
        lines.append(f"  name = '{title}'")
        lines.append(f"  url = '{url}'")
        lines.append(f"  weight = {weight}")
        if parent_id:
            lines.append(f"  parent = '{parent_id}'")
        lines.append(f"  identifier = 'menu-{item_id}'")
        lines.append("")

        weight += 1

        # Add children
        item_children = children.get(item['id'], [])
        for child in item_children:
            add_menu_item(child, f"menu-{item['id']}", level + 1)

    # Process roots - skip first one (it's home/leeuc which we don't need)
    for root in roots:
        url = clean_url(root['url'])
        # Skip home page and help2 duplicate
        if url in ['/', '/help2/']:
            continue
        add_menu_item(root)

    lines.append("[markup]")
    lines.append("  [markup.goldmark]")
    lines.append("    [markup.goldmark.renderer]")
    lines.append("      unsafe = true")

    return '\n'.join(lines)

def main():
    xml_file = '/Users/monique/Projecten/carottesgrillees/reference/carottesgrilles.WordPress.2025-12-06.xml'

    menu_items = extract_menus(xml_file)
    roots, children = build_tree(menu_items)

    toml_content = generate_toml(roots, children, menu_items)

    output_file = '/Users/monique/Projecten/carottesgrillees/hugo.toml'
    with open(output_file, 'w') as f:
        f.write(toml_content)

    print(f"Generated {output_file}")
    print(f"Total menu items: {len(menu_items)}")

if __name__ == '__main__':
    main()
