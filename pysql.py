import sys
import traceback
import ast
import re
import pickle

line = 0
column = 0

SP = '  '
_sys_funcs = {'_var': '', '_type': 'type ', '_subtype': 'subtype ', '_fetch': '',
    'var': '', 'const': '', 'type': 'type ', 'subtype': 'subtype ', 'exception': '', 'cursor': 'cursor ',
    }
_alias = {'print': 'dbms_output.put_line',}

def loc_tag(node):
    try:
        return '/*%d:%d*/' % (node.lineno, node.col_offset)
    except AttributeError:
        return ''

def strip_type(name):
    """
    remove size constraint from the type name
    """
    if '(' in name:
        return name.split('(',1)[0]
    return name

def get_name(node):
    if isinstance(node, str):
        return node
    elif isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Str):
        return node.s
    elif isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Attribute):
        return '%s.%s' % (get_name(node.value), get_name(node.attr))
    else:
        #breakpoint()
        print('?', node.__class__.__name__)
        return '<<<<NULL>>>>'

class ListX(list):
    def __init__(self):
        self.local_vars = {}        # holds definitions of local variables
        self.locals = []            # holds generated code for local variables, fucntions and types TODO: start using it!
        self.autofunc = 0           # sequenced number to distinguish auto-generated functions, i.e. for "select into" ones

    def add(self, value, node=None):
        """
        Add generated value to the result
        """
        if value is None:
            pass
        elif isinstance(value, (list, tuple)):
            super().extend(value)
        else:
            super().append(value)
        if node:
            #breakpoint()
            self.add(loc_tag(node))

class Visitor():

    def visit(self, node, result, delim=None):
        """Override original function."""
        try:
            global line, column
            line, column = node.lineno, node.col_offset
        except:
            pass
        if node is None:
            result.add("NULL")
        elif isinstance(node, str):
            result.add("'%s'"%node)
        elif isinstance(node, bool):
            result.add(str(node))
        elif isinstance(node, int):
            result.add(str(node))
        elif isinstance(node, (list, tuple)):
            for i, x in enumerate(node):
                if delim and i > 0:
                    result.add(delim)
                self.visit(x, result)
        else:
            method = 'visit_' + node.__class__.__name__
            visitor = getattr(self, method, None)
            if visitor is None:
                visitor = self.generic_visit
            visitor(node, result)

    def generic_visit(self, node, result):
        """Called if no explicit visitor function exists for a node."""
        result.add("\n--%s is not supported!!!\n" % node.__class__.__name__)
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        result.add(self.visit(item, result))
            elif isinstance(value, ast.AST):
                result.add(self.visit(value, result))

def getStr(node):
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Str):
        return node.s
    elif isinstance(node, ast.Num):
        return str(node.n)
    elif isinstance(node, ast.Call):
        breakpoint()
        return getStr(node.func)+'~'+getStr(node.args)
    elif isinstance(node, list):
        #breakpoint()
        r = '[list]' + getStr(node[0])
        return r
    elif isinstance(node, ast.List):
        #breakpoint()
        r = '[List]'+ getStr(node.elts[0])
        return r


def getTarget(targets):
    if isinstance(targets, list):
        node = targets[0]
    else:
        node =  targets

    if isinstance(node, ast.Name):
        return node.id
    else:
        breakpoint()
        return '?1'

def getExpr(value):

    #breakpoint()
    # could ne Name, Call, Dict
    if isinstance(value, ast.Name):
        return value.id
    elif isinstance(value, ast.Call):
        return '%s(%s)' % (getStr(value.func), getStr(value.args[0]))
    elif isinstance(value, ast.Tuple):
        if len(value.elts) == 1:
            return getStr(value.elts[0])
        elif len(value.elts) > 1:
            return '%s := %s' % (getStr(value.elts[0]), getStr(value.elts[1]))
        else:
            return '?'
    elif isinstance(value, ast.Dict):
        return 'table of %s indexed by %s' % (getStr(value.values[0]), getStr(value.keys[0]))
    elif isinstance(value, ast.Str):
        return value.s
    else:
        breakpoint()
        return '???'
    return res


