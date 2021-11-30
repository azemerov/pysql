from pysql_lark import *
import re

curls = re.compile('\{.+?\}')

def iterate(tree, call_back, depth=0):
    if isinstance(tree, Tree):
        call_back(tree, depth)
        for child in tree.children:
            iterate(child, call_back, depth + 1)
    else:
        call_back(tree, depth)
    return

    if isinstance(tree, Tree):
        if len(tree.children) == 1 and not isinstance(tree.children[0], Tree):
            print(' '*depth, tree.data, tree.children[0])
        else:
            print(' '*offsedepth, tree.data)
            for child in tree.children:
                iterate(child, depth + 1)
    else:
        print(' '*depth, tree)
        
def _do_print(node, depth):
    if isinstance(node, Tree):
        print(' '*depth, node.data)
    else:
        print(' '*depth, node)

def unquote(value):
    if not value:
        return "NULL"
    elif value[0] == '"':
        return value.strip('"')
    elif value[0] == "'":
        return value.strip("'")
    else:
        return value

def requote(value):
    if not value:
        return "NULL"
    elif value[0] == '"':
        return "'" + value.strip('"') + "'"
    elif value[0:3] == "'''":
        return "'" + value.strip("'") + "'"
    else:
        return value

def strip_type(name):
    """
    remove size constraint from the type name
    """
    if '(' in name:
        return name.split('(',1)[0]
    return name

def loc_tag(node):
    if isinstance(node, Token):
        return '/*%s, line:%s*/' % (node.type, node.line)
    elif isinstance(node, Tree):
        return '/*%s line:%s*/' % (node.data, node._meta.line)
    else:
        breakpoint()

verbose = False
def trace(*text):
    if verbose:
        print(*text)

SP = '  '

class ListX(object):
    def __init__(self):
        self.declarations = []
        self.body = []
        self.local_vars = {}
    
    def append_decl(self, value):
        self.declarations.append(value)

    def extend_decl(self, value):
        self.declarations.extend(value)

    def append(self, value):
        self.body.append(value)

    def extend(self, value):
        self.body.extend(value)
        
    def __getitem__(self, key):
        return self.body[key]

    def __setitem__(self, key, value):
        self.body[key] = value

    def __str__(self):
        return "%s\n%s" % (self.declarations.__str__(), self.body.__str__())

    def __repr__(self):
        return "%s\n%s" % (self.declarations.__repr__(), self.body.__repr__())

