from pyteal import *
def approval_program():
    on_creation = Seq([
        # store the creator of this app as "Creator"
        App.globalPut(Bytes("Creator"), Txn.sender()),
        # check if there are 5 arguments
        Assert(Txn.application_args.length() == Int(5)),
        # store all the arguments
        # the start and end time of the fund; during which users can donate fund in
        App.globalPut(Bytes("StartDate"), Btoi(Txn.application_args[0])),
        App.globalPut(Bytes("EndDate"), Btoi(Txn.application_args[1])),
        # the goal of the fund amount
        App.globalPut(Bytes("Goal"), Btoi(Txn.application_args[2])),
        # The fund owner's address
        App.globalPut(Bytes("Receiver"), Btoi(Txn.application_args[3])),
        # the close time of the fund; after which fund owner can claim the funds or the users
        # can reclaim their funds
        App.globalPut(Bytes("FundCloseDate"), Btoi(Txn.application_args[4])),
        # create another state data to store total funds raised
        App.globalPut(Bytes("Total"), Int(0)),
        Return(Int(1))
    ])

    # utility conditions for checking if the sender is the creator
    is_creator = Txn.sender() == App.globalGet(Bytes("Creator"))

    # a series of conditions that need to be checked upon donating
    donate_assertions = And(
        # check if the time is still between the valid donation time
        Global.latest_timestamp() >= App.globalGet(Bytes("StartDate")),
        Global.latest_timestamp() <= App.globalGet(Bytes("EndDate")),
        # there should be a group txs of two
        # the first tx is the app call tx, which specifies app call type and argument
        # the second tx should be a payment tx that transfers funds into escrow
        Global.group_size() == Int(2),
        Gtxn[1].type_enum() == TxnType.Payment,
        Gtxn[1].receiver() == App.globalGet(Bytes("Escrow")),
    )

    # the operations of donating
    donate = Seq([
        # check if all the conditions are met
        Assert(donate_assertions),
        # increase the donating amount to the global state "Total"
        App.globalPut(Bytes("Total"),Gtxn[1].amount()+App.globalGet(Bytes("Total"))),
        # increase the donating amount to the user's local state "MyAmountGiven"
        If(
            # check if the sender already donated
            App.localGet(Int(0), Bytes("MyAmountGiven")) >= Int(0),
            # if yes then increase the number
            App.localPut(Int(0), Bytes("MyAmountGiven"), App.localGet(Int(0), Bytes("MyAmountGiven")) + Gtxn[1].amount()),
            # if not then store the amount of this donation
            App.localPut(Int(0), Bytes("MyAmountGiven"), App.localGet(Int(0), Bytes("MyAmountGiven")))
        ),
        Return(Int(1))
    ])

    # a series of conditions that need to be checked upon claim the fund to the fund creator
    claim_assertions = And(
        # check if the fund raising goal is reached
        App.globalGet(Bytes("Total")) >= App.globalGet(Bytes("Goal")),
        # check if it has past the fund close time
        Global.latest_timestamp() >= App.globalGet(Bytes("FundCloseDate")),
        # there should be a group txs of two
        # the first tx is the app call tx, which specifies app call type and argument
        # the second tx sends all the funds from escrow contract to the fund owner ("Receiver") 
        # this tx should use the CloseRmainerTo parameter
        Global.group_size() == Int(2),
        Gtxn[1].sender() == App.globalGet(Bytes("Escrow")),
        Gtxn[1].receiver() == App.globalGet(Bytes("Receiver")),
        Gtxn[1].close_remainder_to() == App.globalGet(Bytes("Receiver"))
    )

    # the operations of claimng the funds
    claim = Seq([
        # check if all the conditions are met
        Assert(claim_assertions),
        # set the total funds amount to 0 
        App.globalPut(Bytes("Total"), Int(0)),
        Return(Int(1))
    ])

    # a series of conditions that need to be checked upon users reclaiming their funds
    reclaim_assertions = And(
        # only when the fund fails, i.e. the goal is not reached, can the users reclaim their funds
        App.globalGet(Bytes("Total")) < App.globalGet(Bytes("Goal")),
        # check if it has past the fund close time
        Global.latest_timestamp() >= App.globalGet(Bytes("FundCloseDate")),
        # there should be a group txs of two
        # the first tx is the app call tx, which specifies app call type and argument
        # the second transaction should be sending from the escrow contract to the user who's calling this app
        Global.group_size() == Int(2),
        Gtxn[1].receiver() == Gtxn[0].sender(),
        Gtxn[1].sender() == App.globalGet(Bytes("Escrow")),
        # check if it is the last reclaiming transaction for this user
        Or(
            # it's not the last reclaiming tx
            Gtxn[1].amount() + Gtxn[1].fee() < App.localGet(Int(0), Bytes("MyAmountGiven")),
            # it is the last reclaiming tx, then this tx should use the CloseRemainderTo parameter
            And(
                Gtxn[1].amount() + Gtxn[1].fee() == App.localGet(Int(0), Bytes("MyAmountGiven")),
                Gtxn[1].close_remainder_to() != Global.zero_address()
            )
        )
    )

    # the operations of reclaming the funds
    reclaim = Seq([
        # check if all the conditions are met
        Assert(reclaim_assertions),
        # reduce the reclaimed amount and tx fee from the user's local state storage i.e. "MyAmountGiven"
        App.localPut(Int(0), Bytes("MyAmountGiven"), App.localGet(Int(0), Bytes("MyAmountGiven")) - Gtxn[1].amount() - Gtxn[1].fee()),
        # reduce the amount of total funds in contract
        App.globalPut(Bytes("Total"), App.globalGet(Bytes("Total")) - Gtxn[1].amount() - Gtxn[1].fee()),
        Return(Int(1))
    ])
    
    # users should use NoOP type of app call to donate or claim or reclaim
    # depending on the arguements passed by the user, different logics are executed
    handle_noop = Cond(
        [Txn.application_args[0] == Bytes("donate"), donate],
        [Txn.application_args[0] == Bytes("claim"), claim],
        [Txn.application_args[0] == Bytes("reclaim"), reclaim]
    )

    # users can use Opt-In type of app call to opt-in for this app
    # this is always allowed
    handle_optin = Seq([
        Return(Int(1))
    ])

    # users can clear their state using closeout type of app call
    # this is always allowed
    handle_closeout = Seq([
        Return(Int(1))
    ])

    # the app creator can update the app logics
    # here we update the value of "Escrow" with the address of the escrow contract
    handle_updateapp = Seq([
        # make sure the tx sender is the creator
        Assert(is_creator),
        # make sure there is only 1 arugument
        Assert(Txn.application_args.length() == Int(1)),
        # store the argument as a global state "Escrow"
        App.globalPut(Bytes("Escrow"), Btoi(Txn.application_args[0])),
        Return(Int(1))
    ])

    # the app creator can delete the app when these conditions are met
    deleteapp_assertions = And(
        # make sure the tx sender is the creator
        is_creator,
        # make sure it has past the fund close time
        Global.latest_timestamp() >= App.globalGet(Bytes("FundCloseDate")),
        # make sure all the funds are claimed or reclaimed
        App.globalGet(Bytes("Total")) == Int(0)
    )

    # as long as all the conditions above are met, the app can be deleted
    handle_deleteapp = Seq([
        Assert(deleteapp_assertions),
        Return(Int(1))
    ])

    # depdning on different type of app call, executing different programs
    program = Cond(
        [Txn.application_id() == Int(0), on_creation], # if it is the app creation tx
        [Txn.on_completion() == OnComplete.NoOp, handle_noop],
        [Txn.on_completion() == OnComplete.OptIn, handle_optin],
        [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
        [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
        [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp]
    )
    return program

# compile and write the contract to file
with open('approval.teal', 'w') as f:
    compiled = compileTeal(approval_program(), Mode.Application, version = 3)
    f.write(compiled)