class DeclareMaker(Visitor):
    def visit_FunctionDef(self, node, result):
        #FunctionDef(name, args, body, decorator_list, returns, type_comment)
        # name defines type of directive - var|const|type|subtype|cursor
        # args are used for cursors only
        # body lits must to contain only single statement - an assignment whcih may be
        #   name = type = value -> target[0], target[1], expression - declarartion with initialization
        #   or
        #   name = type -> target[0], expression
        # expression can be Name, Call, Dict
        
        name = getTarget(node.body[0].targets)
        expr = getExpr(node.body[0].value)
        print(name, expr)
        return

        temp = ListX()
        breakpoint()
        for x in node.body: self.visit(x, temp)
        name = temp[0] # name
        expr = temp[1] # definition
        if node.name in ('var', 'const'):  #variable, constant
            breakpoint()
            if len(temp) > 3:
                # expected: {name} {type} '$Num$' {init_value}
                if temp[2] in ('$Num$',):
                    expr = expr + ' := ' + str(temp[3])
            elif temp[1] in ('$Call$', '$Name$'):
                # expected {name} '$Call$'|'$Name$' {type}
                if node.name == 'const':
                    expr = ' constant '+temp[2]
                else:
                    expr = temp[2]
            result.local_vars[name] = expr
                    
        elif node.name == 'subtype':
            if temp[1] in ('$Call$', '$Name$'):
                # expected {name} '$Call$'|'$Name$' {type}
                expr = 'is '+temp[2]
        elif temp[1]=='$Call$' and temp[2]=='[]': #varray
            # expected {name} '$Call$' '[]' {type} {size}
            expr = 'is varray(%s) of %s' % (temp[4], temp[3])
            
        elif temp[1]=='$Dict$': #associative arrays aka plsql table
            # expected {name} '$Dict$' {idx type} {type}
            expr = 'is table of %s index by %s' % (temp[3], temp[2])

        elif node.name=='exception' and temp[1] in ('$Num$','$UnaryOp$'):
            if len(temp) > 3:
                expr = 'exception; pragma exception_init(%s, %s%s)' % (name, temp[2], temp[3])
            else:
                expr = 'exception; pragma exception_init(%s, %s)' % (name, temp[2])
        elif node.name=='cursor' and temp[1] in ('$Str$',):
            args = ListX()
            breakpoint()
            self.visit(node.args, args)
            if args:
                expr = '(%s) is %s' % (', '.join(args), temp[2])
            else:
                expr = 'is %s' % temp[2]
            del args
        else:
            #breakpoint()
            expr = '?'
            expr +=', '.join(temp[1:])
        del temp

        kind = _sys_funcs.get(node.name, '') # 'type', 'subtype', 'cursor' or '' for var
        result.append('%s%s %s%s;' % (kind, name, expr, loc_tag(node)))

    def visit_Assign(self, node, result):
        #Assign(targets, value, type_comment)
        self.visit(node.targets, result)
        result.add('$'+node.value.__class__.__name__+'$')
        if isinstance(node.value, ast.Call):
            self.visit(node.value, result)
            #self.visit(node.value.func.elts, result)
            #result.add(node.value.args[0].n) # Num -> array size
        elif isinstance(node.value, ast.List):
            self.visit(node.value.elts, result)
        elif isinstance(node.value, ast.Set):
            self.visit(node.value.elts, result)
        elif isinstance(node.value, ast.Dict):
            self.visit(node.value.keys, result)
            self.visit(node.value.values, result)
        elif isinstance(node.value, ast.Num):
            result.add(node.value.n)
        elif isinstance(node.value, ast.Str):
            result.add(node.value.s)
        elif isinstance(node.value, ast.UnaryOp):
            self.visit(node.value, result)
        else:
            self.visit(node.value, result)

    def visit_List(self, node, result):
        #List(elts, ctx)
        result.add('[]')
        for x in node.elts:
            self.visit(x, result)

    def visit_Name(self, node, result):
        #Name(id, ctx)
        #result.add('$name$')
        result.add(node.id)

    def visit_Call(self, node, result):
        #Call(func, args, keywords, starargs, kwargs)
        #result.add('$call$')
        temp = ListX()
        
        try:
            if isinstance(node.func, ast.Name) and node.func.id == 'rowtype':
                #self.visit(node.args, temp)
                #result.add(temp[0] + '%rowtype')
                if node.args[0]:
                    result.add(node.args[0].id + '%rowtype')
                else:
                    result.add('?%rowtype')
                    print('?', 'rowtype() pseudeofunction requires a parameter (table or cursor name)')
                return
        except:
            pass
            #breakpoint()

        self.visit(node.func, temp) #result.add(node.func.id)
        complex = False
        while len(temp) > 1:
            complex = True
            result.add(temp.pop(0))
        val = temp.pop(0)
        for x in node.args: self.visit(x, temp)
        if temp:
            if complex:
                result.add(val)
                result.add(temp)
            else:
                val = '%s(%s)' % (val, ', '.join(temp))
                result.add(val)
        del temp

    def visit_UnaryOp(self, node, result):
        #UnaryOp(op, operand)
        if isinstance(node.op, ast.UAdd):
            result.add('+')
        elif isinstance(node.op, ast.USub):
            result.add('-')
        else:
            raise Exception("%s is not supported in context of declare functions")
        self.visit(node.operand, result)

    def visit_Num(self, node, result):
        #Num(n) <Py 3.8
        #result.add('$num$')
        result.add(str(node.n))

    def visit_Attribute(self, node, result):
        #Attribute(value, attr, ctx)
        breakpoint()

    def visit_Load(self, node, result):
        #Load
        pass

