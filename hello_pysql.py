class az_application:
    var i integer
    var d1 type(AZ_T1.COL3)
    var rt rowtype(dual)
    cursor cur q"select 1 from dual"
    var s string(10)
    var pkg_i integer
    #z = [1, 2, 3] # list expression is not supported

    i = 1

    def main(a: integer, b: string, c: date):
        type StrVarray is array(5) of string(10)
        type IntArray is dictionary [binary_integer] of integer
        type StrArray is dictionary [binary_integer] of string(10)
        type StrDict is dictionary [string(5)] of string(10)
        subtype Str12 string(12)
        var s string(10)
        var d date
        var i integer
        var eof boolean
        var array StrArray
        exception BulkErrors = -24381
        exception TestException = -24382
        
        @integer
        def increment(param:integer):
            var ii integer
            return param + 1

        open(cur)
        # example of cfetch_break() usage - the function has side effect - it executes break on cursors's EOF
        while True:
            cfetch_break(cur, i)
        # example of cfetch() usage with explicit  notfound() check
        while True:
            cfetch(cur, i)
            if notfound(c):
                break
        close(cur)
        
        for x in (q"""select 'Alex' as name, 'home' as place, sysdate as now
        from dual"""):
            print(f"{x.name} sends hello from {x.place} at {x.now:hh24:mi:ss}")
            i = i + 123
            i += 1
        try:
            if not i==0:
                print(1)
            else:
                print(2)
        except others as err:
            i = sqlcode
            print(f"error{i}")
        #finally: -- not supported
        #    print("finally")
            
        if substr("abc",1,1)=='a':
            i = 1
        else:
            i = 2

        # example of fetch statement
        try:
            fetch q"select 1, 'abc', sysdate from dual" into i, s, d
        except no_data_found:
            raise TestException
            raise "Error"
            raise (-20123, "Error")
            raise (20456, "Error")
            
        # example of fetch function
        if fetch(q"select 1, 'abc', sysdate from dual", i, s, d):
            print(f'i={i}, s={s}, d={d}')
        else:
            raise TestException

        q"insert into AZ_T1 (COL1) values (123)"
        q"insert into AZ_T1 (COL1) values (i)"

        array[0] = 'ABC'
        array[1] = 'XYZ'
        array[2] = array[0]
        for i in range(0, array.count-1):
            q"insert into AZ_T1 (COL1) values (array(i))"
        # Expected: for i in 1..array.count loop insert into AZ_T1 (COL1) values (array(i)); end loop;

        forall i in range(0, array.count-1):
            q"insert into AZ_T1 (COL1) values (array(i))"
        # Expected: forall i in 1..array.count /*todo: save exception */ insert into AZ_T1 (COL1) values (array(i));
    i = -2

exec(az_application.main(1, 'test', sysdate))

exec(print('123, 456'))

q"select * from az_T1"
q"rollback"