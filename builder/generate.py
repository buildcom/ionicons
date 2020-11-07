from subprocess import call
import sys
import os
import random
import svgwrite
import tempfile
import json
import copy

BUILDER_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.join(BUILDER_PATH, '..')
FONTS_FOLDER_PATH = os.path.join(ROOT_PATH, 'fonts')
CSS_FOLDER_PATH = os.path.join(ROOT_PATH, 'css')
SCSS_FOLDER_PATH = os.path.join(ROOT_PATH, 'scss')
LESS_FOLDER_PATH = os.path.join(ROOT_PATH, 'less')

INPUT_SVG_DIR = os.path.join(BUILDER_PATH, '..', '..', 'src')
OUTPUT_FONT_DIR = os.path.join(BUILDER_PATH, '..', '..', 'fonts')
MANIFEST_PATH = os.path.join(BUILDER_PATH, '..', 'manifest.json')
BUILD_DATA_PATH = os.path.join(BUILDER_PATH, '..', 'build_data.json')

manifest_file = open(MANIFEST_PATH, 'r')
manifest_data = json.loads(manifest_file.read())
manifest_file.close()
print("Load Manifest, Icons: %s" % (len(manifest_data['icons'])))

build_data = copy.deepcopy(manifest_data)
build_data['icons'] = []

def main():
    generate_font_files()
    data = get_build_data()
    rename_svg_glyph_names(data)
    generate_scss(data)
    generate_less(data)
    generate_cheatsheet(data)
    generate_component_json(data)
    generate_composer_json(data)
    generate_bower_json(data)


def generate_font_files():
    print("Generate SVG Fonts")
    try:
        bundle_svg_files()
    except OSError:
        print("Unexpected error: ", sys.exc_info()[0])
        raise


def bundle_svg_files():
    cp = 0xf100
    glyphs = []
    font_name = manifest_data['name']
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

                    filepath = tmpsvgfile.name
                    # end hack

                # Fixme with svgwrite library
                # glyphs.append(svgwrite.)
                # glyph = f.createChar(int(chr_code, 16))
                # glyph.importOutlines(filepath)

                # if we created a temporary file, let's clean it up
                if tmpsvgfile:
                    os.unlink(tmpsvgfile.name)

        font_file = '%s/ionicons' % OUTPUT_FONT_DIR

    # FIXME: Hash has to be calculated depending on possible changes.
    build_hash = hex(random.getrandbits(128))

    if build_hash == manifest_data.get('build_hash'):
        print("Source files unchanged, did not rebuild fonts")
    else:
        svg_output(build_hash, glyphs, font_name, font_file)

# Output Compiled SVG file
def svg_output(build_hash, glyph, font_name, font_file):
    manifest_data['build_hash'] = build_hash

    # Perform SVG header modification for webkit
    svgfile = open(font_file + '.svg', 'r+')
    svgtext = svgfile.read()
    svgfile.seek(0)
    svgfile.write(svgtext.replace('''<svg>''', '''<svg xmlns="http://www.w3.org/2000/svg">'''))

    # FIXME: with svgwrite compile glyphs and inject them in
    # font.fontName = font_name
    # font.familyName = font_name
    # font.fullname = font_name
    # font.generate(font_file + '.svg')

    svgfile.close()

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


def rename_svg_glyph_names(data):
    # hacky and slow (but safe) way to rename glyph-name attributes
    svg_path = os.path.join(FONTS_FOLDER_PATH, 'ionicons.svg')
    svg_file = open(svg_path, 'r+')
    svg_text = svg_file.read()
    svg_file.seek(0)

    for ionicon in data['icons']:
        # uniF2CA
        org_name = 'uni%s' % (ionicon['code'].replace('0x', '').upper())
        ion_name = 'ion-%s' % (ionicon['name'])
        svg_text = svg_text.replace(org_name, ion_name)

    svg_file.write(svg_text)
    svg_file.close()


