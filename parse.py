import sys
import ast
import tokenize

# python -m tokenize hello.py

def do_generate_tokens(fname):
    with tokenize.open(fname) as f:
        tokens = tokenize.generate_tokens(f.readline)
        for token in tokens:
            print(token)

def do_tokenize(fname):
    with open(fname, 'rb') as f:
        tokens = tokenize.tokenize(f.readline)
        for token in tokens:
            print(token)


def do_dump(fname):
    f = open(fname, "rb")
    content = f.read()
    root = ast.parse(content)
    ast.dump(root)
    for node in ast.walk(root):
        print(node)


class Visitor(ast.NodeVisitor):

    def __init__(self):
        self.offset = 0

    def visit(self, node):
        """Override original function."""
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is None:
            self.trace(node.__class__.__name__, "is not supported!!!")
            visitor = self.generic_visit
        return visitor(node)


    def sub_visit(self, node):
        self.offset += 1
        if node is None:
            self.trace("<None>")
        elif isinstance(node, (str, int)):
            self.trace(node)
        elif isinstance(node, (list, tuple)):
            for x in node: self.visit(x)
        else:
            self.visit(node)
        self.offset -= 1

    def trace(self, *args):
        print(' .'*self.offset, *args)

    # Literals
    def visit_Constant(self, node): # Py3.8
        #Constant(value, kind)
        self.trace("constant", node.value)

    def visit_Num(self, node):
        #Num(n) <Py 3.8
        self.trace(type(node.n).__name__, node.n)

    def visit_Str(self, node):
        #Str(s) <Py 3.8
        self.trace("Str", node.s)
        
    def visit_FormattedValue(self, node):
        #FormattedValue(value, conversion, format_spec) 3.6
        self.trace('FormattedValue')
        self.sub_visit(node.value)
        self.sub_visit(node.conversion)
        self.sub_visit(node.format_spec)

    def visit_JoinedStr(self, node):
        #JoinedStr(values)
        self.trace('JoinedStr')
        self.sub_visit(node.values)

    def visit_Bytes(self, node):
        #Bytes(s), <Py 3.8
        self.trace('Bytes')
        self.sub_visit(node.s)

    def visit_List(self, node):
        #List(elts, ctx)
        self.trace("List")
        self.sub_visit(node.elts)
        
    def visit_Tuple(self, node):
        #Tuple(elts, ctx)
        self.trace("Tuple")
        self.sub_visit(node.elts)

    def visit_Set(self, node):
        #Set(elts)
        self.trace("Set")
        self.sub_visit(node.elts)

    def visit_Dict(self, node):
        #Dict(keys, values)
        self.trace("Dict")
        self.sub_visit(node.keys)
        self.sub_visit(node.values)