class NodeVisitor(object):
    """
    A node visitor base class that walks the abstract syntax tree and calls a
    visitor function for every node found.  This function may return a value
    which is forwarded by the `visit` method.

    This class is meant to be subclassed, with the subclass adding visitor
    methods.

    Per default the visitor functions for the nodes are ``'visit_'`` +
    class name of the node.  So a `TryFinally` node visit function would
    be `visit_TryFinally`.  This behavior can be changed by overriding
    the `visit` method.  If no visitor function exists for a node
    (return value `None`) the `generic_visit` visitor is used instead.

    Don't use the `NodeVisitor` if you want to apply changes to nodes during
    traversing.  For this a special visitor exists (`NodeTransformer`) that
    allows modifications.
    """

    def __init__(self):
        self.offset = 0             # defines the indentation level
        self.autofunc = 1

    def indent(self, adjust=0):
        return SP*(self.offset+adjust)

    def visit(self, node, result):
        """Visit a node."""
        if isinstance(node, Tree):
            method = 'visit_' + node.data
        elif isinstance(node, Token):
            method = 'visit_' + node.type
        else:
            method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, None) #self.generic_visit)
        if visitor:
            visitor(node, result)
        else:
            print('?def %s(self, node, result): breakpoint()' % method)
            self.generic_visit(node, result)

    def generic_visit(self, node, result):
        """Called if no explicit visitor function exists for a node."""
        if isinstance(node, Tree):
            i = 0
            for child in node.children:
                i += 1
                self.visit(child, result)

    def visit_file_input(self, node, result):
        #trace('file_input')
        self.generic_visit(node, result)

    def visit_import_stmt(self, node, result):
        trace('import')
        result.append('-- import ')
        self.generic_visit(node, result)
        result.append(';%s\n' % loc_tag(node))

    def visit_import_name(self, node, result):
        #trace('import_name')
        self.generic_visit(node, result)

    def visit_dotted_as_names(self, node, result):
        #trace('dotted_as_names')
        for i, child in enumerate(node.children):
            if i > 0:
                trace(',')
                result.append(', ')
            self.visit(child, result)

    def visit_dotted_as_name(self, node, result):
        #trace('dotted_as_name')
        self.generic_visit(node, result)

    def visit_dotted_name(self, node, result):
        #trace('dotted_name')
        self.generic_visit(node, result)

    def visit_suite(self, node, result):
        trace(':')
        #result.append('\n')
        self.offset += 1
        self.generic_visit(node, result)
        self.offset -= 1

    def visit_assign_stmt(self, node, result):
        #trace('assign_stmt')
        result.append(self.indent())
        self.generic_visit(node, result)
        result.append(';%s\n' % loc_tag(node))

    def visit_assign(self, node, result):
        #trace('assign')
        #self.generic_visit(node)
        self.visit(node.children[0], result)
        trace('=')
        result.append(' := ')
        self.visit(node.children[1], result)

    def visit_var(self, node, result):
        trace('var:', node.children[0])
        self.visit(node.children[0], result) #result.append(node.children[0])
        
    def visit_const_none(self, node, result):
        trace('None')
        result.append('NULL')

    def visit_if_stmt(self, node, result):
        trace('if, len() = ', len(node.children))
        result.append('\n%sif ' % self.indent())
        # if [ comparison, suite, elifs [ comparison, suite ], suite ]
        self.visit(node.children[0], result) # comparison
        trace('then')
        result.append(' then\n')
        self.offset += 1
        self.visit(node.children[1], result) # suite
        self.offset -= 1
        self.visit(node.children[2], result) # elifs
        if len(node.children)>3:
            trace('else')
            result.append('%selse\n' % self.indent())
            self.offset += 1
            self.visit(node.children[3], result) # else
            self.offset -= 1
        trace('endif')
        result.append('%send if;%s\n' % (self.indent(), loc_tag(node)))

    def visit_expr_stmt(self, node, result):
        trace('expr_stmt')
        result.append(self.indent())
        self.generic_visit(node, result)
        result.append(';%s\n' % loc_tag(node))

    def visit_elifs(self, node, result):
        #trace('elifs')
        #self.generic_visit(node)
        for child in node.children:
            self.visit(child, result)
        #trace('endelifs')

    def visit_elif_(self, node, result):
        trace('elif')
        result.append('%selsif ' % self.indent())
        self.visit(node.children[0], result)
        result.append(' then\n')
        self.offset += 1
        self.visit(node.children[1], result)
        self.offset -= 1
        #trace('endelif_')

    def visit_comparison(self, node, result):
        trace('comparison')
        self.visit(node.children[0], result)
        self.visit(node.children[1], result)
        self.visit(node.children[2], result)
        #trace('endcomparison')

    def visit_comp_op(self, node, result):
        trace('comp_op')
        for child in node.children:
            self.visit(child, result)

    def visit_for_stmt(self, node, result):
        result.append('\n%sfor ' % self.indent())
        self.visit(node.children[0], result) # for_var
        if isinstance(node.children[1], Tree) and node.children[1].data == 'funccall':
            result.append(' in ')
        else:
            result.append(' in (')
        self.visit(node.children[1], result) # iterator
        if isinstance(node.children[1], Tree) and node.children[1].data == 'funccall':
            result.append(' loop%s\n' % loc_tag(node))
        else:
            result.append(')\n%sloop%s\n' % (self.indent(), loc_tag(node)))
        self.offset += 1
        self.visit(node.children[2], result) # suite
        self.offset -= 1
        result.append('%send loop;\n' % self.indent())

    def visit_forall_stmt(self, node, result):
        result.append('\n%sforall ' % self.indent())
        self.visit(node.children[0], result) # for_var
        result.append(' in ')
        self.visit(node.children[1], result) # iterator
        result.append(' --save exception %s\n' % loc_tag(node))
        self.offset += 1
        self.visit(node.children[2], result) # suite
        self.offset -= 1

    def visit_while_stmt(self, node, result):
        result.append('%swhile ' % self.indent())
        self.visit(node.children[0], result) # condition
        result.append('\n%sloop %s\n' % (self.indent(), loc_tag(node)))
        self.offset += 1
        self.visit(node.children[1], result) # suite
        self.offset -= 1
        result.append('%send loop;\n' % self.indent())

    def visit_fetchinto_stmt(self, node, result):
        result.append(self.indent())
        tmp = ListX()
        self.visit(node.children[0], tmp)
        tmp = tmp[0]
        tmp = tmp.split('from', 1)
        result.append(tmp[0])
        result.append('\n%sinto ' % self.indent(1))
        self.visit(node.children[1], result)
        result.append(' from')
        result.append(tmp[1])
        result.append(';%s\n' % loc_tag(node))

    def visit_names(self, node, result):
        for i, child in enumerate(node.children):
            if i:
                result.append(', ')
            self.visit(child, result)

    def visit_exprlist(self, node, result):
        for i, child in enumerate(node.children):
            if i:
                result.append(', ')
            self.visit(child, result)

    def visit_query(self, node, result):
        self.visit(node.children[0], result) 

    def visit_QSTRING(self, node, result):
        result.append(node.value[1:].strip("'\""))

    def visit_QLONG_STRING(self, node, result):
        result.append(node.value[1:].strip("'\""))

    def visit_augassign(self, node, result):
        self.visit(node.children[0], result) # var
        result.append(' := ')
        self.visit(node.children[0], result) # var
        self.visit(node.children[1], result) # oper
        self.visit(node.children[2], result) # for_var

    def visit_augassign_op(self, node, result):
        self.visit(node.children[0], result)

    def visit___ANON_2(self, node, result):
        if node.value in ('+=', '-=', '*=', '/=', '%='):
            result.append(' %s ' % node.value[0])
        else:
            result.append(' %s ' % node.value)

    def visit_decorated(self, node, result):
        self.generic_visit(node, result)

    def visit_decorators(self, node, result):
        self.generic_visit(node, result)

    _decorator = ""
    def visit_decorator(self, node, result):
        tmp = ListX()
        self.visit(node.children[0], tmp)
        self._decorator = tmp[0]
        del tmp

    def visit_classdef(self, node, result):
        trace(node.children[0].value) # package name
        result.append('%screate or replace package body %s as\n' % (self.indent(), node.children[0].value))
        if len(node.children) < 2:
            breakpoint()
        tmp = ListX()
        self.visit(node.children[1], tmp) # suite
        result.extend(tmp.declarations)
        if tmp.body:
            result.append('%sbegin\n' % self.indent())
            result.extend(tmp.body)
        del tmp
        result.append('%send; --PACKAGE\n/\n' % self.indent())

    def visit_funcdef(self, node, result):
        i = 0
        trace(node.children[i]) # function name
        if self._decorator:
            result.append_decl('\n%sfunction ' % self.indent())
        else:
            result.append_decl('\n%sprocedure ' % self.indent())
        self.visit(node.children[i], result.declarations) # function name
        i += 1
        if node.children[i].data.value == 'parameters':
            self.visit(node.children[1], result.declarations) # parameters
            i += 1
        if self._decorator:
            result.append_decl(' return %s as\n' % self._decorator)
        else:
            result.append_decl(' as\n')
        tmp = ListX()
        self.offset += 1
        self.visit(node.children[i], tmp) # suite
        self.offset -= 1

        result.extend_decl(tmp.declarations)
        if self._decorator:
            result.append_decl('%sbegin --FUNC\n' % self.indent())
        else:
            result.append_decl('%sbegin --FUNC\n' % self.indent())
        result.extend_decl(tmp.body)
        del tmp

        if self._decorator:
            result.append_decl('%send; --FUNC\n' % self.indent())
            self._decorator = ""
        else:
            result.append_decl('%send; --PROC\n' % self.indent())

    def visit_parameters(self, node, result):
        trace('(')
        result.append('(')
        for i, child in enumerate(node.children):
            if i > 0:
                trace(', ')
                result.append(', ')
            self.visit(child, result)
        trace(')')
        result.append(')')
        
    def visit_typedparam(self, node, result):
        self.visit(node.children[0], result)
        if len(node.children) > 1:
            result.append(' ')
            self.visit(node.children[1], result)

    def visit_return_stmt(self, node, result):
        trace('return')
        result.append('%sreturn ' % self.indent());
        self.visit(node.children[0], result)
        result.append(';%s\n' % loc_tag(node))

    def visit_funccall(self, node, result):
        tmp = ListX()
        self.visit(node.children[0], tmp) # function name
        if tmp[0] == 'print':
            tmp[0] = 'dbms_output.put_line'

        if len(node.children) > 1:
            self.visit(node.children[1], tmp) # arguments
        if tmp[0] == 'range':
            #result.append('%s .. %s' % (tmp[2], tmp[-2]))
            for x in tmp[2:-1]:
                if x == ', ':
                    result.append(' .. ')
                else:
                    result.append(x)
        elif tmp[0] == 'type':
            result.append('%s%%type' % tmp[2])
        elif tmp[0] == 'rowtype':
            result.append('%s%%rowtype' % tmp[2])
        elif tmp[0] == 'open':
            result.append('open %s' % tmp[2])
        elif tmp[0] == 'close':
            result.append('close %s' % tmp[2])
        elif tmp[0] == 'exec':
            result.append('exec ')
            result.extend(tmp[2:-1]) # remove outer parenthesis
        elif tmp[0] == 'cfetch':
            result.append('fetch %s into %s' % (tmp[2], tmp[4]))
        elif tmp[0] == 'cfetch_break':
            result.append('fetch %s into %s; exit when %s%%notfound' % (tmp[2], tmp[4], tmp[2]))
        elif tmp[0] == 'notfound':
            result.append('%s%%notfound' % tmp[2])
        elif tmp[0] == 'fetch': #selectinto
            tmp = [x for x in tmp if x.strip() not in ('(', ',', ')')]
            select = unquote(tmp[1])
            params = tmp[2:]
            result.append_decl('\n%sfunction select_into_%s(%s) return boolean as' % (
                self.indent(),
                self.autofunc,
                ', '.join(['%s out %s' % (x, strip_type(result.local_vars.get(x,'varchar2'))) for x in params]))
                )
            result.append_decl(loc_tag(node))
            result.append_decl('\n')
            result.append_decl('%sbegin\n' % self.indent())
            i = select.find('from')
            select = select[:i] + ' into %s' % ', '.join(params) +' '+select[i:]
            result.append_decl('%s  %s;\n' % (self.indent(), select))
            result.append_decl('%s  return True;\n' % self.indent())
            result.append_decl('%sexception when no_data_found then\n' % self.indent())
            result.append_decl('%s  return False;\n' % self.indent())
            result.append_decl('%send;\n' % self.indent())

            result.append('select_into_%d(%s)' % (self.autofunc, ', '.join(params)))
            self.autofunc += 1
            # also see visit_Expr() which has explicitly removre ';' after  pseudo function calls
        else:
            result.append(''.join(tmp)) # .extend(tmp)

        del tmp
        #result.append(';\n')

    def visit_arguments(self, node, result):
        trace('(')
        result.append('(')
        for i, child in enumerate(node.children):
            if i > 0:
                trace(', ')
                result.append(', ')
            self.visit(child, result)
        trace(')')
        result.append(')')

    def visit_getitem(self, node, result):
        self.visit(node.children[0], result)
        result.append('(')
        self.visit(node.children[1], result)
        result.append(')')

    def visit_getattr(self, node, result):
        tmp = ListX()
        self.generic_visit(node, tmp)
        result.append('.'.join(tmp))
        del tmp

    def visit_arith_expr(self, node, result):
        self.visit(node.children[0], result) # 1st argument
        self.visit(node.children[1], result) # operator
        self.visit(node.children[2], result) # 2nd argument

    def visit_break_stmt(self, node, result):
        result.append('%sbreak;\n' % self.indent())

    def visit___ANON_18(self, node, result):
        trace('==')
        result.append(' = ')

    def visit_PLUS(self, node, result):
        trace('+')
        result.append(' + ')

    def visit_term(self, node, result):
        self.generic_visit(node, result)

    def visit_STAR(self, node, result):
        trace('*')
        result.append(' * ')

    def visit_try_stmt(self, node, result):
        trace('try')
        result.append('\n%sbegin --TRY %s\n' % (self.indent(), loc_tag(node)))
        self.visit(node.children[0], result) # suite
        for child in node.children[1].children: # list of excepts
            self.visit(child, result) 
        result.append('%send; --TRY\n' % self.indent())
        
    def visit_except_clauses(self, node, result):
        for child in node.children:
            self.visit(child, result) # can have multiple excpetion handlers

    def visit_except_clause(self, node, result):
        _type = ''
        _var = ''
        for child in node.children:
            if isinstance(child, Tree) and child.data == 'var' and isinstance(child.children[0], Token):
                _type = child.children[0].value
            elif isinstance(child, Token) and child.type == 'NAME':
                _var = child.value
                # next Tokens are ignored
            elif isinstance(child, Tree): # suite
                trace('exception %s as %s' % (_type, _var))
                result.append('%sexception when %s then\n' % (self.indent(), _type))
                self.visit(child, result) 

    def visit_raise_stmt(self, node, result):
        if node.children[0].data == 'tuple':
            result.append('%sraise_application_error' % self.indent())
            self.visit(node.children[0], result)
        elif isinstance(node.children[0], Tree) and node.children[0].children[0].type=='STRING':
            result.append('%sraise_application_error(-20000, %s)' % (self.indent(), requote(node.children[0].children[0].value)))
        else:
            result.append('%sraise ' % self.indent())
            self.generic_visit(node, result)
        result.append(';%s\n' % loc_tag(node))

    def visit_exception_stmt(self, node, result): # todo: rename to exception_decl_stmt
        result.append_decl(self.indent())
        self.visit(node.children[0], result.declarations)
        result.append_decl(' exception; pragma exception_init(')
        self.visit(node.children[0], result.declarations)
        result.append_decl(', ')
        self.visit(node.children[1], result.declarations)
        if len(node.children) > 2: # if we have number with negation
            self.visit(node.children[2], result.declarations)
        result.append_decl('); %s\n' % loc_tag(node))

    def visit_tuple(self, node, result):
        result.append('(')
        for i, child in enumerate(node.children):
            if i:
                result.append(', ')
            self.visit(child, result)
        result.append(')')

    def visit_factor(self, node, result):
        self.generic_visit(node, result)

    def visit_MINUS(self, node, result):
        result.append('-')

    def visit_Token(self, node, result):
        trace('Token:', node.type, node.value)
        result.append(node.value)

    def visit_NAME(self, node, result):
        trace('NAME:', node.value)
        result.append(node.value)

    def visit_NUMBER(self, node, result):
        trace('NUMBER:', node.value)
        result.append(node.value)

    def visit_DEC_NUMBER(self, node, result):
        trace('DEC_NUMBER:', node.value)
        result.append(node.value)

    def visit_STRING(self, node, result):
        trace('STRING:', node.value)
        breakpoint()
        result.append(node.value)

    def visit_PERCENT(self, node, result):
        result.append('%')

    def visit_const_true(self, node, result):
        result.append('True')

    def visit_string(self, node, result):
        trace('string:', node.children[0])
        if node.children[0].type in ('QSTRING', 'QLONG_STRING'):
            self.visit(node.children[0], result)
        elif node.children[0].type in ('FSTRING', 'FLONG_STRING'):
            s = requote(node.children[0].value[1:])
            #s = s.replace("{", "'||").replace("}", "||'")
            expressions = curls.findall(s)
            for x in expressions:
                if ':' in x:
                    x1, x2 = x.split(':',1)
                    s = s.replace(x, "'||to_char(%s,'%s')||'" % (x1[1:], x2[:-1]))
                else:
                    s = s.replace(x, "'||%s||'" % x[1:-1])
            result.append(s)
        else:
            result.append(requote(node.children[0].value))

    def visit_number(self, node, result):
        trace('number:', node.children[0])
        self.visit(node.children[0], result)

    def visit_var_stmt(self, node, result):
        # variable declaration
        result.append_decl(self.indent())
        self.visit(node.children[0], result.declarations) # variable name
        var_name = result.declarations[-1]
        result.append_decl(' ')
        tmp = ListX()
        self.visit(node.children[1], tmp) # variable type
        if False: #~tmp[0] == 'type':
            result.append_decl('%s%%rowtype' % '.'.join(tmp[2:-1]))
        else:
            result.extend_decl(tmp)
            result.local_vars[var_name] = ''.join(tmp)
            if len(node.children) > 2:
                result.append_decl(' := ')
                self.visit(node.children[2], result.declarations)
                # result.append('(')
                # self.visit(node.children[2], result)
                # result.append(')')
            if len(node.children) > 3:
                breakpoint()
                result.append_decl(' := ')
                self.visit(node.children[3], result.declarations)
        del tmp
        result.append_decl(';%s\n' % loc_tag(node))

    def visit_decl_name(self, node, result):
        result.append(node.children[0].value)

    def visit_decl_type(self, node, result):
        #result.append(node.children[0].value)
        self.visit(node.children[0], result)

    def visit_type_constraint(self, node, result):
        child0 = node.children[0]
        if isinstance(node.children[0], Token):
            result.append(child0.value)
        elif isinstance(node.children[0], Tree):
            result.append('.'.join((c.value for c in child0.children)))
        else:
            breakpoint()

    def visit_cursor_stmt(self, node, result):
        result.append_decl("%scursor " % self.indent())
        self.visit(node.children[0], result.declarations) # name
        result.append_decl(" is ")
        if len(node.children) > 2:
            result.append_decl('(')
            self.visit(node.children[1], result.declarations)
            result.append_decl(')')
            self.visit(node.children[2], result.declarations)
        else:
            self.visit(node.children[1], result.declarations)
        result.append_decl(';%s\n' % loc_tag(node))

    def visit_IN(self, node, result):
        result.append(' in ')

    def visit_not_test(self, node, result):
        result.append('not ')
        self.generic_visit(node, result)

    def visit_type_stmt(self, node, result):
        """"array" "type" decl_name "[" type_constraint "]" "of" decl_type [ "(" type_constraint ")" ]"""
        tmp = ListX()
        for child in node.children:
            self.visit(child, tmp)
        name = tmp[0]
        if tmp[1] == 'record':
            result.append_decl('%stype %s is record ( TODO!!! ); %s\n' % ( self.indent(), name, loc_tag(node)))
        elif tmp[1] == 'array':
            size = tmp[2]
            subtype = tmp[3]
            result.append_decl('%stype %s is varray(%s) of %s; %s\n' % ( self.indent(), name, size, subtype, loc_tag(node)))
        elif tmp[1] == 'dict':
            subtype = tmp[2]
            index = tmp[3]
            result.append_decl('%stype %s is table of %s index by %s; %s\n' % ( self.indent(), name, index, subtype, loc_tag(node)))
        del tmp
        return

    def visit_type_size(self, node, result):
        self.visit(node.children[0], result)

    def visit_ARRAY(self, node, result):
        result.append('array')

    def visit_DICT(self, node, result):
        result.append('dict')

    def visit_RECORD(self, node, result):
        result.append('record')

    def visit_subtype_stmt(self, node, result):
        """decl_name decl_type [type_constraint]"""
        result.append_decl('%ssubtype ' % self.indent())
        self.visit(node.children[0], result.declarations) # decl_name
        result.append_decl(' is ')
        self.visit(node.children[1], result.declarations) # decl_type
        if len(node.children) > 2:
            result.append_decl('(')
            self.visit(node.children[2], result.declarations) # type_constraint
            result.append_decl(')')
        result.append_decl('; %s\n' % loc_tag(node))

    def visit_list(self, node, result):
        result.append('/*<list>*/')
        self.generic_visit(node, result)
    def visit_dict(self, node, result):
        result.append('/*<dict>*/')
        self.generic_visit(node, result)
    def visit_key_value(self, node, result):
        #result.append('/*<key_value>*/')
        self.generic_visit(node, result)

