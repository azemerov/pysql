# pysql
Python-style language for server-side stored procedures

PySQL is a proposed procedural language for Database stored procedures. It is proposed as a replacement for PL/SQL. Instead of bulky PL/SQL constructions it uses
Python-style syntax (which has to be extended in next versions). Version 0.01 should be considered as a proposal only, just to demonstrate the idea.

Current implementation simply transforms PySQL code into PL/SQL, with knowledge of PL/SQL bytecode it will be possible to procude  bytecode directly from PySQL.
Current implementation uses standard Python AST parser. As result we have some problems - 
1) Python syntax has nothing to address SQL sysntax. As result SQL expressions are provided as string literals.
2) Python language has no variable declarations, while PL/SQL bytecode needs to know variable types.
3) It is impossible to know in advance if we have use string concatenation or numerical summation. Even if we can deduce types from local variables we don't 
   know types for values retured by SQL select statements. As result, in general we cannot automatically convert string summation to string concatenation.

Currently, for issues ##1 and 2 we use pseudo functions _var(), _type() and _subtype() as a dirty workarounds. Later with usage of modified AST parser we may 
extend Python syntax with an additional elements to support PL/SQL constructions.
To address issue #3 we can use either 
    - interpolated strings (recommended way)
    - Oracle build-in function concat() which is limited by only two parameters
    - pseudo function _concat() which will convert list of input values into explicetly concatenation expression

An additional pseudo functions are used to simplify some PL/SQL constructions, i.e. instead of bulky select into statement combined an exception handler we use
function _selectinto(), i.e. 
    if not _selectinto("select NAME, AGE from EMPLOYEE where ID=123", name, age):
        raise "Employee ID (123) doesn't exists
such code results in a generation of additional local function which handles PL/SQL select into statement.
