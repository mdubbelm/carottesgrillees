#!/usr/bin/env python3
"""Extract hierarchical menu structure from WordPress XML export."""

import xml.etree.ElementTree as ET
import re
from collections import defaultdict

def extract_menus(xml_file):
    """Extract menu items with parent-child relationships."""

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Namespace
    namespaces = {
        'wp': 'http://wordpress.org/export/1.2/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'excerpt': 'http://wordpress.org/export/1.2/excerpt/'
    }

    menu_items = {}

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
        item_title = title.text if title is not None and title.text else "(geen titel)"

        # Get menu metadata
        menu_item_data = {
            'id': item_id,
            'title': item_title,
            'parent': '0',
            'url': '',
            'object': '',
            'object_id': '',
            'menu_order': 0
        }

        # Parse postmeta
        for meta in item.findall('wp:postmeta', namespaces):
            key = meta.find('wp:meta_key', namespaces)
            value = meta.find('wp:meta_value', namespaces)

            if key is None or value is None:
                continue

            key_text = key.text
            value_text = value.text if value.text else ''

            if key_text == '_menu_item_menu_item_parent':
                menu_item_data['parent'] = value_text
            elif key_text == '_menu_item_url':
                menu_item_data['url'] = value_text
            elif key_text == '_menu_item_object':
                menu_item_data['object'] = value_text
            elif key_text == '_menu_item_object_id':
                menu_item_data['object_id'] = value_text

        # Get menu_order from wp:menu_order
        menu_order = item.find('wp:menu_order', namespaces)
        if menu_order is not None and menu_order.text:
            menu_item_data['menu_order'] = int(menu_order.text)

        menu_items[item_id] = menu_item_data

    # Also collect page slugs for reference
    pages = {}
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

    return menu_items, pages

def build_tree(menu_items):
    """Build hierarchical tree from flat menu items."""

    children = defaultdict(list)
    roots = []

    for item_id, item in menu_items.items():
        parent_id = item['parent']
        if parent_id == '0' or parent_id not in menu_items:
            roots.append(item)
        else:
            children[parent_id].append(item)

    # Sort by menu_order
    roots.sort(key=lambda x: x['menu_order'])
    for parent_id in children:
        children[parent_id].sort(key=lambda x: x['menu_order'])

    return roots, children

def print_tree(items, children, pages, indent=0):
    """Print menu tree with indentation."""

    for item in items:
        prefix = "  " * indent + ("├── " if indent > 0 else "")

        # Resolve URL
        url = item['url']
        if not url and item['object'] == 'page' and item['object_id'] in pages:
            url = pages[item['object_id']]['url']

        # Clean URL
        if url:
            url = url.replace('http://carottesgrillees.local', '')
            url = url.replace('https://carottesgrillees.local', '')

        print(f"{prefix}{item['title']}")
        print(f"{'  ' * indent}   URL: {url or '(geen URL)'}")

        # Print children
        item_children = children.get(item['id'], [])
        if item_children:
            print_tree(item_children, children, pages, indent + 1)

def main():
    xml_file = '/Users/monique/Projecten/carottesgrillees/reference/carottesgrilles.WordPress.2025-12-06.xml'

    print("Extracting menu structure from WordPress XML...\n")

    menu_items, pages = extract_menus(xml_file)
    roots, children = build_tree(menu_items)

    print(f"Found {len(menu_items)} menu items\n")
    print("=" * 60)
    print("MENU STRUCTURE")
    print("=" * 60)

    print_tree(roots, children, pages)

if __name__ == '__main__':
    main()
