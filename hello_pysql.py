def main(a: integer, b: string, c: date):

    _type(MyType, array) # pseudo function to declare type # TODO:
    _var(s, string, 10)  # pseudo function to declare variable, TODO: optional parameter for initial value
    _var(d, date)        # pseudo function to declare variable
    _var(i, integer)     # pseudo function to declare variable
    _var(x, integer)     # pseudo function to declare variable
    _var(y, integer)     # pseudo function to declare variable

    def increment(param:integer):
        return param + 1

    
    for x in ("""select 'Alex' as name, 'home' as place, sysdate as now
    from dual"""):
        print(f"{x.name} sends hello from {x.place} at {x.now:hh24:mi:ss}")
        i = i + 123
        i += 1
        #z = [1, 2, 3]
    try:
        if not i:
            print(1)
        else:
            print(2)
    except MyError as err:
        print(f"error{err}")
    finally:
        print("finally")
        
    if myfunc("abc"):
        i = 1
    else:
        i = 2

    if _selectinto("select 1, 2 from dual", x, y):
        print(f'i={i}, y={y}')
    else:
        raise "Error" # TODO:

print(123, 456)