# coding=utf-8
"""Generate code from an annotated syntax tree."""
# Copyright 2017 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections

from pasta.base import annotate
from pasta.base import ast_utils

# TODO: Handle indentation correctly on inserted nodes


class PrintError(Exception):
  """An exception for when we failed to print the tree."""


class Printer(annotate.BaseVisitor):
  """Traverses an AST and generates formatted python source code.
  
  This uses the same base visitor as annotating the AST, but instead of eating a
  token it spits one out. For special formatting information which was stored on
  the node, this is output exactly as it was read in unless one or more of the
  dependency attributes used to generate it has changed, in which case its
  default formatting is used.
  """

  def __init__(self):
    super(Printer, self).__init__()
    self.code = ''

  def visit(self, node):
    node._printer_info = collections.defaultdict(lambda: False)
    try:
      super(Printer, self).visit(node)
    except (TypeError, ValueError, IndexError, KeyError) as e:
      raise PrintError(e)
    del node._printer_info

  def visit_Num(self, node):
    self.prefix(node)
    content = ast_utils.prop(node, 'content')
    self.code += content if content is not None else repr(node.n)
    self.suffix(node)

  def visit_Str(self, node):
    self.prefix(node)
    content = ast_utils.prop(node, 'content')
    self.code += content if content is not None else repr(node.s)
    self.suffix(node)

  def token(self, value):
    self.code += value

  def optional_token(self, node, attr_name, token_val):
    del token_val
    if not hasattr(node, ast_utils.PASTA_DICT):
      return
    self.code += ast_utils.prop(node, attr_name)

  def attr(self, node, attr_name, attr_vals, deps=None, default=None):
    """Add the formatted data stored for a given attribute on this node.

    If any of the dependent attributes of the node have changed since it was
    annotated, then the stored formatted data for this attr_name is no longer
    valid, and we must use the default instead.
    
    Arguments:
      node: (ast.AST) An AST node to retrieve formatting information from.
      attr_name: (string) Name to load the formatting information from.
      attr_vals: (list of functions/strings) Unused here.
      deps: (optional, set of strings) Attributes of the node which the stored
        formatting data depends on.
      default: (string) Default formatted data for this attribute.
    """
    del attr_vals
    if not hasattr(node, '_printer_info') or node._printer_info[attr_name]:
      return
    node._printer_info[attr_name] = True
    if (deps and
        any(getattr(node, dep, None) != ast_utils.prop(node, dep + '__src')
            for dep in deps)):
      self.code += default or ''
    else:
      val = ast_utils.prop(node, attr_name)
      self.code += val if val is not None else (default or '')

  def check_is_elif(self, node):
    try:
      return ast_utils.prop(node, 'is_elif')
    except AttributeError:
      return False

  def check_is_continued_try(self, node):
    # TODO: Don't set extra attributes on nodes
    return getattr(node, 'is_continued', False)

  def check_is_continued_with(self, node):
    # TODO: Don't set extra attributes on nodes
    return getattr(node, 'is_continued', False)


def to_str(tree):
  """Convenient function to get the python source for an AST."""
  p = Printer()
  p.visit(tree)
  return p.code