#Ellipsis

    def visit_NameConstant(self, node):
        #NameConstant(value)
        self.trace('NameConstant')
        self.sub_visit(node.value)

    # Variables

    def visit_Name(self, node):
        #Name(id, ctx)
        self.trace("name", node.id)

    def visit_Load(self, node):
        #Load
        self.trace("Load")

    def visit_Store(self, node):
        #Store
        self.trace("Store")

    def visit_Del(self, node):
        #Del
        self.trace("Del")

    def visit_Starred(self, node):
        #Starred(value, ctx)
        self.trace("Starred", node.value)


    # Expressions

    def visit_Expr(self, node):
        #Expr(value)
        self.trace('Expr')
        self.sub_visit(node.value)

    def visit_NamedExpr(self, node):
        #NamedExpr(target, value)Py3.8
        self.trace('NamedExpr')
        self.sub_visit(node.target)
        self.sub_visit(node.value)

    def visit_UnaryOp(self, node):
        #UnaryOp(op, operand)
        self.trace('UnaryOp')
        self.sub_visit(node.op)
        self.sub_visit(node.operand)

    def visit_UAdd(self, node):
        #UAdd
        self.trace('UAdd')

    def visit_USub(self, node):
        #USub
        self.trace('USub')

    def visit_Not(self, node):
        #Not
        self.trace('Not')

    def visit_Invert(self, node):
        #Invert
        self.trace('Invert')

    def visit_BinOp(self, node):
        #BinOp(left, op, right)
        self.trace('BinOp')
        self.sub_visit(node.left)
        self.sub_visit(node.op)
        self.sub_visit(node.right)

    def visit_Add(self, node):
        #Add
        self.trace('Add')

    def visit_Sub(self, node):
        #Sub
        self.trace('Sub')

    def visit_Mult(self, node):
        #Mult
        self.trace('Mult')

    def visit_Div(self, node):
        #Div
        self.trace('Div')

    def visit_FloorDiv(self, node):
        #FloorDiv
        self.trace('FloorDiv')

    def visit_Mod(self, node):
        #Mod
        self.trace('Mod')

    def visit_Pow(self, node):
        #Pow
        self.trace('Pow')

    def visit_LShift(self, node):
        #LShift
        self.trace('LShift')

    def visit_RShift(self, node):
        #RShift
        self.trace('RShift')

    def visit_BitOr(self, node):
        #BitOr
        self.trace('BitOr')

    def visit_BitXor(self, node):
        #BitXor
        self.trace('BitXor')

    def visit_BitAnd(self, node):
        #BitAnd
        self.trace('BitAnd')

    def visit_MatMult(self, node):
        #MatMult
        self.trace('MatMult')

    def visit_BoolOp(self, node):
        #BoolOp(op, values)
        self.trace('BoolOp')
        self.sub_visit(node.op)
        self.sub_visit(node.values)

    def visit_And(self, node):
        #And
        self.trace('And')

    def visit_Or(self, node):
        #Or
        self.trace('Or')

    def visit_Compare(self, node):
        #Compare(left, ops, comparators)
        self.trace('Compare')
        self.sub_visit(node.left)
        self.sub_visit(node.ops)
        self.sub_visit(node.comparators)

    def visit_Eq(self, node):
        #Eq
        self.trace('Eq')

    def visit_NotEq(self, node):
        #NotEq
        self.trace('NotEq')

    def visit_Lt(self, node):
        #Lt
        self.trace('Lt')

    def visit_LtE(self, node):
        #LtE
        self.trace('LtE')

    def visit_Gt(self, node):
        #Gt
        self.trace('Gt')

    def visit_GtE(self, node):
        #GtE
        self.trace('GtE')

    def visit_Is(self, node):
        #Is
        self.trace('Is')

    def visit_IsNot(self, node):
        #IsNot
        self.trace('IsNot')

    def visit_In(self, node):
        #In
        self.trace('In')

    def visit_NotIn(self, node):
        #NotIn
        self.trace('NotIn')

    def visit_Call(self, node):
        #Call(func, args, keywords, starargs, kwargs)
        #import pdb; pdb.set_trace()
        if isinstance(node.func, ast.Name):
            self.trace('call', node.func.id)
        else:
            self.trace('call')
            self.sub_visit(node.func)
        self.sub_visit(node.args)
        self.sub_visit(node.keywords)
        #<Py3.5 self.sub_visit(node.starargs)
        #<Py3.5 self.sub_visit(node.kwargs)

    def visit_keyword(self, node):
        #keyword(arg, value)
        self.trace('keyword')
        self.sub_visit(node.arg)
        self.sub_visit(node.value)

    def visit_IfExp(self, node):
        #IfExp(test, body, orelse)
        self.trace('IfExp')
        self.sub_visit(node.test)
        self.sub_visit(node.body)
        self.sub_visit(node.orelse)

    def visit_Attribute(self, node):
        #Attribute(value, attr, ctx)
        if isinstance(node.value, ast.Name):
            self.trace('Attribute', node.value.id, node.attr)
        else:
            self.trace('Attribute', node.value, node.attr) # todo:expand node.name

    # Subscripting
    def visit_Subscript(self, node):
        #Subscript(value, slice, ctx)
        self.trace('Subscript')
        self.sub_visit(node.value)
        self.sub_visit(node.slice)

    def visit_Index(self, node):
        #Index(value)
        self.trace('Index')
        self.sub_visit(node.value)

    def visit_Slice(self, node):
        #Slice(lower, upper, step)
        self.trace('Slice')
        self.sub_visit(node.lower)
        self.sub_visit(node.upper)
        self.sub_visit(node.step)

    def visit_ExtSlice(self, node):
        #ExtSlice(dims)
        self.trace('ExtSlice')
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
        self.trace('Assign')
        self.sub_visit(node.targets)
        self.sub_visit(node.value)

    def visit_AnnAssign(self, node):
        #AnnAssign(target, annotation, value, simple) Py3.6
        self.trace('Assign')
        self.sub_visit(node.target)
        self.sub_visit(node.annotation)
        self.sub_visit(node.value)
        self.sub_visit(node.simple)

    def visit_AugAssign(self, node):
        #AugAssign(target, op, value)
        self.trace('AugAssing')
        self.sub_visit(node.target)
        self.sub_visit(node.op)
        self.sub_visit(node.value)

#Print(dest, values, nl) Py2 only

    def visit_Raise(self, node):
        #Raise(exc, cause)
        self.trace('Raise')
        self.sub_visit(node.exc)
        self.sub_visit(node.cause)

    def visit_Assert(self, node):
        #Assert(test, msg)
        self.trace('Assert')
        self.sub_visit(node.test)
        self.sub_visit(node.msg)

