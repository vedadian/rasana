# =================================================================================
#  Copyright (c) 2023 Behrooz Vedadian
 
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
 
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
 
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
# =================================================================================

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

def compile_ejs_template(template: str) -> Callable:
    def render(context: dict) -> str:
        return render.__context.call('render', context)
    render.__context = MiniRacer()
    def string_literal(text):
        return json.dumps(text)
    compiled_template = ''
    remove_succeeding_ws = False
    remove_succeeding_nl = False
    i = 0
    result = ''
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
    render.__context.eval(
        compile_ejs_template.__compiled_ejs_template.replace(
            '// body_of_rendered_ejs_function',
            compiled_template
        )
    )
    return render
with open(os.path.join(os.path.dirname(__file__), './js/compiled_ejs_template.js')) as f:
    compile_ejs_template.__compiled_ejs_template = f.read()

__all__ = [
    'minify_css',
    'minify_js'
]
