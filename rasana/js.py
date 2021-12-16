import os
import json
import re
from typing import Any, Callable
from py_mini_racer import MiniRacer

def minify_css(*a: list, **b: dict) -> Any:
    return minify_css.__context.call("csso.minify", *a, **b)

def minify_js(*a: list, **b: dict) -> Any:
    o = {
        "mangle": True,
        "compress": {
            "sequences": True,
            "dead_code": True,
            "conditionals": True,
            "booleans": True,
            "unused": True,
            "if_return": True,
            "join_vars": True,
            "drop_console": True
        }
    }
    o.update(b)
    return minify_js.__context.call("minify", *a, o)

minify_css.__context = MiniRacer()
with open(os.path.join(os.path.dirname(__file__), './js/csso.min.js')) as f:
    minify_css.__context.eval(f.read())
minify_js.__context = MiniRacer()
with open(os.path.join(os.path.dirname(__file__), './js/uglifyjs3.min.js')) as f:
    minify_js.__context.eval(f.read())

def compile_ejs_template(template: str, parameters: list) -> Callable:
    def render(context: dict) -> str:
        return render.__context.call('render', context)
    render.__context = MiniRacer()
    def string_literal(text):
        return json.dumps(text)
    escape_html_function = ''
    compiled_template = 'function render({' + ','.join(parameters) + '}) {let result="";'
    remove_succeeding_ws = False
    remove_succeeding_nl = False
    i = 0
    for m in re.finditer('<%[^%].*?%>', template):
        code = m.group()
        operation = 0 # Add code to execution pipeline
        remove_preceding_ws = False
        escape_code_output = False
        left_offset = 3
        right_offset = -3
        text = template[i:m.start()]
        if remove_succeeding_nl:
            text = text.lstrip('\n')
        elif remove_succeeding_ws:
            text = text.lstrip()
        remove_succeeding_ws = False
        remove_succeeding_nl = False
        if code[2] == '=':
            operation = 1
        elif code[2] == '-':
            operation = 1
            escape_code_output = True
            if not escape_html_function:
                escape_html_function = 'const HTML_SAFE_ALTERNATIVES = {'\
                                           '"&":"&amp;","\\"":"&quot;","\'":"&apos;","<":"&lt;",">":"&gt;"'\
                                        '};'\
                                        'const escapeForHtml = '\
                                            's => s.replace(/[&"\'<>]/g, c => HTML_SAFE_ALTERNATIVES[c]);'
        elif code[3] == '#':
            operation = 2 # No operation
        elif code[3] == '_':
            remove_preceding_ws = True
        else:
            left_offset = 2
        if code[-3] == '-':
            remove_succeeding_nl = True
        elif code[-3] == '_':
            remove_succeeding_ws = True
        else:
            right_offset = -2
        if remove_preceding_ws:
            text = text.rstrip()
        compiled_template += f'result+={string_literal(text)};'
        if operation == 1:
            if escape_code_output:
                compiled_template += f'result+=escapeForHtml({code[left_offset:right_offset]});'
            else:
                compiled_template += f'result+={code[left_offset:right_offset]};'
        elif operation == 2:
            pass
        else:
            compiled_template += f'{code[left_offset:right_offset]};'
        i = m.end()
    if i < len(template):
        compiled_template += f'result+={string_literal(template[i:])};'
    compiled_template += 'return result;}'
    compiled_template = escape_html_function + compiled_template
    render.__context.eval(compiled_template)
    return render


__all__ = [
    'minify_css',
    'minify_js'
]