class PlSqlMaker(Visitor):

    def __init__(self):
        self.offset = 0             # defines the indentation level
        #self.remove_quote = False   # is used to convert string literal into cursor
        self.bulk = False
        self.parenthesis = False

    def indent(self, adjust=0):
        return SP*(self.offset+adjust)

    # Literals
    def visit_Constant(self, node, result): # Py3.8
        #Constant(value, kind)
        result.add(node.value) #todo: depends on kind

    def visit_Num(self, node, result):
        #Num(n) <Py 3.8
        result.add(str(node.n))

    def visit_Str(self, node, result):
        #Str(s) <Py 3.8
        #if self.remove_quote:
        #    result.add(node.s)
        #el
        if self.bulk:
            result.add(node.s)
            self.bulk = False
        else:
            result.add("'%s'" % node.s)
        
    def visit_FormattedValue(self, node, result):
        #FormattedValue(value, conversion, format_spec) 3.6
        #self.add(str(node.conversion))
        if node.format_spec:
            result.add("to_char(")
        self.visit(node.value, result)
        if node.format_spec:
            result.add(", ")
            self.visit(node.format_spec, result)
            result.add(")")
        #todo:
        #self.visit(node.conversion, result)
        #self.visit(node.format_spec, result)

    def visit_JoinedStr(self, node, result):
        #JoinedStr(values)
        #todo
        for i, x in enumerate(node.values):
            if i> 0:
                result.add(" || ")
            self.visit(x, result)

    def visit_Bytes(self, node, result):
        #Bytes(s), <Py 3.8
        result.add(node.s)

    def visit_List(self, node, result):
        #List(elts, ctx)
        result.add("(")
        for x in node.elts:
            self.visit(x, result)
            result.add(",")
        result.add(") /*list*/ %s" % loc_tag(node))
        
    def visit_Tuple(self, node, result):
        #Tuple(elts, ctx)
        result.add("(")
        for x in node.elts:
            self.visit(x, result)
            result.add(",")
        result.add(") /*tuple*/ %s" % loc_tag(node))

    def visit_Set(self, node, result):
        #Set(elts)
        result.add("(")
        for x in node.elts:
            self.visit(x, result)
            result.add(",")
        result.add(") /*set*/ %s" % loc_tag(node))

    def visit_Dict(self, node, result):
        #Dict(keys, values)
        result.add("/*!!! Dict is not supported! !!!*/")

