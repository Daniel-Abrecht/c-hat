#!/usr/bin/python3
import sys
from lark import Lark, Visitor, Tree, Token

with open("syntax.lark") as f:
  class C_hat:
    parser = Lark(f.read(), start="translation_unit", keep_all_tokens=True)
    def __init__(self, code):
      self.code = code
      self.tree = C_hat.parser.parse(code)
      self.transpile()
    def transpile(self):
      # TODO
      pass
    def dump_code(self):
      context = type('', (), {})()
      context.pos = 0
      def sub(tree):
        #print(tree.data);
        for entry in tree.children:
          if isinstance(entry,Tree):
            sub(entry)
          elif isinstance(entry, Token):
            spaces = self.code[context.pos:entry.start_pos]
            print(f"{spaces}{entry}", end='')
            context.pos = entry.end_pos
          else:
            raise Exception("Can't handle this type of entry");
      sub(self.tree)
      spaces = self.code[context.pos]
      if spaces[-1] != '\n':
        spaces += '\n'
      print(spaces, end='')

with open(sys.argv[1]) as f:
  C_hat(f.read()).dump_code()

# TODO: make changes here
