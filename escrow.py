from pyteal import *

# deploy app first then get id

# after compile this contract, update the app with this contract address


def escrow(app_id):
    # it's a transaction group with 2 transactions
    is_two_tx = Global.group_size() == Int(2)
    # the first tx is an app call tx
    is_appcall = Gtxn[0].type_enum() == TxnType.ApplicationCall
    # check the app called in the first tx
    is_appid = Gtxn[0].application_id() == Int(app_id)
    # check the type of the app call is NoOP
    acceptable_app_call = Gtxn[0].on_completion() == OnComplete.NoOp
    # make sure these 2 transactions are not rekey tx
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

with open('escrow.teal', 'w') as f:
    compiled = compileTeal(escrow(1), Mode.Application, version = 3)
    f.write(compiled)