#Ellipsis

    def visit_NameConstant(self, node, result):
        #NameConstant(value)
        self.visit(node.value, result)

    # Variables

    def visit_Name(self, node, result):
        #Name(id, ctx)
        result.add(node.id)

    def visit_Load(self, node, result):
        #Load
        pass

    def visit_Store(self, node, result):
        #Store
        pass

    def visit_Del(self, node, result):
        #Del
        pass

    def visit_Starred(self, node, result):
        #Starred(value, ctx)
        pass


    # Expressions

    def visit_Expr(self, node, result):
        #Expr(value)
        result.add('\n%s' % self.indent())
        self.visit(node.value, result)
        if isinstance( node.value, ast.Call):
            if isinstance(node.value.func, ast.Attribute):
                pass#breakpoint()
            elif node.value.func.id in _sys_funcs:
                #breakpoint()
                return
        else:
            result.add(loc_tag(node))
            result.add(';')

    def visit_NamedExpr(self, node, result):
        #NamedExpr(target, value) >=Py3.8 
        pass

    def visit_UnaryOp(self, node, result):
        #UnaryOp(op, operand)
        if isinstance(node.op, (ast.UAdd, ast.USub)):
            self.visit(node.operand, result)
            if isinstance(node.op, ast.USub):
                result.add("-1;")
            else:
                result.add("1;")
        elif isinstance(node.op, (ast.Not, ast.Invert)):
            self.visit(node.op, result)
            self.visit(node.operand, result)

    def visit_UAdd(self, node, result):
       #UAdd
       result.add(' + ') # todo: for strings convert to || operator
    def visit_USub(self, node, result):
       #USub
       result.add(' - ')
    def visit_Not(self, node, result):
       #Not
       result.add(' not ')
    def visit_Invert(self, node, result):
       #Invert
       result.add(' - ')

    def visit_BinOp(self, node, result):
        #BinOp(left, op, right)
        self.visit(node.left, result)
        self.visit(node.op, result)
        self.visit(node.right, result)

    def visit_Add(self, node, result):
        #Add
        result.add(' + ')

    def visit_Sub(self, node, result):
        #Sub
        result.add(' - ')

    def visit_Mult(self, node, result):
        #Mult
        result.add('todo:Mult')

    def visit_Div(self, node, result):
        #Div
        result.add('todo:Div')

    def visit_FloorDiv(self, node, result):
        #FloorDiv
        result.add('todo:FloorDiv')

    def visit_Mod(self, node, result):
        #Mod
        result.add('todo:Mod')

    def visit_Pow(self, node, result):
        #Pow
        result.add('todo:Pow')

    def visit_LShift(self, node, result):
        #LShift
        result.add('todo:LShift')

    def visit_RShift(self, node, result):
        #RShift
        result.add('todo:RShift')

    def visit_BitOr(self, node, result):
        #BitOr
        result.add('todo:BitOr')

    def visit_BitXor(self, node, result):
        #BitXor
        result.add('todo:BitXor')

    def visit_BitAnd(self, node, result):
        #BitAnd
        result.add('todo:BitAnd')

    def visit_MatMult(self, node, result):
        #MatMult
        result.add('todo:MatMult')

    def visit_BoolOp(self, node, result):
        #BoolOp(op, values)
        result.add('todo:BoolOp')
        self.visit(node.op, result)
        self.visit(node.values, result)

    def visit_And(self, node, result):
        #And
        result.add(' and ')

    def visit_Or(self, node, result):
        #Or
        result.add(' or ')

    def visit_Compare(self, node, result):
        #Compare(left, ops, comparators)
        self.visit(node.left, result)
        self.visit(node.ops, result)
        self.visit(node.comparators, result)

    def visit_Eq(self, node, result):
        #Eq
        result.add(' = ')

    def visit_NotEq(self, node, result):
        #NotEq
        result.add(' != ')

    def visit_Lt(self, node, result):
        #Lt
        result.add(' < ')

    def visit_LtE(self, node, result):
        #LtE
        result.add(' <= ')

    def visit_Gt(self, node, result):
        #Gt
        result.add(' > ')

    def visit_GtE(self, node, result):
        #GtE
        result.add(' >= ')

    def visit_Is(self, node, result):
        #Is
        result.add('todo:Is')

    def visit_IsNot(self, node, result):
        #IsNot
        result.add('todo:IsNot')

    def visit_In(self, node, result):
        #In
        result.add(' in ')

    def visit_NotIn(self, node, result):
        #NotIn
        result.add(' not in ')

    def visit_Call(self, node, result):
        #Call(func, args, keywords, starargs, kwargs)
        fname = get_name(node.func)
        if fname == 'selectinto':
            temp = ListX()
            for x in node.args: self.visit(x, temp)
            fetch = ListX()
            fetch.add('\n%sfunction select_into_%s(%s) return boolean as' % (
                self.indent(),
                result.autofunc,
                ', '.join(['%s out %s' % (x, strip_type(result.local_vars.get(x,'varchar2'))) for x in temp[1:]]))
                )
            fetch.add(loc_tag(node))
            fetch.add('\n%sbegin' % self.indent())
            result.autofunc += 1
            select = temp[0].strip()[1:-1] # remove quotes
            i = select.find('from')
            select = select[:i] + ' into %s' % ', '.join(temp[1:]) +' '+select[i:]
            fetch.add('\n%s  %s' % (self.indent(), select))
            fetch.add(';\n%s  return True;' % self.indent())
            fetch.add('\n%sexception when no_data_found then' % self.indent())
            fetch.add('\n%s  return False;' % self.indent())
            fetch.add('\n%send;' % self.indent())
            result.locals.extend(fetch)
            result.add('select_into_%d(%s)' % (result.autofunc-1, ', '.join(temp[1:])))
            # also see visit_Expr() which has explicitly removre ';' after  pseudo function calls
        elif fname == 'exec':
            result.add('exec ')
            self.visit(node.args, result, ',')
            self.visit(node.keywords, result, ',')
        elif fname == 'sql':
            if self.parenthesis:
                result.add("(")
            result.add(node.args[0].s)
            if self.parenthesis:
                result.add(")")
        elif fname == 'range':
            temp = ListX()
            self.visit(node.args, temp)
            result.add('%s .. %s' % (temp[0], temp[1]))
            del temp
        elif fname == 'bulk':
            self.bulk = True
            result.add('null')
        elif fname == 'open':
            temp = ListX();
            self.visit(node.args, temp)
            if len(temp) == 1:
                result.add('open %s' % temp[0])
            elif len(temp) > 1:
                result.add('open %s for %s' % (temp[0], temp[1]))
            del temp
        elif fname == 'fetch':
            temp = ListX();
            self.visit(node.args, temp)
            if len(temp) > 1:
                result.add('fetch %s into %s; exit when %s%%notfound' % (temp[0], temp[1], temp[0])) # todo: make function
            del temp
        elif fname == 'close':
            temp = ListX();
            self.visit(node.args, temp)
            if len(temp) > 0:
                result.add('close %s' % temp[0])
            del temp
        elif fname == 'type':
            temp = ListX();
            self.visit(node.args, temp)
            if len(temp) > 0:
                result.add('%s%type' % temp[0])
            del temp
        else:
            fname = _alias.get(fname, fname)
            result.add('%s (' %fname)
            self.visit(node.args, result, ',')
            self.visit(node.keywords, result, ',')
            #<Py3.5 self.visit(node.starargs)
            #<Py3.5 self.visit(node.kwargs)
            result.add(')')

    def visit_keyword(self, node, result):
        #keyword(arg, value)
        result.add('keyword')
        self.visit(node.arg, result, ',')
        self.visit(node.value, result)

    def visit_IfExp(self, node, result):
        #IfExp(test, body, orelse)
        result.add('%sif ' % self.indent())
        self.visit(node.test, result)
        result.add(' then')
        result.add(loc_tag(node))
        self.offset += 1
        self.visit(node.body, result, None)
        self.offset -= 1
        result.add('\n%selse' % self.indent())
        self.offset += 1
        self.visit(node.orelse, result, None)
        self.offset -= 1
        result.add('\n%send if;' % self.indent())

    def visit_Attribute(self, node, result):
        #Attribute(value, attr, ctx)
        result.add('%s.%s' % (get_name(node.value), get_name(node.attr)))
        return
        if isinstance(node.value, ast.Name):
            result.add('%s.%s' % (get_name(node.value), get_name(node.attr)))
        else:
            result.add('%s.%s' %  (node.value, node.attr)) # todo:expand node.name

    # Subscripting
    def visit_Subscript(self, node, result):
        #Subscript(value, slice, ctx)
        temp = ListX()
        self.visit(node.value, temp)
        self.visit(node.slice, temp)
        result.add('%s(%s)' % (temp[0], temp[1]))
        del temp

    def visit_Index(self, node, result):
        #Index(value)
        self.visit(node.value, result)

    def visit_Slice(self, node, result):
        #Slice(lower, upper, step)
        self.visit(node.lower, result)
        self.visit(node.upper, result)
        self.visit(node.step, result)

    def visit_ExtSlice(self, node, result):
        #ExtSlice(dims)
        self.visit(node.dims, result)

    # Comprehensions