def generate_less(data):
    print("Generate LESS")
    fontName = data['name']
    font_version = data['version']
    css_prefix = data['prefix']
    variables_file_path = os.path.join(LESS_FOLDER_PATH, '_ionicons-variables.less')
    icons_file_path = os.path.join(LESS_FOLDER_PATH, '_ionicons-icons.less')

    d = []
    d.append('/*!');
    d.append('Ionicons, v%s' % (font_version));
    d.append('Created by Ben Sperry for the Ionic Framework, http://ionicons.com/');
    d.append('https://twitter.com/benjsperry  https://twitter.com/ionicframework');
    d.append('MIT License: https://github.com/driftyco/ionicons');
    d.append('*/');
    d.append('// Ionicons Variables')
    d.append('// --------------------------\n')
    d.append('@ionicons-font-path: "../fonts";')
    d.append('@ionicons-font-family: "%s";' % (fontName))
    d.append('@ionicons-version: "%s";' % (font_version))
    d.append('@ionicons-prefix: %s;' % (css_prefix))
    d.append('')
    for ionicon in data['icons']:
        chr_code = ionicon['code'].replace('0x', '\\')
        d.append('@ionicon-var-%s: "%s";' % (ionicon['name'], chr_code))
    f = open(variables_file_path, 'w')
    f.write('\n'.join(d))
    f.close()

    d = []
    d.append('// Ionicons Icons')
    d.append('// --------------------------\n')

    group = ['.%s' % (data['name'].lower())]
    for ionicon in data['icons']:
        group.append('.@{ionicons-prefix}%s:before' % (ionicon['name']))

    d.append(',\n'.join(group))

    d.append('{')
    d.append('  &:extend(.ion);')
    d.append('}')

    for ionicon in data['icons']:
        chr_code = ionicon['code'].replace('0x', '\\')
        d.append('.@{ionicons-prefix}%s:before { content: @ionicon-var-%s; }' % (ionicon['name'], ionicon['name']))

    f = open(icons_file_path, 'w')
    f.write('\n'.join(d))
    f.close()


def generate_scss(data):
    print("Generate SCSS")
    font_name = data['name']
    font_version = data['version']
    css_prefix = data['prefix']
    variables_file_path = os.path.join(SCSS_FOLDER_PATH, '_ionicons-variables.scss')
    icons_file_path = os.path.join(SCSS_FOLDER_PATH, '_ionicons-icons.scss')

    d = []
    d.append('// Ionicons Variables')
    d.append('// --------------------------\n')
    d.append('$ionicons-font-path: "../fonts" !default;')
    d.append('$ionicons-font-family: "%s" !default;' % (font_name))
    d.append('$ionicons-version: "%s" !default;' % (font_version))
    d.append('$ionicons-prefix: %s !default;' % (css_prefix))
    d.append('')
    for ionicon in data['icons']:
        chr_code = ionicon['code'].replace('0x', '\\')
        d.append('$ionicon-var-%s: "%s";' % (ionicon['name'], chr_code))
    f = open(variables_file_path, 'w')
    f.write('\n'.join(d))
    f.close()

    d = []
    d.append('// Ionicons Icons')
    d.append('// --------------------------\n')

    group = ['.%s' % (data['name'].lower())]
    for ionicon in data['icons']:
        group.append('.#{$ionicons-prefix}%s:before' % (ionicon['name']))

    d.append(',\n'.join(group))

    d.append('{')
    d.append('  @extend .ion;')
    d.append('}')

    for ionicon in data['icons']:
        chr_code = ionicon['code'].replace('0x', '\\')
        d.append('.#{$ionicons-prefix}%s:before { content: $ionicon-var-%s; }' % (ionicon['name'], ionicon['name']))

    f = open(icons_file_path, 'w')
    f.write('\n'.join(d))
    f.close()

    generate_css_from_scss(data)