#Delete(targets)

    def visit_Pass(self, node):
        #Pass
        self.trace('Pass')

    # Imports
    def visit_Import(self, node):
        #Import(names)
        self.trace('Import')
        self.sub_visit(node.names)

    def visit_ImportFrom(self, node):
        #ImportFrom(module, names, level)
        self.trace('ImportFrom')
        self.sub_visit(node.module)
        self.sub_visit(node.names)
        self.sub_visit(node.level)

    def visit_alias(self, node):
        #alias(name, asname) TODO:
        self.trace('alias', node.name, node.asname)

    # Control Flow
    
    def visit_If(self, node):
        #If(test, body, orelse)
        self.trace('if')
        self.offset += 1
        self.visit(node.test)
        for x in node.body: self.visit(x)
        for x in node.orelse: self.visit(x)
        self.offset -= 1
        
    def visit_For(self, node):
        self.trace('for')
        self.offset += 1
        self.visit(node.target)
        self.visit(node.iter)
        for x in node.body: self.visit(x)
        for x in node.orelse: self.visit(x)
        self.offset -= 1

    def visit_While(self, node):
        #While(test, body, orelse)
        self.trace('While')
        self.sub_visit(node.test)
        self.sub_visit(node.body)
        self.sub_visit(node.orelse)

    def visit_Break(self, node):
        #Break
        self.trace('Break')

    def visit_Continue(self, node):
        #Continue
        self.trace('Continue')

    def visit_Try(self, node):
        #Try(body, handlers, orelse, finalbody)
        self.trace('Try')
        self.sub_visit(node.body)
        self.sub_visit(node.handlers)
        self.sub_visit(node.orelse)
        self.sub_visit(node.finalbody)
        
    def visit_TryFinally(self, node):
        #TryFinally(body, finalbody)
        self.trace('TryFinally')
        self.sub_visit(node.body)
        self.sub_visit(node.finalbody)

    def visit_TryExcept(self, node):
        #TryExcept(body, handlers, orelse)
        self.trace('TryExcept')
        self.sub_visit(node.body)
        self.sub_visit(node.handlers)
        self.sub_visit(node.orelse)

    def visit_ExceptHandler(self, node):
        #ExceptHandler(type, name, body)
        self.trace('ExceptHandler')
        self.sub_visit(node.type)
        self.sub_visit(node.name)
        self.sub_visit(node.body)
        
#With(items, body, type_comment)
#withitem(context_expr, optional_vars)

    # Function and class definitions

    def visit_FunctionDef(self, node):
        #FunctionDef(name, args, body, decorator_list, returns, type_comment)
        self.trace('function', node.name)
        self.sub_visit(node.args)
        self.sub_visit(node.body)
        self.sub_visit(node.decorator_list)
        self.sub_visit(node.returns)

#Lambda(args, body)

    def visit_arguments(self, node):
        #arguments(posonlyargs, args, vararg, kwonlyargs, kw_defaults, kwarg, defaults)
        self.trace('arguments')
        #py3.8: self.sub_visit(node.posonlyargs)
        self.sub_visit(node.args)
        if node.vararg: self.sub_visit(node.vararg)
        self.sub_visit(node.kwonlyargs)
        if node.kwarg: self.sub_visit(node.kwarg)
        self.sub_visit(node.kw_defaults)
        
    def visit_arg(self, node):
        #arg(arg, annotation, type_comment)
        self.trace('arg', node.arg, node.annotation.id if isinstance(node.annotation, ast.Name) else node.annotation.s if isinstance(node.annotation, ast.Str) else node.annotation)
        
    def visit_Return(self, node):
        #Return(value)
        self.trace('return', node.value)

#Yield(value)
#YieldFrom(value)
#Global(names)
#Nonlocal(names)
    def visit_ClassDef(self, node):
        #ClassDef(name, bases, keywords, body, decorator_list) 
        self.trace('ClassDef', node.name)
        self.sub_visit(node.bases)
        self.sub_visit(node.keywords)
        self.sub_visit(node.body)
        self.sub_visit(node.decorator_list)

    # Async and await
    
#AsyncFunctionDef(name, args, body, decorator_list, returns, type_comment)
#Await(value)
#AsyncFor(target, iter, body, orelse)
#AsyncWith(items, body)
#async for loops and async with context managers. They have the same fields as For and With, respectively. Only valid in the body of an AsyncFunctionDef.

    def visit_Module(self, node):
        #Module(stmt* body, type_ignore *type_ignores)
        self.trace('Module')
        self.sub_visit(node.body) #for x in node.body: self.visit(x)

    def visit_Interactive(self, node):
        #Interactive(stmt* body)
        self.trace('Interactive')
        self.sub_visit(node.body)

    def visit_Expression(self, node):
        #Expression(expr body)
        self.trace('Expression')
        self.visit(node.expr)
        self.visit(node.body)


def do_visit(fname):
    f = open(fname, "rb")
    content = f.read()
    root = ast.parse(content)
    p = Visitor()
    p.visit(root)
    #print(p.calls)

def do_plsql(fname):
    f = open(fname, "rb")
    content = f.read()
    root = ast.parse(content)
    p = PlSqlMaker()
    p.visit(root)
    print(''.join(p.output))

if __name__=='__main__':
    fname = sys.argv[1] if len(sys.argv)>1 else "hello.py"

    #input("Press Enter to continue to tokenize.generate_tokens() ...")
    #do_generate_tokens(fname)

    #input("Press Enter to continue to tokenize.tokenize() ...")
    #do_tokenize(fname)

    #input("Press Enter to continue to ast.parse() and dump()...")
    #do_dump(fname)

    #input("Press Enter to continue to ast result visiting ...")
    do_visit(fname)