#ListComp(elt, generators)
#SetComp(elt, generators)
#GeneratorExp(elt, generators)
#DictComp(key, value, generators)
#comprehension(target, iter, ifs, is_async)

    # Statements
    def visit_Assign(self, node, result):
        #Assign(targets, value, type_comment)
        #self.add('Assign')
        result.add('\n%s' % self.indent())
        self.visit(node.targets, result)
        result.add(' := ')
        self.visit(node.value, result)
        result.add(loc_tag(node))
        result.add(';')

    def visit_AnnAssign(self, node, result):
        #AnnAssign(target, annotation, value, simple) Py3.6
        result.add('\n%s' % self.indent())
        self.visit(node.target, result)
        result.add(' := ')
        #? self.visit(node.annotation)
        self.visit(node.value, result)
        result.add(loc_tag(node))
        result.add(';')
        #? self.visit(node.simple)

    def visit_AugAssign(self, node, result):
        #AugAssign(target, op, value)
        result.add('\n%s' % self.indent())
        self.visit(node.target, result)
        result.add(' := ')
        self.visit(node.target, result)
        self.visit(node.op, result)
        self.visit(node.value, result)
        result.add(loc_tag(node))
        result.add(';')

#Print(dest, values, nl) Py2 only

    def visit_Raise(self, node, result):
        #Raise(exc, cause)
        if isinstance(node.exc, ast.Name): # named exception
            result.add('\n%sraise %s' % (self.indent(), node.exc.id))
        elif isinstance(node.exc, ast.Tuple): # erro code and error message
            temp = ListX()
            self.visit(node.exc.elts, temp)
            if len(temp)>2: # includes UnaryOp
                if temp[1] == '-1;':
                    temp[0] = '-' + temp[0]
                result.add('\n%sraise_application_error(%s, %s)' % (self.indent(), temp[0], temp[2]))
            else:
                result.add('\n%sraise_application_error(%s, %s)' % (self.indent(), temp[0], temp[1]))
            del temp
        else:
            result.add('\n%sraise_application_error(-20000,' % self.indent())
            self.visit(node.exc, result)
            result.add(')')
        result.add(loc_tag(node))
        result.add(';')
        #? self.visit(node.cause)

    def visit_Assert(self, node, result):
        #Assert(test, msg)
        result.add('todo:Assert')
        self.visit(node.test, result)
        self.visit(node.msg, result)
        result.add(loc_tag(node))