if __name__ == '__main__':
    kwargs = dict(postlex=PythonIndenter())
    parser = Lark_StandAlone(**kwargs)
    parser.options.propagate_positions = True
    
    infile = None
    outfile = None
    mapfile = None
    for arg in sys.argv[1:]:
        if arg in ('-v', '--verbose'):
            verbose = True
        elif not infile:
            infile = arg
        elif not outfile:
            outfile = arg
        elif not mapfile:
            mapfile = arg

    with open(infile, 'r') as f:
        lines = f.readlines()
        if not lines[-1].endswith('\n'):
            lines.append('\n')
        trace(lines)

        tree = parser.parse(''.join(lines))
        trace('*' * 30)
        trace(tree.pretty())
        
        trace('*' * 30)
        visitor = NodeVisitor()
        result = ListX()
        visitor.visit(tree, result)

        if outfile:
            out = open(outfile, 'w')
        else:
            out = sys.stdout

        i = 1
        LC = re.compile('/\*.+?\sline\:(\d+)\*/') # like /*xxx 123*/
        line_map = []
        if result.declarations:
            for x in ''.join(result.declarations).split('\n'):
                print(x, file=out)
                m = LC.search(x)
                if m:
                    #line_map[i] = m.groups()
                    line_map.append('%s=%s\n' % (i, m.group(1)))
                i += 1
        if result.body:
            for x in ''.join(result.body).split('\n'):
                print(x, file=out)
                m = LC.search(x)
                if m:
                    #line_map[i] = m.groups()
                    line_map.append('%s=%s\n' % (i, m.group(1)))
                i += 1
        if mapfile:
            #with open(mapfile, 'wb') as f:
            #    f.write(pickle.dumps(line_map))
            with open(mapfile, 'w') as f:
                for x in line_map:
                    f.write(x)

