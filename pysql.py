import sys
import ast

SP = '  '

class PlSqlMaker(ast.NodeVisitor):

    def __init__(self):
        self.offset = 0 # todo: use it to make indentations
        self.output = [] # produces output lines
        self.temp = None # temporary replacement for self.output, used when child lines should net directly produce output,, parent node will use their values stored in this list
        self.remove_quote = False # is used to convert string literal into cursor
        self.locals = {} # holds definitions of local variables
        self.begin_index = 0 # index of the current function body
        self.autofunc = 0 # sequenced number to distinguish auto-generated functions, i.e. for "select into" ones

    def start_temp(self):
        self.temp = []
        
    def end_temp(self):
        result = self.temp
        self.temp = None
        return result

    def visit(self, node):
        """Override original function."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is None:
            self.add("\n--%s is not supported!!!\n" % node.__class__.__name__)
            visitor = self.generic_visit
        return visitor(node)


    def sub_visit(self, node, delim=None):
#~        self.offset += 1
        if node is None:
            self.add("NULL")
        elif isinstance(node, str):
            self.add("'%s'"%node)
        elif isinstance(node, int):
            self.add(node)
        elif isinstance(node, (list, tuple)):
            for i, x in enumerate(node):
                if delim and i > 0:
                    self.add(delim)
                self.visit(x)
        else:
            self.visit(node)
#~        self.offset -= 1

    def indent(self):
        return SP*self.offset

    def add(self, arg):
        arg = arg.replace('\n', '\n' + self.indent())
        if self.temp is None:
            self.output.append(arg)
        else:
            self.temp.append(arg)

    # Literals
    def visit_Constant(self, node): # Py3.8
        #Constant(value, kind)
        self.add(node.value) #todo: depends on kind

    def visit_Num(self, node):
        #Num(n) <Py 3.8
        self.add(str(node.n))

    def visit_Str(self, node):
        #Str(s) <Py 3.8
        if self.remove_quote:
            self.add(node.s)
        else:
            self.add("'%s'"%node.s)
        
    def visit_FormattedValue(self, node):
        #FormattedValue(value, conversion, format_spec) 3.6
        #self.add(str(node.conversion))
        if node.format_spec:
            self.add("to_char(")
        self.sub_visit(node.value)
        if node.format_spec:
            self.add(", ")
            self.visit(node.format_spec)
            self.add(")")
            
        #todo:
        #self.sub_visit(node.conversion)
        #self.sub_visit(node.format_spec)

    def visit_JoinedStr(self, node):
        #JoinedStr(values)
        #todo
        for i, x in enumerate(node.values):
            if i> 0:
                self.add(" || ")
            self.visit(x)

    def visit_Bytes(self, node):
        #Bytes(s), <Py 3.8
        self.add(node.s)

    def visit_List(self, node):
        #List(elts, ctx)
        self.add("(")
        for x in node.elts:
            self.visit(x)
            self.add(",")
        self.add(") /*list*/")
        
    def visit_Tuple(self, node):
        #Tuple(elts, ctx)
        self.add("(")
        for x in node.elts:
            self.visit(x)
            self.add(",")
        self.add(") /*tuple*/")

    def visit_Set(self, node):
        #Set(elts)
        self.add("(")
        for x in node.elts:
            self.visit(x)
            self.add(",")
        self.add(") /*set*/")

    def visit_Dict(self, node):
        #Dict(keys, values)
        self.add("not supported")

#Ellipsis

    def visit_NameConstant(self, node):
        #NameConstant(value)
        self.sub_visit(node.value)

    # Variables

    def visit_Name(self, node):
        #Name(id, ctx)
        self.add(node.id)

    def visit_Load(self, node):
        #Load
        pass

    def visit_Store(self, node):
        #Store
        pass

    def visit_Del(self, node):
        #Del
        pass

    def visit_Starred(self, node):
        #Starred(value, ctx)
        pass


    # Expressions

    def visit_Expr(self, node):
        #Expr(value)
        self.sub_visit(node.value)
        if isinstance( node.value, ast.Call) and (node.value.func.id in self._sys_funcs):
            pass
        else:
            self.add(';\n')

    def visit_NamedExpr(self, node):
        #NamedExpr(target, value) >=Py3.8 
        pass

    def visit_UnaryOp(self, node):
        #UnaryOp(op, operand)
        #import pdb; pdb.set_trace()
        if isinstance(node.op, (ast.UAdd, ast.USub)):
            self.visit(node.operand)
            self.add("1;")
        elif isinstance(node.op, (ast.Not, ast.Invert)):
            self.visit(node.op)
            self.visit(node.operand)

    def visit_UAdd(self, node):
       #UAdd
       self.add('+') # todo: for strings convert to || operator
    def visit_USub(self, node):
       #USub
       self.add('-')
    def visit_Not(self, node):
       #Not
       self.add(' not ')
    def visit_Invert(self, node):
       #Invert
       self.add('-')

    def visit_BinOp(self, node):
        #BinOp(left, op, right)
        self.sub_visit(node.left)
        self.sub_visit(node.op)
        self.sub_visit(node.right)

    def visit_Add(self, node):
        #Add
        self.add('+')

    def visit_Sub(self, node):
        #Sub
        self.add('-')

    def visit_Mult(self, node):
        #Mult
        self.add('Mult')

    def visit_Div(self, node):
        #Div
        self.add('Div')

    def visit_FloorDiv(self, node):
        #FloorDiv
        self.add('FloorDiv')

    def visit_Mod(self, node):
        #Mod
        self.add('Mod')

    def visit_Pow(self, node):
        #Pow
        self.add('Pow')

    def visit_LShift(self, node):
        #LShift
        self.add('LShift')

    def visit_RShift(self, node):
        #RShift
        self.add('RShift')

    def visit_BitOr(self, node):
        #BitOr
        self.add('BitOr')

    def visit_BitXor(self, node):
        #BitXor
        self.add('BitXor')

    def visit_BitAnd(self, node):
        #BitAnd
        self.add('BitAnd')

    def visit_MatMult(self, node):
        #MatMult
        self.add('MatMult')

    def visit_BoolOp(self, node):
        #BoolOp(op, values)
        self.add('BoolOp')
        self.sub_visit(node.op)
        self.sub_visit(node.values)

    def visit_And(self, node):
        #And
        self.add('And')

    def visit_Or(self, node):
        #Or
        self.add('Or')

    def visit_Compare(self, node):
        #Compare(left, ops, comparators)
        self.add('Compare')
        self.sub_visit(node.left)
        self.sub_visit(node.ops)
        self.sub_visit(node.comparators)

    def visit_Eq(self, node):
        #Eq
        self.add('Eq')

    def visit_NotEq(self, node):
        #NotEq
        self.add('NotEq')

    def visit_Lt(self, node):
        #Lt
        self.add('Lt')

    def visit_LtE(self, node):
        #LtE
        self.add('LtE')

    def visit_Gt(self, node):
        #Gt
        self.add('Gt')

    def visit_GtE(self, node):
        #GtE
        self.add('GtE')

    def visit_Is(self, node):
        #Is
        self.add('Is')

    def visit_IsNot(self, node):
        #IsNot
        self.add('IsNot')

    def visit_In(self, node):
        #In
        self.add('In')

    def visit_NotIn(self, node):
        #NotIn
        self.add('NotIn')

    _sys_funcs = {'_var': '', '_type': 'type ', '_subtype': 'subtype ', '_fetch': '',}
    _alias = {'print': 'dbms_output.put_line',}
    def visit_Call(self, node):
        #Call(func, args, keywords, starargs, kwargs)
        if node.func.id == '_fetch':
            # .. todo: implement as a local function
            #import pdb; pdb.set_trace()
            self.start_temp()
            for x in node.args: self.visit(x)
            temp = self.end_temp()
            fetch = []
            self.autofunc += 1
            fetch.append('\nfunction select_into_%s(%s) return boolan as\nbegin\n' % (self.autofunc, ', '.join(['%s out %s' % (x, self.locals.get(x,'varchar2')) for x in temp[1:]])))
            select = temp[0].strip()[1:-1] # remove quotes
            i = select.find('from')
            select = select[:i] + ' into %s' % ', '.join(temp[1:]) +' '+select[i:]
            fetch.append(SP+select)
            fetch.append(';\n%sreturn := True;\n' % SP)
            fetch.append('exception when no_data_found then\n')
            fetch.append('%sreturn False;\n' % SP)
            fetch.append('end;')
            fetch = [x.replace('\n', '\n'+self.indent()) for x in fetch]
            #self.output[self.currentIf:self.currentIf] = fetch
            self.output[self.begin_index:self.begin_index] = fetch
            self.add('select_into_%d(%s)' % (self.autofunc, ', '.join(temp[1:])))
            # also see visit_Expr() which has explicitly removre ';' after  pseudo function calls
        elif node.func.id in self._sys_funcs:
            self.start_temp()
            self.sub_visit(node.args)
            n = self.temp[0] # name
            v = self.temp[1] # definition
            if len(self.temp)>2:
                v = '%s(%s)' % (v, self.temp[2])

            t = self._sys_funcs.get(node.func.id, '')
            self.end_temp()
            self.output.insert(self.begin_index, '\n' + self.indent() + '%s%s %s;--from _sys_func' % (t, n, v))  # move before "begin" line
            if node.func.id == '_var':
                self.locals[n] = v
            # also see visit_Expr() which has explicitly removre ';' after pseudo function calls
        else:
            fname = self._alias.get(node.func.id, node.func.id)
            self.add('%s (' %fname)
            self.sub_visit(node.args, ',')
            self.sub_visit(node.keywords, ',')
            #<Py3.5 self.sub_visit(node.starargs)
            #<Py3.5 self.sub_visit(node.kwargs)
            self.add(')')

    def visit_keyword(self, node):
        #keyword(arg, value)
        self.add('keyword')
        self.sub_visit(node.arg, ',')
        self.sub_visit(node.value)

    def visit_IfExp(self, node):
        #IfExp(test, body, orelse)
        self.add('if ')
        self.sub_visit(node.test)
        self.add(' then\n')
        self.sub_visit(node.body, None)
        self.add('\nelse\n')
        self.sub_visit(node.orelse, None)
        self.add('\nend if;\n')

    def visit_Attribute(self, node):
        #Attribute(value, attr, ctx)
        if isinstance(node.value, ast.Name):
            self.add('%s.%s' % (node.value.id, node.attr))
        else:
            self.add('%s.%s' %  (node.value, node.attr)) # todo:expand node.name

    # Subscripting
    def visit_Subscript(self, node):
        #Subscript(value, slice, ctx)
        pass
        #self.sub_visit(node.value)
        #self.sub_visit(node.slice)

    def visit_Index(self, node):
        #Index(value)
        self.add('Index')
        self.sub_visit(node.value)

    def visit_Slice(self, node):
        #Slice(lower, upper, step)
        self.add('Slice')
        self.sub_visit(node.lower)
        self.sub_visit(node.upper)
        self.sub_visit(node.step)

    def visit_ExtSlice(self, node):
        #ExtSlice(dims)
        self.add('ExtSlice')
        self.sub_visit(node.dims)

    # Comprehensions
#ListComp(elt, generators)
#SetComp(elt, generators)
#GeneratorExp(elt, generators)
#DictComp(key, value, generators)
#comprehension(target, iter, ifs, is_async)

    # Statements
    def visit_Assign(self, node):
        #Assign(targets, value, type_comment)
        #self.add('Assign')
        self.sub_visit(node.targets)
        self.add(' := ')
        self.sub_visit(node.value)
        self.add(';\n')

    def visit_AnnAssign(self, node):
        #AnnAssign(target, annotation, value, simple) Py3.6
        self.sub_visit(node.target)
        self.add(' := ')
        #? self.sub_visit(node.annotation)
        self.sub_visit(node.value)
        self.add(';\n')
        #? self.sub_visit(node.simple)

    def visit_AugAssign(self, node):
        #AugAssign(target, op, value)
        self.sub_visit(node.target)
        self.add(' := ')
        self.sub_visit(node.target)
        self.sub_visit(node.op)
        self.sub_visit(node.value)
        self.add(';\n')

#Print(dest, values, nl) Py2 only

    def visit_Raise(self, node):
        #Raise(exc, cause)
        self.add('raise')
        self.sub_visit(node.exc)
        self.add(';')
        #? self.sub_visit(node.cause)

    def visit_Assert(self, node):
        #Assert(test, msg)
        self.add('Assert')
        self.sub_visit(node.test)
        self.sub_visit(node.msg)

#Delete(targets)

    def visit_Pass(self, node):
        #Pass
        self.add('Pass')

    # Imports
    def visit_Import(self, node):
        #Import(names)
        self.add('Import')
        self.sub_visit(node.names)

    def visit_ImportFrom(self, node):
        #ImportFrom(module, names, level)
        self.add('ImportFrom')
        self.sub_visit(node.module)
        self.sub_visit(node.names)
        self.sub_visit(node.level)

    def visit_alias(self, node):
        #alias(name, asname) TODO:
        self.add('alias %s %s' % (node.name, node.asname))

    # Control Flow
    
    def visit_If(self, node):
        #If(test, body, orelse)
        self.currentIf = len(self.output)
        self.add('\nif ')
        self.sub_visit(node.test)
        self.offset += 1
        self.add(' then\n')
        #import pdb; pdb.set_trace()
        self.sub_visit(node.body, None)
        self.offset -= 1
        self.add('\n')
        self.offset += 1
        self.add('else\n')
        self.sub_visit(node.orelse, None)
        self.offset -= 1
        self.add('\nend if;\n')
        
    def visit_For(self, node):
        self.add('\nfor ')
        self.visit(node.target)
        self.add(' in (\n'+SP)
        self.remove_quote = True
        self.visit(node.iter) # todo: convert from string to cursor
        self.remove_quote = False
        self.add('\n )')
        self.offset += 1
        self.add('loop\n')
        self.sub_visit(node.body, None)
        #not used? self.sub_visit(node.orelse)
        self.offset -= 1
        self.add('\nend loop;\n')
        

    def visit_While(self, node):
        #While(test, body, orelse)
        self.add('While')
        self.sub_visit(node.test)
        self.offset += 1
        self.sub_visit(node.body, None)
        self.sub_visit(node.orelse, None)
        self.offset -= 1

    def visit_Break(self, node):
        #Break
        self.add('Break')

    def visit_Continue(self, node):
        #Continue
        self.add('Continue')

    def visit_Try(self, node):
        #Try(body, handlers, orelse, finalbody)
        self.add('\n')
        self.offset += 1
        self.add('begin\n')
        for x in node.body: self.visit(x)
        self.offset -= 1
        self.add('\nexception ')
        self.offset += 1
        self.sub_visit(node.handlers)
        #todo: self.sub_visit(node.orelse)
        self.offset -= 1
        self.add('\n')
        self.offset += 1
        self.add('finally--try\n') # ??
        self.sub_visit(node.finalbody, None)
        self.offset -= 1
        self.add("\nend;--try\n")
        
    def visit_TryFinally(self, node):
        #TryFinally(body, finalbody)
        self.add('\n')
        self.offset += 1
        self.add('begin\n')
        for x in node.body: self.visit(x)
        self.offset -= 1
        self.add('\n')
        self.offset += 1
        self.add('finally--try.finally\n') # ??
        self.sub_visit(node.finalbody, None)
        self.offset -= 1
        self.add("\nend;--try-finally\n")

    def visit_TryExcept(self, node):
        #TryExcept(body, handlers, orelse)
        self.add('\n')
        self.offset += 1
        self.add('begin\n')
        for x in node.body: self.visit(x)
        self.offset -= 1
        self.add('\nexception ')
        self.sub_visit(node.handlers)
        #todo:self.sub_visit(node.orelse)
        self.add("\nend;--try.except\n")

    def visit_ExceptHandler(self, node):
        #ExceptHandler(type, name, body)
        self.add('when ')
        self.sub_visit(node.type)
        self.add(' then\n')
        self.add(node.name + ' := sql%errcode;\n');
        self.sub_visit(node.body, None)
        
#With(items, body, type_comment)
#withitem(context_expr, optional_vars)

    # Function and class definitions

    def visit_FunctionDef(self, node):
        #FunctionDef(name, args, body, decorator_list, returns, type_comment)
        self.locals = {}
        self.autofunc = 0
        self.add('procedure %s (' % node.name) # todo: switch betwee procedure and function
        self.sub_visit(node.args)
        self.add(') as\n')
        # for x in node.decorator_list:
            # #import pdb; pdb.set_trace()
            # self.visit(x)
            # self.add(';--local var\n')
        self.begin_index = len(self.output) #todo: use stack of values to support enclosed functions with their own locals
        self.add('\nbegin\n')
        self.offset += 1
        for x in node.body: self.visit(x)
        #self.sub_visit(node.decorator_list)
        #?self.sub_visit(node.returns)
        self.offset -= 1
        self.add('end;--procedure\n')

#Lambda(args, body)

    def visit_arguments(self, node):
        #arguments(posonlyargs, args, vararg, kwonlyargs, kw_defaults, kwarg, defaults)
        #py3.8: self.sub_visit(node.posonlyargs)
        self.sub_visit(node.args, ', ')
        if node.vararg: self.sub_visit(node.vararg)
        self.sub_visit(node.kwonlyargs)
        if node.kwarg: self.sub_visit(node.kwarg)
        self.sub_visit(node.kw_defaults)
        
    def visit_arg(self, node):
        #arg(arg, annotation, type_comment)
        self.add('%s %s' % (
            node.arg, 
            node.annotation.id if isinstance(node.annotation, ast.Name) \
            else node.annotation.s if isinstance(node.annotation, ast.Str) \
            else node.annotation))
        
    def visit_Return(self, node):
        #Return(value)
        self.add('return %s' % node.value)

#Yield(value)
#YieldFrom(value)
#Global(names)
#Nonlocal(names)
    def visit_ClassDef(self, node):
        #ClassDef(name, bases, keywords, starargs, kwargs, body, decorator_list) 
        self.add('ClassDef' % node.name)
        self.sub_visit(node.bases)
        self.sub_visit(node.keywords)
        self.sub_visit(node.starargs)
        self.sub_visit(node.kwargs)
        self.sub_visit(node.body, None)
        self.sub_visit(node.decorator_list)

    # Async and await
    
#AsyncFunctionDef(name, args, body, decorator_list, returns, type_comment)
#Await(value)
#AsyncFor(target, iter, body, orelse)
#AsyncWith(items, body)
#async for loops and async with context managers. They have the same fields as For and With, respectively. Only valid in the body of an AsyncFunctionDef.

    def visit_Module(self, node):
        #Module(stmt* body, type_ignore *type_ignores)
        self.add('--****** module ******\n')
        self.sub_visit(node.body, None) #for x in node.body: self.visit(x)
        self.add('--****** end of module ******\n')
#Interactive(stmt* body)
#Expression(expr body)


def do_plsql(fname):
    f = open(fname, "rb")
    content = f.read()
    root = ast.parse(content)
    p = PlSqlMaker()
    p.visit(root)
    print(''.join(p.output))

if __name__=='__main__':
    if len(sys.argv) > 1:
        do_plsql(sys.argv[1])
    else:
        raise  "input file name is required"