#Delete(targets)

    def visit_Pass(self, node, result):
        #Pass
        result.add('\n%snull%s;' % (self.indent(), loc_tag(node)))

    # Imports
    def visit_Import(self, node, result):
        #Import(names)
        result.add('\n%stodo:Import ' % self.indent())
        self.visit(node.names, result)
        result.add(loc_tag(node))

    def visit_ImportFrom(self, node, result):
        #ImportFrom(module, names, level)
        result.add('todo:ImportFrom')
        self.visit(node.module, result)
        self.visit(node.names, result)
        self.visit(node.level, result)
        result.add(loc_tag(node))

    def visit_alias(self, node, result):
        #alias(name, asname) TODO:
        breakpoint()
        result.add('todo:alias %s %s' % (node.name, node.asname))
        result.add(loc_tag(node))

    # Control Flow
    
    def visit_If(self, node, result):
        #If(test, body, orelse)
        self.currentIf = len(result)
        result.add('\n%sif ' % self.indent())
        self.visit(node.test, result)
        result.add(' then')
        result.add(loc_tag(node))
        self.offset += 1
        self.visit(node.body, result)
        result.add('\n%selse' % self.indent(-1))
        self.visit(node.orelse, result)
        self.offset -= 1
        result.add('\n%send if;' % self.indent())
        
    def visit_For(self, node, result):
        bulk = self.bulk
        if bulk:
            result.add('\n%sforall ' % self.indent())
        else:
            result.add('\n%sfor ' % self.indent())
        self.visit(node.target, result)
        self.parenthesis = True
        result.add(' in ')
        self.visit(node.iter, result)
        self.parenthesis = False
        result.add(loc_tag(node))
        if not bulk:
            result.add('\n%sloop' % self.indent())
        self.offset += 1
        self.visit(node.body, result)
        #not used? self.visit(node.orelse)
        self.offset -= 1
        if not bulk:
            result.add('\n%send loop;' % self.indent())
        

    def visit_While(self, node, result):
        #While(test, body, orelse)
        result.add('\n%swhile ' % self.indent())
        self.visit(node.test, result)
        result.add('\n%sloop' % self.indent())
        result.add(loc_tag(node))
        self.offset += 1
        self.visit(node.body, result)
        #todo? self.visit(node.orelse, result)
        self.offset -= 1
        result.add('\n%send loop;' % self.indent())

    def visit_Break(self, node, result):
        #Break
        result.add('\n%sbreak;' % self.indent())
        result.add(loc_tag(node))

    def visit_Continue(self, node, result):
        #Continue
        result.add('\n%scontinue;' % self.indent())
        result.add(loc_tag(node))

    def visit_Try(self, node, result):
        #Try(body, handlers, orelse, finalbody) >= Py3.3
        result.add('\n%sbegin' % self.indent())
        result.add(loc_tag(node))
        self.offset += 1
        for x in node.body: self.visit(x, result)
        result.add('\n%sexception ' % self.indent(-1))
        self.visit(node.handlers, result)
        if node.orelse:
            #todo: self.visit(node.orelse)
            print("Warning: orelse block is not supported, skip it")
            result.add("\n%s--Warning: orelse block is not supported, skip it" % self.indent())
        if node.finalbody:
            #~result.add('\n%sfinally' % self.indent(-1))
            #~self.visit(node.finalbody, result)
            print("Warning: finally block is not supported, skip it")
            result.add("\n%s--Warning: finally block is not supported, skip it" % self.indent())
        self.offset -= 1
        result.add("\n%send;" % self.indent())
        
    def visit_TryFinally(self, node, result):
        #TryFinally(body, finalbody) <= Py#3.2
        print("Warning: finally block is not supported, skip it")
        result.add("\n%s--Warning: finally block is not supported, skip it" % self.indent())
        return
        result.add('\n')
        self.offset += 1
        result.add('begin\n')
        for x in node.body: self.visit(x, result)
        result.add('\n%sfinally' % self.indent(-1))
        result.add(loc_tag(node))
        self.visit(node.finalbody, result)
        self.offset -= 1
        result.add("\n%send;" % self.indent())

    def visit_TryExcept(self, node, result):
        #TryExcept(body, handlers, orelse) <= Py#3.2
        self.offset += 1
        result.add('\n%sbegin\n%s' % (self.indent(-1), self.indent()))
        for x in node.body: self.visit(x, result)
        result.add('\n%sexception ' % self.indent(-1))
        result.add(loc_tag(node))
        self.visit(node.handlers, result)
        #todo:self.visit(node.orelse, result)
        self.offset -= 1
        result.add("\n%send;" % self.indent())

    def visit_ExceptHandler(self, node, result):
        #ExceptHandler(type, name, body)
        result.add('when ')
        self.visit(node.type, result)
        result.add(' then')
        #~result.add('\n%s%s := %s;' % (self.indent(), node.name, 'sqlcode'));
        result.add(loc_tag(node))
        self.visit(node.body, result)
        
