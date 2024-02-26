#!/usr/bin/python3
import sys
from lark import Lark, Tree, Token, Transformer

with open("syntax.lark") as f:
  class C_hat:
    parser = Lark(f.read(), start="translation_unit", keep_all_tokens=True)
    def __init__(self, code):
      self.code = code
      self.tree = C_hat.parser.parse(code)
      self.add_back_ignored_tokens()
      self.transpile()
    def transpile(self):
      #print(self.tree.pretty())
      pass
    def add_back_ignored_tokens(self):
      context = type('', (), {})()
      context.pos = 0
      def sub(tree):
        n = 0
        for i, entry in enumerate(tree.children):
          if isinstance(entry,Tree):
            sub(entry)
          elif isinstance(entry, Token):
            if context.pos < entry.start_pos:
              spaces = self.code[context.pos:entry.start_pos]
              tree.children.insert(i+n,Token('ignored', spaces))
              n += 1
            context.pos = entry.end_pos
          else:
            raise Exception("Can't handle this type of entry");
      sub(self.tree)
      spaces = self.code[context.pos]
      if spaces[-1] != '\n':
        spaces += '\n'
      self.tree.children.append(Token('ignored', spaces))
    def dump_code(self):
      def sub(tree):
        for entry in tree.children:
          if isinstance(entry,Tree):
            sub(entry)
          elif isinstance(entry, Token):
            print(entry, end='')
          else:
            raise Exception("Can't handle this type of entry");
      sub(self.tree)


with open(sys.argv[1]) as f:
  C_hat(f.read()).dump_code()
