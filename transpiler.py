#!/usr/bin/python3
import sys
from lark import Lark, Tree, Token, Transformer, Visitor

def ast(tree):
  if isinstance(tree, list):
    return [x for x in [ast(x) for x in tree] if x]
  elif isinstance(tree, Tree):
    return getattr(tree.meta,'ast', None)

with open("syntax.lark") as f:
  class C_hat:
    parser = Lark(f.read(), start="translation_unit", keep_all_tokens=True)
    def __init__(self, code):
      self.code = code
      self.tree = C_hat.parser.parse(code)
      self.add_back_ignored_tokens()
      self.transpile()
    def transpile(self):
      ShadowAst().visit(self.tree)
      #print(self.tree.pretty())
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

def serialize(x, context={}):
  if isinstance(x, Tree):
    a = ast(x)
    if a:
      return a.serialize(context)
    else:
      result = ''
      for entry in x.children:
        result += serialize(entry, context)
      return result
  elif isinstance(x, Token):
    return x
  raise Exception("Can't handle this type of entry");

class ShadowAstEntry():
  def __init__(self, tree):
    tree.meta.ast = self
    self.tree = tree
  def ast_children(self):
    l = []
    def sub(tree):
      for entry in tree.children:
        if isinstance(entry,Tree):
          a = ast(entry)
          if a:
            l.append(a)
          else:
            sub(entry)
    sub(self.tree)
    return l
  def serialize(self, context={}):
    result = ''
    for entry in self.tree.children:
      result += serialize(entry, context)
    return result

class declarator_mixin:
  def is_pointer(self):
    for a in ast(self.tree.children):
      if isinstance(a, ShadowAst.pointer):
        return True
      elif isinstance(a, ShadowAst.declarator):
        return a.is_pointer()
    return False

class direct_declarator_mixin: pass

class array_declarator_mixin:
  def serialize(self, context={}):
    context={**context}
    if 'array_sub' not in context:
      context['array_sub'] = [False]
    if not context['array_sub'][0]:
      self.serialize_sub(context)
    return self.serialize_sub(context)
  def serialize_sub(self, context={}):
    defined_later = context.get('defined_later',set())
    result = ''
    multi = False
    for entry in self.tree.children:
      a = ast(entry)
      if a:
        if isinstance(a, array_declarator_mixin):
          result += serialize(entry, context)
          multi = True
          continue
        elif isinstance(a, ShadowAst.direct_declarator) and context['array_sub'][0]:
          fb = context.get('function_body', None)
          if context.get("parameter_list_counter",0) == 1:
            result += serialize(entry, {**context,'id_prefix':'_C_HAT_'})
            continue
          if fb:
            x = ''
            if fb == 'def':
              x = serialize(entry, context)
            elif fb == 'cast':
              x = serialize(entry, {**context,'id_prefix':-1})
            if not a.is_pointer():
              if entry.data == 'declarator':
                return '*'+x.strip();
              else:
                return '(*'+x.strip()+')';
            result += x
            continue
        elif isinstance(a, ShadowAst.assignment_expression):
          gri = a.get_referenced_identifiers()
          used_not_yet_defined_identifiers = gri & defined_later
          if used_not_yet_defined_identifiers:
            if multi:
              context['array_sub'][0] = True
              if context.get('function_definition',False) and context.get("parameter_list_counter",0) == 1:
                result += '1';
              else:
                result += '*'
            continue # Remove expression
      result += serialize(entry, context)
    return result

class function_declarator: pass

class expression_component_mixin:
  def get_referenced_identifiers(self):
    result = set()
    for entry in self.ast_children():
      if isinstance(entry, expression_component_mixin):
        result += entry.get_referenced_identifiers()
      elif isinstance(entry, ShadowAst.identifier):
        result.add(entry.value())
    return result

class ShadowAst(Visitor):
  class declaration_specifiers(ShadowAstEntry):
    def __init__(self, tree):
      super().__init__(tree)
    def get_specifiers(self):
      return [str(token) for token in self.tree.children if isinstance(token, Token) and token.type != 'ignored']

  class declarator(declarator_mixin, ShadowAstEntry):
    def get_identifier(self):
      for a in ast(self.tree.children):
        if isinstance(a, ShadowAst.identifier):
          return a.value()
        elif isinstance(a, ShadowAst.declarator):
          return a.get_identifier()
  class abstract_declarator(declarator_mixin, ShadowAstEntry): pass

  class direct_declarator(direct_declarator_mixin, declarator): pass
  class direct_abstract_declarator(direct_declarator_mixin, abstract_declarator): pass

  class direct_array_declarator(array_declarator_mixin, direct_declarator): pass
  class abstract_array_declarator(array_declarator_mixin, direct_abstract_declarator): pass

  class direct_function_declarator(direct_declarator, function_declarator): pass
  class abstract_function_declarator(direct_abstract_declarator, function_declarator): pass

  class identifier(ShadowAstEntry):
    def value(self):
      return next(x for x in self.tree.children if isinstance(x, Token) and x.type == 'IDENTIFIER').value
    def serialize(self, context={}):
      prefix = context.get('id_prefix', None)
      if prefix == -1:
        return ''
      result = ''
      for entry in self.tree.children:
        if isinstance(entry, Token) and entry.type == 'IDENTIFIER' and prefix is not None:
          result += prefix;
        result += serialize(entry, context)
      return result

  class parameter_declaration(declarator): pass

  class parameter_list(ShadowAstEntry):
    def get_parameters(self):
      return [entry for entry in ast(self.tree.children) if isinstance(entry, ShadowAst.parameter_declaration)]
    def get_arguments(self):
      return [p.get_identifier() for p in self.get_parameters()]
    def serialize(self, context={}):
      pl_count = context.get('parameter_list_counter', 0) + 1
      args = self.get_arguments()
      result = ''
      for i, entry in enumerate(self.tree.children):
        c = {**context}
        c['parameter_list_counter'] = pl_count
        c['defined_later'] = {*args[i+1:]} - {None}
        c['array_sub'] = [False]
        a = ast(entry)
        result += serialize(entry, c)
        if pl_count == 1 and c['array_sub'][0] and 'body_insert' in c:
          c['body_insert'].append(
            serialize(entry, {**context,
              'parameter_list_counter': 2,
              'array_sub': [True],
              'function_body': 'def',
            }) + ' = (' + serialize(entry, {**context,
              'parameter_list_counter': 2,
              'array_sub': [True],
              'function_body': 'cast',
            }) +')_C_HAT_'+a.get_identifier()+';'
          );
      return result

  class assignment_expression(expression_component_mixin, ShadowAstEntry): pass
  class pointer(ShadowAstEntry): pass

  class function_definition(ShadowAstEntry):
    def serialize(self, context={}):
      context={**context,
        'function_definition': True,
        'body_insert': [],
      }
      result = ''
      for entry in self.tree.children:
        result += serialize(entry, context)
      return result

  class compound_statement(ShadowAstEntry):
    def serialize(self, context={}):
      compound_count = context.get('compound_count', 0) + 1
      body_insert = context.get('body_insert',[])
      if body_insert: del context['body_insert']
      first = True
      result = ''
      for entry in self.tree.children:
        c = {**context}
        c['compound_count'] = compound_count
        if isinstance(entry, Tree):
          if first and compound_count == 1 and body_insert:
            result += '\n  '+'\n  '.join(body_insert)+'\n  '
          first = False
        result += serialize(entry, c)
      return result

with open(sys.argv[1]) as f:
  print(serialize(C_hat(f.read()).tree))
