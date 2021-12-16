from genericpath import isfile
import os
import re
import json
import shutil
import urllib
from glob import glob
from typing import Callable, Optional
from bs4 import BeautifulSoup as bs4
from .markdown import render as render_markdown, get_stylesheet as get_markdown_stylesheet
from .js import minify_css, minify_js, compile_ejs_template

HOME_DIRECTORY = os.path.expanduser("~")

def get_file_contents(file_path: str) -> str:
    with open(file_path) as f:
        return f.read()

def build(website_path: str, output_path: str, base_url: str) -> None:
    if base_url[-1] == '/':
        base_url = base_url[:-1]
    website_specs_json = os.path.join(website_path, 'website.json')
    if not os.path.isfile(website_specs_json):
        raise Exception(f'No `blog.json` file found in `{website_path}`')
    with open(website_specs_json) as f:
        website_specs = json.load(f)
    if 'theme' not in website_specs:
        raise Exception(f'No theme specified in `{website_specs_json}`')
    if 'mainPage' not in website_specs:
        raise Exception(f'No `mainPage` section in `{website_specs_json}`')
    if '404' not in website_specs:
        raise Exception(f'No `404` section in `{website_specs_json}`')
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
    if ('templates' not in theme_specs) or ('404' not in theme_specs['templates']):
        raise Exception(f'Every theme must contain a 404 template')
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
                get_template_renderer.__templates[template_name] = compile_ejs_template(f.read())
        return get_template_renderer.__templates[template_name]
    get_template_renderer.__templates = {}
    def clean_posix_path(url: str) -> str:
        url = url.replace('/./', '/')
        url = re.sub(r'/[^\/]+/\.\.(?=/)', '/', url)
        url = re.sub('//+', '/', url)
        return url
    def copy_resources(node: dict, base_path: str, node_output_path: str) -> None:
        if 'resources' in node:
            for r, rtype in node['resources'].items():
                if os.path.isdir(os.path.join(base_path, r)):
                    shutil.copytree(
                        os.path.join(base_path, r),
                        os.path.join(node_output_path, (rtype or r)),
                        symlinks=True,
                        dirs_exist_ok=True
                    )
                elif os.path.isfile(os.path.join(base_path, r)):
                    if rtype not in ['css', 'font', 'img', 'js']:
                        # TODO: Warn the inconsistency
                        pass
                    else:
                        shutil.copy2(
                            os.path.join(base_path, r),
                            os.path.join(node_output_path, rtype, r)
                        )
    def build_root_contents(node: dict, base_path: str, node_output_path: str, relative_url: str, html_file_name: Optional[str] = 'index'):
        if 'template' not in node:
            # TODO: Warn the inconsistency if `relative_url` is not empty
            node['template'] = 'default' if html_file_name == 'index' else html_file_name
        extra_stylesheets = []
        if 'extraStylesheets' in node:
            extra_stylesheets = node['extraStylesheets']
        if 'markdowns' in node:
            md_vars = {}
            for var_name, file_name in node['markdowns'].items():
                contents_markdown = os.path.join(website_path, base_path, file_name)
                if os.path.isfile(contents_markdown):
                    md_vars[var_name] = render_markdown(contents_markdown)
                else:
                    # TODO: Warn the inconsistency
                    pass
            if 'markdown' not in additional_stylesheets:
                additional_stylesheets['markdown'] = get_markdown_stylesheet()
            if 'variables' not in node:
                node['variables'] = {}
            node['variables'].update(md_vars)
            extra_stylesheets.append('markdown')
        html_renderer = get_template_renderer(node['template'])
        html = html_renderer({
            'websiteSpecs':website_specs,
            'themeSpecs': theme_specs,
            'items': items,
            'nodeSpecs': node,
            'breadCrumb': [e for e in relative_url.split('/') if e]
        })
        html = bs4(html, features="html.parser")
        for s in html.find_all('script'):
            if not s.get('type') or s.get('type').lower() == 'javascript':
                s.string = minify_js(s.string)['code']
        for s in html.find_all('style'):
            if not s.get('type') or s.get('type').lower() == 'javascript':
                s.string = minify_css(s.string)['css']
        for s in extra_stylesheets:
            new_stylesheet_node = html.new_tag('link')
            new_stylesheet_node['rel'] = 'stylesheet'
            new_stylesheet_node['href'] = f'./css/{s[2:]}.css' if s.startswith('./') else f'/css/{s}.css'
            html.find('head').append(new_stylesheet_node)
        if 'inlineStyles' in node:
            new_stylesheet_node = html.new_tag('style')
            new_stylesheet_node.string = get_file_contents(
                os.path.join(
                    website_path, base_path,
                    node['inlineStyles']
                )
            )
            html.find('head').append(new_stylesheet_node)
        html = html.encode(encoding='utf8', formatter='html5')
        with open(os.path.join(node_output_path, f'{html_file_name}.html'), 'wb') as f:
            f.write(html)
        copy_resources(node, base_path, node_output_path)
        return f'{base_url}/{relative_url}'

    def build_contents(node: dict, base_path: str, relative_url: str) -> None:
        built_urls = []
        relative_url = clean_posix_path(relative_url)
        node_output_path = os.path.join(output_path, relative_url)
        os.makedirs(node_output_path, exist_ok=True)
        if 'specs' in node:
            built_urls.append(
                build_root_contents(
                    node['specs'],
                    base_path,
                    node_output_path,
                    relative_url
                )
            )
        if 'children' in node:
            for child in node['children']:
                child_built_urls = build_contents(
                    node['children'][child],
                    os.path.join(base_path, child),
                    os.path.join(relative_url, child)
                )
                built_urls.extend(child_built_urls)
        return built_urls
    built_urls = build_contents(items, website_specs['contents'], '')
    copy_resources(theme_specs, website_path, output_path)
    copy_resources(website_specs, website_path, output_path)
    if additional_stylesheets:
        os.makedirs(os.path.join(output_path, 'css'), exist_ok=True)
        for name, value in additional_stylesheets.items():
            with open(os.path.join(output_path, 'css', f'{name}.css'), 'w') as f:
                f.write(minify_css(value)['css'])
    with open(os.path.join(output_path, 'sitemap.txt'), 'w') as f:
        f.writelines(e + '\n' for e in built_urls)
    if 'googleVerification' in website_specs:
        with open(os.path.join(output_path, f'google{website_specs["googleVerification"]}.html'), 'w') as f:
            f.write(f'google-site-verification: google{website_specs["googleVerification"]}.html')
    if 'aliases' in website_specs:
        for a, target_url in website_specs['aliases'].items():
            if target_url not in built_urls:
                # TODO: Warn the inconsistency
                continue
            os.makedirs(os.path.join(output_path, a))
            with open(os.path.join(output_path, a, 'index.html'), 'w') as f:
                f.write(
                    f'<html><head>' +
                    '<meta http-equiv="refresh" content="0; url={target_url}" />' +
                    '</head><body><p>' + 
                    f'This page has been moved to <a href="{target_url}">here</a>.' +
                    '</p></html>'
                )
        build_root_contents(website_specs['mainPage'], website_specs['mainPage']['basePath'], output_path, '')
        build_root_contents(website_specs['404'], website_specs['404']['basePath'], output_path, '', '404')
        if 'robots' in website_specs:
            with open(os.path.join(output_path, 'robots.txt'), 'w') as f:
                for user_agent, rules in website_specs['robots'].items():
                    f.write(f'User-agent: {user_agent}\n')
                    for name, value in rules:
                        f.write(f'{name}: {value}\n')
                    f.write('\n')
                f.write(f'Sitemap: {base_url}/sitemap.txt')

build("/home/behrooz/Temp/Raw", "/home/behrooz/Temp/Blog", "https://vedadian.com")