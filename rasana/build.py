# =================================================================================
#  Copyright (c) 2021 Behrooz Vedadian
 
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

import jdatetime
import os
import glob
import json

def read_json_file(path: str) -> dict:
    with open(path) as f:
        result = json.dump(f)
    return result

def build_blog(material_path: str, base_uri: str) -> None:
    if not os.path.isfile(f'{material_path}/blog.json'):
        raise Exception(f'Invalid material directory ({material_path}) for blog')
    for post_path in glob.glob(f'{material_path}/posts/**/'):
        post_path = post_path[:-1]
        post_id = os.path.basename(post_path)
        if not os.path.isfile(f'{post_path}/post.json'):
            # TODO: log warning
            continue
        specs = read_json_file(f'{post_path}/post.json')
        specs['id'] = post_id
