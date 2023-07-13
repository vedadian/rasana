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

import re
from typing import Any
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from commonmark import inlines
from commonmark.node import Node
from commonmark.inlines import InlineParser as OldInlineParser, text
from commonmark import Parser as OldParser, HtmlRenderer as OldHtmlRenderer

reTexCode = re.compile(r'(\$\$?)(?:[^$]|\\\$)*\1')
class InlineParser(OldInlineParser):
    def parseInline(self, block):
        c = self.peek()
        if c == '$':
            tex_code = self.match(reTexCode)
            if tex_code is not None:
                block.append_child(text(tex_code))
                return True
        return super().parseInline(block)

class Parser(OldParser):
    def __init__(self, options={}) -> None:
        super().__init__(options=options)
        self.inline_parser = InlineParser(options=options)

class HtmlRenderer(OldHtmlRenderer):
    def code_block(self, node, entering):
        self.cr()
        self.lit(
            highlight(
                node.literal,
                get_lexer_by_name(node.info),
                HtmlFormatter()
            )
        )
        self.cr()

def render(markdown_file_path: str) -> str:
    ast = None
    with open(markdown_file_path) as f:
        ast = render.__parser.parse(f.read())
    return render.__html.render(ast)
render.__parser = Parser({})
render.__html = HtmlRenderer({})

def get_stylesheet() -> str:
    return HtmlFormatter().get_style_defs()
