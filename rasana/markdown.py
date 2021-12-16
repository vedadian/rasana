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



__all__ = [
    'Parser',
    'HtmlRenderer',
    'stylesheet'
]