#With(items, body, type_comment)
#withitem(context_expr, optional_vars)

    # Function and class definitions

    def visit_FunctionDef(self, node, result):
        #FunctionDef(name, args, body, decorator_list, returns, type_comment)

        if node.name in _sys_funcs:
            temp = ListX()
            visitor = DeclareMaker()
            visitor.visit(node, temp)
            for i, x in enumerate(temp):
                temp[i] = "\n%s%s" % (self.indent(), x)
            result.locals.extend(temp)
            result.local_vars.update(temp.local_vars)
            # also see visit_Expr() which has explicitly remove ';' after pseudo function calls
            return
        else:
            ftype = 'procedure'
            returns = ''
            for x in node.decorator_list[:1]: # we use only 1st decorator
                ftype = 'function'
                returns = ' return '+x.id
            decl = ListX()
            decl.add('\n%s%s %s (' % (self.indent(), ftype, node.name))
            self.visit(node.args, decl)
            decl.append(')%s as' % returns)
            decl.add(loc_tag(node))
            func = ListX()
            func.local_vars.update(decl.local_vars)
            func.add('\n%sbegin --procedure' % self.indent())
            self.offset += 1
            for x in node.body: self.visit(x, func)
            #?self.visit(node.returns)
            self.offset -= 1
            func.add('\n%send;--procedure %s' % (self.indent(), node.name))

            result.locals.extend(decl)
            result.locals.extend(func.locals)
            result.locals.extend(func)

    def visit_Lambda(self, node, result):
        #Lambda(args, body)
        result.add('ARGS:')
        self.visit(node.args, result)
        result.add('BODY:')
        self.visit(node.body, result)

    def visit_arguments(self, node, result):
        #arguments(posonlyargs, args, vararg, kwonlyargs, kw_defaults, kwarg, defaults)
        #py3.8: self.visit(node.posonlyargs)
        self.visit(node.args, result, ', ')
        if node.vararg: self.visit(node.vararg, result)
        self.visit(node.kwonlyargs, result)
        if node.kwarg: self.visit(node.kwarg, result)
        self.visit(node.kw_defaults, result)
        
    def visit_arg(self, node, result):
        #arg(arg, annotation, type_comment)
        name = node.arg
        if node.annotation:
            type = get_name(node.annotation)
            result.local_vars[name] = type
            result.add('%s %s' % (name, type))
                #node.annotation.id if isinstance(node.annotation, ast.Name) \
                #else node.annotation.s if isinstance(node.annotation, ast.Str) \
                #else node.annotation))
        else:
            result.add(name)
        
    def visit_Return(self, node, result):
        #Return(value)
        result.add('\n%sreturn ' % self.indent())
        self.visit(node.value, result)
        result.add(loc_tag(node))
        result.add(';')