def generate_css_from_scss(data):
    print("Generate CSS From SCSS")

    scss_file_path = os.path.join(SCSS_FOLDER_PATH, 'ionicons.scss')
    css_file_path = os.path.join(CSS_FOLDER_PATH, 'ionicons.css')
    css_min_file_path = os.path.join(CSS_FOLDER_PATH, 'ionicons.min.css')

    cmd = "sass %s %s --style compact" % (scss_file_path, css_file_path)
    call(cmd, shell=True)

    print("Generate Minified CSS From SCSS")
    cmd = "sass %s %s --style compressed" % (scss_file_path, css_min_file_path)
    call(cmd, shell=True)


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


def generate_component_json(data):
    print("Generate component.json")
    d = {
        "name": data['name'],
        "repo": "driftyco/ionicons",
        "description": "The premium icon font for Ionic Framework.",
        "version": data['version'],
        "keywords": [],
        "dependencies": {},
        "development": {},
        "license": "MIT",
        "styles": [
            "css/%s.css" % (data['name'].lower())
        ],
        "fonts": [
            "fonts/%s.eot" % (data['name'].lower()),
            "fonts/%s.svg" % (data['name'].lower()),
            "fonts/%s.ttf" % (data['name'].lower()),
            "fonts/%s.woff" % (data['name'].lower())
        ]
    }
    txt = json.dumps(d, indent=4, separators=(',', ': '))

    component_file_path = os.path.join(ROOT_PATH, 'component.json')
    f = open(component_file_path, 'w')
    f.write(txt)
    f.close()


def generate_composer_json(data):
    print("Generate composer.json")
    d = {
        "name": "driftyco/ionicons",
        "description": "The premium icon font for Ionic Framework.",
        "keywords": ["fonts", "icon font", "icons", "ionic", "web font"],
        "homepage": "http://ionicons.com/",
        "authors": [
            {
                "name": "Ben Sperry",
                "email": "ben@drifty.com",
                "role": "Designer",
                "homepage": "https://twitter.com/benjsperry"
            },
            {
                "name": "Adam Bradley",
                "email": "adam@drifty.com",
                "role": "Developer",
                "homepage": "https://twitter.com/adamdbradley"
            },
            {
                "name": "Max Lynch",
                "email": "max@drifty.com",
                "role": "Developer",
                "homepage": "https://twitter.com/maxlynch"
            }
        ],
        "extra": {},
        "license": ["MIT"]
    }
    txt = json.dumps(d, indent=4, separators=(',', ': '))

    composer_file_path = os.path.join(ROOT_PATH, 'composer.json')
    f = open(composer_file_path, 'w')
    f.write(txt)
    f.close()


def generate_bower_json(data):
    print("Generate bower.json")
    d = {
        "name": data['name'],
        "version": data['version'],
        "homepage": "https://github.com/driftyco/ionicons",
        "authors": [
            "Ben Sperry <ben@drifty.com>",
            "Adam Bradley <adam@drifty.com>",
            "Max Lynch <max@drifty.com>"
        ],
        "description": "Ionicons - free and beautiful icons from the creators of Ionic Framework",
        "main": [
            "css/%s.css" % (data['name'].lower()),
            "fonts/*"
        ],
        "keywords": ["fonts", "icon font", "icons", "ionic", "web font"],
        "license": "MIT",
        "ignore": [
            "**/.*",
            "builder",
            "node_modules",
            "bower_components",
            "test",
            "tests"
        ]
    }
    txt = json.dumps(d, indent=4, separators=(',', ': '))

    bower_file_path = os.path.join(ROOT_PATH, 'bower.json')
    f = open(bower_file_path, 'w')
    f.write(txt)
    f.close()


def get_build_data():
    build_data_path = os.path.join(BUILDER_PATH, 'build_data.json')
    f = open(build_data_path, 'r')
    data = json.loads(f.read())
    f.close()
    return data


if __name__ == "__main__":
    main()
