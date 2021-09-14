import sys
import ast

SP = '  '

class ListX(list):
    def add(self, value):
        if value is None:
            pass
        elif isinstance(value, (list, tuple)):
            super().extend(value)
        else:
            super().append(value)
            
class PlSqlMaker(ast.NodeVisitor):

    def __init__(self):
        self.offset = 0             # defines the indentation level
        self.remove_quote = False   # is used to convert string literal into cursor
        self.locals = {}            # holds definitions of local variables
        self.funcs = []
        self.autofunc = 0           # sequenced number to distinguish auto-generated functions, i.e. for "select into" ones

    def begin_index(self):
        """index of the current function body"""
        if not self.funcs:
            return 0
        else:
            return self.funcs[-1]

    def visit(self, node, result, delim=None):
        """Override original function."""
        if node is None:
            result.add("NULL")
        elif isinstance(node, str):
            result.add("'%s'"%node)
        elif isinstance(node, int):
            result.add(node)
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
        for field, value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        result.add(self.visit(item))
            elif isinstance(value, AST):
                result.add(self.visit(value))

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
        if self.remove_quote:
            result.add(node.s)
        else:
            result.add("'%s'"%node.s)
        
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
        result.add(") /*list*/")
        
    def visit_Tuple(self, node, result):
        #Tuple(elts, ctx)
        result.add("(")
        for x in node.elts:
            self.visit(x, result)
            result.add(",")
        result.add(") /*tuple*/")

    def visit_Set(self, node, result):
        #Set(elts)
        result.add("(")
        for x in node.elts:
            self.visit(x, result)
            result.add(",")
        result.add(") /*set*/")

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
        if isinstance( node.value, ast.Call) and (node.value.func.id in self._sys_funcs):
            pass
        else:
            result.add(';')

    def visit_NamedExpr(self, node, result):
        #NamedExpr(target, value) >=Py3.8 
        pass

    def visit_UnaryOp(self, node, result):
        #UnaryOp(op, operand)
        #import pdb; pdb.set_trace()
        if isinstance(node.op, (ast.UAdd, ast.USub)):
            self.visit(node.operand, result)
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

    _sys_funcs = {'_var': '', '_type': 'type ', '_subtype': 'subtype ', '_fetch': '',}
    _alias = {'print': 'dbms_output.put_line',}
    def visit_Call(self, node, result):
        #Call(func, args, keywords, starargs, kwargs)
        if node.func.id == '_selectinto':
            temp = ListX([])
            for x in node.args: self.visit(x, temp)
            fetch = ListX([])
            #self.offset += 1
            fetch.add('\n%sfunction select_into_%s(%s) return boolan as' % (self.indent(), self.autofunc, ', '.join(['%s out %s' % (x, self.locals.get(x,'varchar2')) for x in temp[1:]])))
            fetch.add('\n%sbegin' % self.indent())
            self.autofunc += 1
            select = temp[0].strip()[1:-1] # remove quotes
            i = select.find('from')
            select = select[:i] + ' into %s' % ', '.join(temp[1:]) +' '+select[i:]
            fetch.add('\n%s  %s' % (self.indent(), select))
            fetch.add(';\n%s  return := True;' % self.indent())
            fetch.add('\n%sexception when no_data_found then' % self.indent())
            fetch.add('\n%s  return False;' % self.indent())
            fetch.add('\n%send;' % self.indent())
            #self.offset -= 1
            #self.output[self.currentIf:self.currentIf] = fetch
            result[self.begin_index():self.begin_index()] = fetch # todo: correct insert line position
            result.add('select_into_%d(%s)' % (self.autofunc, ', '.join(temp[1:])))
            # also see visit_Expr() which has explicitly removre ';' after  pseudo function calls
        elif node.func.id in self._sys_funcs:
            result.pop(-1) # remove new line originated by visit_Expr()
            temp = ListX([])
            self.visit(node.args, temp)
            n = temp[0] # name
            v = temp[1] # definition
            if len(temp)>2:
                v = '%s(%s)' % (v, temp[2])

            t = self._sys_funcs.get(node.func.id, '')
            result.insert(self.begin_index(), '\n%s%s%s %s;--from _sys_func' % (self.indent(), t, n, v))  # move before "begin" line # todo: correct insert line position
            self.funcs[-1] += 1
            if node.func.id == '_var':
                self.locals[n] = v
            # also see visit_Expr() which has explicitly remove ';' after pseudo function calls
        else:
            fname = self._alias.get(node.func.id, node.func.id)
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
        if isinstance(node.value, ast.Name):
            result.add('%s.%s' % (node.value.id, node.attr))
        else:
            result.add('%s.%s' %  (node.value, node.attr)) # todo:expand node.name

    # Subscripting
    def visit_Subscript(self, node, result):
        #Subscript(value, slice, ctx)
        pass
        #self.visit(node.value)
        #self.visit(node.slice)

    def visit_Index(self, node, result):
        #Index(value)
        result.add('Index')
        self.visit(node.value, result)

    def visit_Slice(self, node, result):
        #Slice(lower, upper, step)
        result.add('Slice')
        self.visit(node.lower, result)
        self.visit(node.upper, result)
        self.visit(node.step, result)

    def visit_ExtSlice(self, node, result):
        #ExtSlice(dims)
        result.add('ExtSlice')
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
        result.add(';')

    def visit_AnnAssign(self, node, result):
        #AnnAssign(target, annotation, value, simple) Py3.6
        result.add('\n%s' % self.indent())
        self.visit(node.target, result)
        result.add(' := ')
        #? self.visit(node.annotation)
        self.visit(node.value, result)
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
        result.add(';')

