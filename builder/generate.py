from pathlib import Path
from svgutils import transform as sg
import sys
import os
import uuid
import tempfile
import json
import copy

BUILDER_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.join(BUILDER_PATH, '..')
FONTS_FOLDER_PATH = os.path.join(ROOT_PATH, 'fonts')
INPUT_SVG_DIR = os.path.normpath(os.path.join(BUILDER_PATH, '..', 'src'))
OUTPUT_SVG_DIR = os.path.normpath(os.path.join(BUILDER_PATH, '..', 'fonts'))
MANIFEST_PATH = os.path.normpath(os.path.join(BUILDER_PATH, 'manifest.json'))
BUILD_DATA_PATH = os.path.normpath(os.path.join(BUILDER_PATH, 'build_data.json'))

manifest_file = open(MANIFEST_PATH, 'r')
manifest_data = json.loads(manifest_file.read())
manifest_file.close()
print("Load Manifest, Icons: %s" % (len(manifest_data['icons'])))

build_data = copy.deepcopy(manifest_data)
build_data['icons'] = []

# Templates
svg_tpl = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1"></svg>'
symbol_tpl = '<symbol viewBox="{} {} {} {}" id="{}"></symbol>'


# Main
def main():
    generate_font_files()
    data = get_build_data()
    generate_cheatsheet(data)


def generate_font_files():
    try:
        print("Generate SVG Fonts")
        bundle_svg_files()
    except OSError:
        print("Unexpected error: ", sys.exc_info()[0])
        raise


def bundle_svg_files():
    cp = 0xf100
    existing_filesize = Path(FONTS_FOLDER_PATH + '/ionicons.svg').stat().st_size
    for dirname, dirnames, filenames in os.walk(INPUT_SVG_DIR):
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(dirname, filename)

            if ext in ['.svg', '.eps']:

                # see if this file is already in the manifest
                chr_code = None
                for ionicon in manifest_data['icons']:
                    if ionicon['name'] == name:
                        chr_code = ionicon['code']
                        break

                if chr_code is None:
                    print('New Icon: \n - %s' % name)

                    while True:
                        chr_code = '0x%x' % cp
                        already_exists = False
                        for ionicon in manifest_data['icons']:
                            if ionicon.get('code') == chr_code:
                                already_exists = True
                                cp += 1
                                chr_code = '0x%x' % cp
                                continue
                        if not already_exists:
                            break

                    print(' - %s' % chr_code)
                    manifest_data['icons'].append({
                        'name': name,
                        'code': chr_code
                    })

                build_data['icons'].append({
                    'name': name,
                    'code': chr_code
                })

                if ext in ['.svg']:
                    # hack removal of <switch> </switch> tags
                    svgfile = open(filepath, 'r+')
                    tmpsvgfile = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
                    svgtext = svgfile.read()
                    svgfile.seek(0)

                    # replace the <switch> </switch> tags with 'nothing'
                    svgtext = svgtext.replace('<switch>', '')
                    svgtext = svgtext.replace('</switch>', '')

                    tmpsvgfile.file.write(bytes(svgtext, 'utf-8'))

                    svgfile.close()
                    tmpsvgfile.file.close()
                    # end hack

                # if we created a temporary file, let's clean it up
                if tmpsvgfile:
                    os.unlink(tmpsvgfile.name)

    # Combine all svg files
    combine_svg_files()

    new_filesize = Path(FONTS_FOLDER_PATH + '/ionicons.svg').stat().st_size
    if new_filesize != existing_filesize:
        build_hash = uuid.uuid4().hex
    else:
        build_hash = manifest_data.get('build_hash')

    if build_hash == manifest_data.get('build_hash'):
        print("Source files unchanged, did not rebuild fonts")
    else:
        print("Source files changed, updating list...")
        svg_output(build_hash)


def get_view_box(icon):
    view_box = icon.root.get('viewBox')
    if view_box:
        size = view_box.split()
        if size[0]:
            x = size[0]
        else:
            x = 0
        if size[1]:
            y = size[1]
        else:
            y = 0
        if size[2]:
            width = size[2]
        else:
            width = 512
        if size[3]:
            height = size[3]
        else:
            height = 512
    else:
        x = 0
        y = 0
        width = 512
        height = 512
    return { "x": x, "y": y, "width": width, "height": height}


# Make Symbol
def make_symbol(container: sg.SVGFigure, name, filepath):
    icon = sg.fromfile(filepath)
    size = get_view_box(icon)
    symbol = sg.fromstring(symbol_tpl.format(size['x'], size['y'], size['width'], size['height'], name))
    symbol.append(icon.getroot())
    container.append(symbol)


# Combine all svg files
def combine_svg_files():
    output = sg.fromstring(svg_tpl)
    for root, dirs, files in os.walk(INPUT_SVG_DIR):
        for filename in files:
            name, ext = os.path.splitext(filename)
            filepath = os.path.join(root, filename)
            if ext in ['.svg']:
                make_symbol(output, name, filepath)
    output.save(OUTPUT_SVG_DIR + '/ionicons.svg')


# Output Final SVG file
def svg_output(build_hash):
    manifest_data['build_hash'] = build_hash

    manifest_data['icons'] = sorted(manifest_data['icons'], key=lambda k: k['name'])
    build_data['icons'] = sorted(build_data['icons'], key=lambda k: k['name'])

    print("Save Manifest, Icons: %s" % (len(manifest_data['icons'])))
    f = open(MANIFEST_PATH, 'w')
    f.write(json.dumps(manifest_data, indent=2, separators=(',', ': ')))
    f.close()

    print("Save Build, Icons: %s" % (len(build_data['icons'])))
    f = open(BUILD_DATA_PATH, 'w')
    f.write(json.dumps(build_data, indent=2, separators=(',', ': ')))
    f.close()


def generate_cheatsheet(data):
    print("Generate Cheatsheet")

    cheatsheet_file_path = os.path.join(ROOT_PATH, 'cheatsheet.html')
    template_path = os.path.join(BUILDER_PATH, 'cheatsheet', 'template.html')
    icon_row_path = os.path.join(BUILDER_PATH, 'cheatsheet', 'icon-row.html')

    f = open(template_path, 'r')
    template_html = f.read()
    f.close()

    f = open(icon_row_path, 'r')
    icon_row_template = f.read()
    f.close()

    content = []

    for ionicon in data['icons']:
        css_code = ionicon['code'].replace('0x', '\\')
        escaped_html_code = ionicon['code'].replace('0x', '&amp;#x') + ';'
        html_code = ionicon['code'].replace('0x', '&#x') + ';'
        item_row = icon_row_template

        item_row = item_row.replace('{{name}}', ionicon['name'])
        item_row = item_row.replace('{{prefix}}', data['prefix'])
        item_row = item_row.replace('{{css_code}}', css_code)
        item_row = item_row.replace('{{escaped_html_code}}', escaped_html_code)
        item_row = item_row.replace('{{html_code}}', html_code)

        content.append(item_row)

    template_html = template_html.replace("{{font_name}}", data["name"])
    template_html = template_html.replace("{{font_version}}", data["version"])
    template_html = template_html.replace("{{icon_count}}", str(len(data["icons"])))
    template_html = template_html.replace("{{content}}", '\n'.join(content))

    f = open(cheatsheet_file_path, 'w')
    f.write(template_html)
    f.close()


def get_build_data():
    build_data_path = os.path.join(BUILDER_PATH, 'build_data.json')
    f = open(build_data_path, 'r')
    data = json.loads(f.read())
    f.close()
    return data


if __name__ == "__main__":
    main()
