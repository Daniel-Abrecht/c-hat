#!/usr/bin/python3
import sys
from lark import Lark, Tree, Token, Transformer, Visitor

with open("syntax.lark") as f:
  class C_hat:
    parser = Lark(f.read(), start="translation_unit", keep_all_tokens=True)
    def __init__(self, code):
      self.code = code
      self.tree = C_hat.parser.parse(code)
      self.add_back_ignored_tokens()
      self.transpile()
    def transpile(self):
      ParallelAst().visit(self.tree)
      #print(self.tree.pretty())
      self.tree = TransformVariableArrayArguments().transform(self.tree)
      pass
    def add_back_ignored_tokens(self):
      context = type('', (), {})()
      context.pos = 0
      def sub(tree):
        n = 0
        for i, entry in enumerate([*tree.children]):
          if isinstance(entry,Tree):
            entry.parent = tree
            sub(entry)
          elif isinstance(entry, Token):
            if context.pos < entry.start_pos:
              spaces = self.code[context.pos:entry.start_pos]
              tree.children.insert(i+n, Token('ignored', spaces))
              n += 1
            context.pos = entry.end_pos
          else:
            raise Exception("Can't handle this type of entry");
      sub(self.tree)
      spaces = self.code[context.pos]
      if spaces[-1] != '\n':
        spaces += '\n'
      self.tree.children.append(Token('ignored', spaces))

def serialize(tree):
  result = ''
  for entry in tree.children:
    if isinstance(entry,Tree):
      if hasattr(entry.meta, 'ast'):
        result += entry.meta.ast.serialize()
      else:
        result += serialize(entry)
    elif isinstance(entry, Token):
      result += entry
    else:
      raise Exception("Can't handle this type of entry");
  return result

class ParallelAstEntry():
  def __init__(self, tree):
    tree.meta.ast = self
    self.tree = tree
  def serialize(self):
    return serialize(self.tree)

class ParallelAst(Visitor):
  class declaration_specifiers(ParallelAstEntry):
    def __init__(self, tree):
      super().__init__(tree)
    def get_specifiers(self):
      return [str(token) for token in self.tree if isinstance(token, Token) and token.type != 'ignored']
  class direct_array_declarator(ParallelAstEntry):
    def __init__(self, tree):
      super().__init__(tree)

class TransformVariableArrayArguments(Transformer):
  def parameter_list(self, args):
    for entry in args:
      if isinstance(entry, Tree):
        if entry.data == 'parameter_declaration':
          #print(entry.pretty())
          #print(entry.data)
          pass
    return Tree('parameter_list', args)

with open(sys.argv[1]) as f:
  print(serialize(C_hat(f.read()).tree))
