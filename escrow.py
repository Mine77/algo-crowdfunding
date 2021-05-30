from pyteal import *

# deploy app first then get id

# use goal app update to set the escrow address

# This contract only spends out
# it two transactions are grouped


def escrow(app_id):
    is_two_tx = Global.group_size() == Int(2)
    is_appcall = Gtxn[0].type_enum() == TxnType.ApplicationCall
    is_appid = Gtxn[0].application_id() == Int(app_id)
    acceptable_app_call = Or(
        Gtxn[0].on_completion() == OnComplete.NoOp,
        Gtxn[0].on_completion() == OnComplete.DeleteApplication
    )
    no_rekey = And(
        Gtxn[0].rekey_to() == Global.zero_address(),
        Gtxn[1].rekey_to() == Global.zero_address()
    )

    return And(
        is_two_tx,
        is_appcall,
        is_appid,
        acceptable_app_call,
        no_rekey,
    )

if __name__ == "__main__":
    program = escrow(1)
    teal = compileTeal(program, mode=Mode.Signature, version=3)
    f = open("escrow.teal", "w")
    f.write(teal)
    f.close()
    print()