#Yield(value)
#YieldFrom(value)
#Global(names)
#Nonlocal(names)

    def visit_ClassDef(self, node, result):
        #ClassDef(name, bases, keywords, starargs, kwargs, body, decorator_list) 
        result.locals.append('create or replace package body %s as' % node.name)
        #self.visit(node.bases, result)
        #self.visit(node.keywords, result)
        #self.visit(node.starargs, result)
        #self.visit(node.kwargs, result)
        self.offset += 1
        self.visit(node.body, result, None)
        self.offset -= 1
        #self.visit(node.decorator_list, result)
        #result.add(loc_tag(node))
        result.add('\nend; -- package body %s' % node.name)
        result.add('\n/')

    # Async and await

#AsyncFunctionDef(name, args, body, decorator_list, returns, type_comment)
#Await(value)
#AsyncFor(target, iter, body, orelse)
#AsyncWith(items, body)
#async for loops and async with context managers. They have the same fields as For and With, respectively. Only valid in the body of an AsyncFunctionDef.

    def visit_Module(self, node, result):
        #Module(stmt* body, type_ignore *type_ignores)
        result.locals.append('--****** module ******\n')
        #self.funcs.append(len(result))
        self.visit(node.body, result, None) #for x in node.body: self.visit(x)
        result.add('\n--****** end of module ******\n')
        #self.funcs.pop(-1)

#Interactive(stmt* body)
#Expression(expr body)

LC = re.compile('/\*(\d+):(\d+)\*/')

def transform_file(fname):
    global line, column
    result = None
    line_map = {}
    try:
        f = open(fname, "rb")
        content = f.read()
        root = ast.parse(content)
        p = PlSqlMaker()
        result = ListX()
        p.visit(root, result)
        result = result.locals + result
        result = ''.join(result).split('\n')
        for i, line in enumerate(result):
            m = LC.search(line)
            if m:
                line_map[i] = m.groups()
            #print(line)
        #print(line_map)
    except Exception as e:
        print(traceback.format_exc())
        # or
        #print(sys.exc_info()[2])
        print('%s, %s at %d:%d' % (e, fname, line, column))
    return result, line_map

def pop(lst, idx=0, default=None):
    try:
        return lst.pop(idx)
    except IndexError:
        return default

if __name__=='__main__':
    args = sys.argv[1:]

    # input file name
    fname = pop(args)
    if fname:
        result, line_map = transform_file(fname)
    else:
        print("input file name is required, output file name is optional")
        exit(1)

    #output file name
    fname = pop(args)
    if fname=='-p':
        for line in result:
            print(line)
    elif fname and fname != '-':
        with open(fname, 'w') as f:
            f.writelines((l+'\n' for l in result))

    # mapping file name
    fname = pop(args)
    if fname=='-p':
        print(line_map)
    elif fname and fname != '-':
        with open(fname, 'wb') as f:
            f.write(pickle.dumps(line_map))
