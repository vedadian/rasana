import os
import re
import json
import shutil
from glob import glob
from typing import Callable
from bs4 import BeautifulSoup as bs4
from .markdown import render as render_markdown, get_stylesheet as get_markdown_stylesheet
from .js import minify_css, minify_js, compile_ejs_template

HOME_DIRECTORY = os.path.expanduser("~")

def get_file_contents(file_path: str) -> str:
    with open(file_path) as f:
        return f.read()

def build(website_path: str, output_path: str, base_url: str) -> None:
    blog_specs_json = os.path.join(website_path, 'website.json')
    if not os.path.isfile(blog_specs_json):
        raise Exception(f'No `blog.json` file found in `{website_path}`')
    with open(blog_specs_json) as f:
        website_specs = json.load(f)
    if 'theme' not in website_specs:
        raise Exception(f'No theme specified in `{blog_specs_json}`')
    def find_theme(theme: str) -> dict:
        theme_specs_json = os.path.join('./themes', theme, 'theme.json')
        if os.path.isfile(theme_specs_json):
            with open(theme_specs_json) as f:
                result = json.load(f)
                result['base_path'] = os.path.join('./themes', theme)
            return result
        theme_specs_json = os.path.join(HOME_DIRECTORY, '.rasana/themes', theme, 'theme.json')
        if os.path.isfile(theme_specs_json):
            with open(theme_specs_json) as f:
                result = json.load(f)
                result['base_path'] = os.path.join(HOME_DIRECTORY, '.rasana/themes', theme)
            return result
        return None
    theme_specs = find_theme(website_specs['theme'])
    if theme_specs is None:
        raise Exception(f'Could not find the theme named `{website_specs["theme"]}`')
    if ('templates' not in theme_specs) or ('default' not in theme_specs['templates']):
        raise Exception(f'Every theme must contain a default template')
    if 'contents' not in website_specs:
        raise Exception(f'No base path for contents were provided')
    def gather_contents(base_path: str, parent_specs) -> dict:
        items = {}
        for child_path in glob(f'{base_path}/*/'):
            child_path = child_path[:-1]
            item = os.path.basename(child_path)
            if 'resources' in parent_specs and\
               os.path.basename(item) in parent_specs['resources']:
                continue
            items[item] = {}
            item_specs = {}
            item_specs_json = os.path.join(child_path, 'item.json')
            if os.path.isfile(item_specs_json):
                with open(item_specs_json) as f:
                    items[item]['specs'] = item_specs = json.load(f)
            children = gather_contents(child_path, item_specs)
            if children is not None:
                items[item]['children'] = children
        return items or None
    items = {
        'children': gather_contents(
            os.path.join(website_path, website_specs['contents']),
            {}
        )
    }
    additional_stylesheets = {}
    if 'additional_stylesheets' in website_specs:
        additional_stylesheets = {\
            var_name: get_file_contents(file_path)\
            for var_name, file_path in\
            website_specs['additional_stylesheets'].items()\
        }
    def get_template_renderer(template_name: str) -> Callable:
        if template_name not in get_template_renderer.__templates:
            with open(os.path.join(theme_specs['base_path'], theme_specs['templates'][template_name])) as f:
                get_template_renderer.__templates[template_name] = compile_ejs_template(
                    f.read(),
                    ['website_specs', 'theme_specs', 'items', 'node_specs']
                )
        return get_template_renderer.__templates[template_name]
    get_template_renderer.__templates = {}
    def clean_posix_path(url: str) -> str:
        url = url.replace('/./', '/')
        url = re.sub(r'/[^\/]+/\.\.(?=/)', '/', url)
        url = re.sub('//+', '/', url)
        return url
    def build_contents(node: dict, base_path: str, relative_url: str) -> None:
        relative_url = clean_posix_path(relative_url)
        node_output_path = os.path.join(output_path, relative_url)
        os.makedirs(node_output_path, exist_ok=True)
        def build_root_contents():
            if 'specs' in node:
                if 'template' not in node['specs']:
                    # TODO: Warn the inconsistency
                    return
                if 'markdowns' in node['specs']:
                    md_vars = {}
                    for var_name, file_name in node['specs']['markdowns'].items():
                        contents_markdown = os.path.join(website_path, base_path, file_name)
                        if os.path.isfile(contents_markdown):
                            md_vars[var_name] = render_markdown(contents_markdown)
                        else:
                            # TODO: Warn the inconsistency
                            pass
                    if 'markdown' not in additional_stylesheets:
                        additional_stylesheets['markdown'] = get_markdown_stylesheet()
                html_renderer = get_template_renderer(node['specs']['template'])
                html = html_renderer({
                    'website_specs':website_specs,
                    'theme_specs': theme_specs,
                    'items': items,
                    'node_specs': node['specs']
                })
                html = bs4(html, features="html.parser")
                for s in html.find_all('script'):
                    if not s.get('type') or s.get('type').lower() == 'javascript':
                        s.string = minify_js(s.string)['code']
                html = html.encode(formatter='html5')
                with open(os.path.join(node_output_path, 'index.html'), 'wb') as f:
                    f.write(html)
                if 'resources' in node['specs']:
                    for r in node['specs']['resources']:
                        if os.path.isdir(os.path.join(base_path, r)):
                            shutil.copytree(
                                os.path.join(base_path, r),
                                os.path.join(node_output_path, r),
                                symlinks=True
                            )
                        else:
                            shutil.copy2(
                                os.path.join(base_path, r),
                                os.path.join(node_output_path, r)
                            )
        build_root_contents()
        if not os.path.isfile(os.path.join(node_output_path, 'index.html')):
            if os.path.islink(os.path.join(node_output_path, 'index.html')):
                os.unlink(os.path.join(node_output_path, 'index.html'))
            os.symlink(
                os.path.join(output_path, '404.html'),
                os.path.join(node_output_path, 'index.html'),
                target_is_directory=True
            )
        if 'children' in node:
            for child in node['children']:
                build_contents(
                    node['children'][child],
                    os.path.join(base_path, child),
                    os.path.join(relative_url, child)
                )
    build_contents(items, website_specs['contents'], '')

build("/home/behrooz/Temp/Raw", "/home/behrooz/Temp/Blog", "https://vedadian.com")