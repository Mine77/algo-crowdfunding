from pyteal import *
def clear_program():
    return Return(Int(1))

# compile and write the contract to file
with open('clear.teal', 'w') as f:
    compiled = compileTeal(clear_program(), Mode.Application, version = 3)
    f.write(compiled)