#Print(dest, values, nl) Py2 only

    def visit_Raise(self, node, result):
        #Raise(exc, cause)
        result.add('\n%sraise' % self.indent())
        self.visit(node.exc, result)
        result.add(';')
        #? self.visit(node.cause)

    def visit_Assert(self, node, result):
        #Assert(test, msg)
        result.add('todo:Assert')
        self.visit(node.test, result)
        self.visit(node.msg, result)

#Delete(targets)

    def visit_Pass(self, node, result):
        #Pass
        result.add('\n%snull;' % self.indent())

    # Imports
    def visit_Import(self, node, result):
        #Import(names)
        result.add('\n%stodo:Import ' % self.indent())
        self.visit(node.names, result)

    def visit_ImportFrom(self, node, result):
        #ImportFrom(module, names, level)
        result.add('todo:ImportFrom')
        self.visit(node.module, result)
        self.visit(node.names, result)
        self.visit(node.level, result)

    def visit_alias(self, node, result):
        #alias(name, asname) TODO:
        result.add('todo:alias %s %s' % (node.name, node.asname))

    # Control Flow
    
    def visit_If(self, node, result):
        #If(test, body, orelse)
        self.currentIf = len(result)
        result.add('\n%sif ' % self.indent())
        self.visit(node.test, result)
        result.add(' then')
        self.offset += 1
        #import pdb; pdb.set_trace()
        self.visit(node.body, result)
        result.add('\n%selse' % self.indent(-1))
        self.visit(node.orelse, result)
        self.offset -= 1
        result.add('\n%send if;' % self.indent())
        
    def visit_For(self, node, result):
        result.add('\n%sfor ' % self.indent())
        self.visit(node.target, result)
        result.add(' in (\n%s' % self.indent(1))
        self.remove_quote = True
        self.visit(node.iter, result) # todo: convert from string to cursor
        self.remove_quote = False
        result.add('\n%s)' % self.indent())
        result.add('\n%sloop' % self.indent())
        self.offset += 1
        self.visit(node.body, result)
        #not used? self.visit(node.orelse)
        self.offset -= 1
        result.add('\n%send loop;' % self.indent())
        

    def visit_While(self, node, result):
        #While(test, body, orelse)
        result.add('\n%swhile ' % self.indent())
        self.visit(node.test, result)
        result.add('\n%sloop' % self.indent())
        self.offset += 1
        self.visit(node.body, result)
        #todo? self.visit(node.orelse, result)
        self.offset -= 1
        result.add('\n%send loop;' % self.indent())

    def visit_Break(self, node, result):
        #Break
        result.add('\n%sbreak;' % self.indent())

    def visit_Continue(self, node, result):
        #Continue
        result.add('\n%scontinue;' % self.indent())

    def visit_Try(self, node, result):
        #Try(body, handlers, orelse, finalbody) >= Py3.3
        result.add('\n%sbegin' % self.indent())
        self.offset += 1
        for x in node.body: self.visit(x, result)
        result.add('\n%sexception ' % self.indent(-1))
        self.visit(node.handlers, result)
        #todo: self.visit(node.orelse)
        result.add('\n%sfinally' % self.indent(-1))
        self.visit(node.finalbody, result)
        self.offset -= 1
        result.add("\n%send;" % self.indent())
        
    def visit_TryFinally(self, node, result):
        #TryFinally(body, finalbody) <= Py#3.2
        result.add('\n')
        self.offset += 1
        result.add('begin\n')
        for x in node.body: self.visit(x, result)
        result.add('\n%sfinally' % self.indent(-1))
        self.visit(node.finalbody, result)
        self.offset -= 1
        result.add("\n%send;" % self.indent())

    def visit_TryExcept(self, node, result):
        #TryExcept(body, handlers, orelse) <= Py#3.2
        self.offset += 1
        result.add('\n%sbegin\n%s' % (self.indent(-1), self.indent()))
        for x in node.body: self.visit(x, result)
        result.add('\n%sexception ' % self.indent(-1))
        self.visit(node.handlers, result)
        #todo:self.visit(node.orelse, result)
        self.offset -= 1
        result.add("\n%send;" % self.indent())

    def visit_ExceptHandler(self, node, result):
        #ExceptHandler(type, name, body)
        result.add('when ')
        self.visit(node.type, result)
        result.add(' then\n')
        result.add('%s%s := %s;' % (self.indent(), node.name, 'sql%errcode'));
        self.visit(node.body, result)
        
