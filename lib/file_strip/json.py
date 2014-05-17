"""
Json Comments
Licensed under MIT
Copyright (c) 2011 Isaac Muse <isaacmuse@gmail.com>
https://gist.github.com/facelessuser/5750103

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from __future__ import absolute_import
import re
from .comments import Comments

JSON_PATTERN = re.compile(
    r"""
        (
            (?P<square_comma>
                ,                        # trailing comma
                (?P<square_ws>[\s\r\n]*) # white space
                (?P<square_bracket>\])   # bracket
            )
          | (?P<curly_comma>
                ,                        # trailing comma
                (?P<curly_ws>[\s\r\n]*)  # white space
                (?P<curly_bracket>\})    # bracket
            )
        )
      | (?P<code>
            "(?:\\.|[^"\\])*"            # double quoted string
          | '(?:\\.|[^'\\])*'            # single quoted string
          | .[^,"']*                     # everything else
        )
    """,
    re.MULTILINE | re.DOTALL | re.VERBOSE
)


def strip_dangling_commas(text, preserve_lines=False):
    regex = JSON_PATTERN

    def remove_comma(g, preserve_lines):
        if preserve_lines:
            # ,] -> ] else ,} -> }
            if g["square_comma"] is not None:
                return g["square_ws"] + g["square_bracket"]
            else:
                return g["curly_ws"] + g["curly_bracket"]
        else:
            # ,] -> ] else ,} -> }
            return g["square_bracket"] if g["square_comma"] else g["curly_bracket"]

    def evaluate(m, preserve_lines):
        g = m.groupdict()
        return remove_comma(g, preserve_lines) if g["code"] is None else g["code"]

    return ''.join(map(lambda m: evaluate(m, preserve_lines), regex.finditer(text)))


def strip_comments(text, preserve_lines=False):
    return Comments('json', preserve_lines).strip(text)


def sanitize_json(text, preserve_lines=False):
    return strip_dangling_commas(Comments('json', preserve_lines).strip(text), preserve_lines)