#With(items, body, type_comment)
#withitem(context_expr, optional_vars)

    # Function and class definitions

    def visit_FunctionDef(self, node, result):
        #FunctionDef(name, args, body, decorator_list, returns, type_comment)
        self.locals = {}
        self.autofunc = 0
        func = ListX()
        # todo: correct insert line position for enclosed functions
        func.add('\n%sprocedure %s (' % (self.indent(), node.name)) # todo: switch betwee procedure and function
        self.visit(node.args, func)
        func.append(') as')
        # for x in node.decorator_list:
            # #import pdb; pdb.set_trace()
            # self.visit(x, func)
            # func.add(';--local var\n')
        self.funcs.append(len(func)) #use stack of values to support enclosed functions with their own locals
        func.add('\n%sbegin--procedure' % self.indent())
        self.offset += 1
        for x in node.body: self.visit(x, func)
        #self.visit(node.decorator_list)
        #?self.visit(node.returns)
        self.offset -= 1
        func.add('\n%send;--procedure %s' % (self.indent(), node.name))
        self.funcs.pop(-1)
        result[self.begin_index():self.begin_index()] = func

#Lambda(args, body)

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
        result.add('%s %s' % (
            node.arg, 
            node.annotation.id if isinstance(node.annotation, ast.Name) \
            else node.annotation.s if isinstance(node.annotation, ast.Str) \
            else node.annotation))
        
    def visit_Return(self, node, result):
        #Return(value)
        result.add('\n%sreturn ' % self.indent())
        self.visit(node.value, result)
        result.add(';')

#Yield(value)
#YieldFrom(value)
#Global(names)
#Nonlocal(names)

    def visit_ClassDef(self, node, result):
        #ClassDef(name, bases, keywords, starargs, kwargs, body, decorator_list) 
        result.add('todo:ClassDef' % node.name) # what for, maybe package?
        self.visit(node.bases, result)
        self.visit(node.keywords, result)
        self.visit(node.starargs, result)
        self.visit(node.kwargs, result)
        self.visit(node.body, result, None)
        self.visit(node.decorator_list, result)

    # Async and await

#AsyncFunctionDef(name, args, body, decorator_list, returns, type_comment)
#Await(value)
#AsyncFor(target, iter, body, orelse)
#AsyncWith(items, body)
#async for loops and async with context managers. They have the same fields as For and With, respectively. Only valid in the body of an AsyncFunctionDef.

    def visit_Module(self, node, result):
        #Module(stmt* body, type_ignore *type_ignores)
        result.add('--****** module ******\n')
        self.funcs.append(len(result))
        self.visit(node.body, result, None) #for x in node.body: self.visit(x)
        result.add('\n--****** end of module ******\n')
        self.funcs.pop(-1)

#Interactive(stmt* body)
#Expression(expr body)


def do_plsql(fname):
    f = open(fname, "rb")
    content = f.read()
    root = ast.parse(content)
    p = PlSqlMaker()
    result = ListX([])
    p.visit(root, result)
    print(''.join(result))

if __name__=='__main__':
    if len(sys.argv) > 1:
        do_plsql(sys.argv[1])
    else:
        raise  "input file name is required"