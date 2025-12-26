from ape import convert, reverts
from ape.utils import ZERO_ADDRESS


def test_init(singleton, purse, owner):
    assert owner.delegate == singleton
    assert purse.address == owner.address
    assert len(purse.accessories) == 0


def test_can_transfer(purse, accounts):
    # NOTE: Make sure reentrancy doesn't lock us out of sending ether
    balance = purse.balance
    accounts[-1].transfer(purse.address, "1 ether")
    assert purse.balance - balance == convert("1 ether", int)


def test_add_rm_accessory(purse, dummy):
    assert dummy not in purse.accessories
    assert all(
        purse.contract.accessoryByMethodId(method.method) == ZERO_ADDRESS
        for method in dummy.methods
    )

    tx = purse.add_accessories(dummy, sender=purse.wallet)
    assert dummy in purse.accessories
    assert all(
        purse.contract.accessoryByMethodId(m.method) == dummy.address
        for m in dummy.methods
    )
    assert tx.events == [
        purse.contract.AccessoryUpdated(
            method=m.method,
            old_accessory=ZERO_ADDRESS,
            new_accessory=m.accessory,
        )
        for m in dummy.methods
    ]

    tx = purse.remove_accessories(dummy, sender=purse.wallet)
    assert dummy not in purse.accessories
    assert all(
        purse.contract.accessoryByMethodId(method.method) == ZERO_ADDRESS
        for method in dummy.methods
    )
    assert tx.events == [
        purse.contract.AccessoryUpdated(
            method=m.method,
            old_accessory=m.accessory,
            new_accessory=ZERO_ADDRESS,
        )
        for m in dummy.methods
    ]


def test_cant_call_arbitrary(purse):
    with reverts(message="Purse:!no-accessory-found"):
        purse.contract(data="0xa1b2c3d", sender=purse.wallet)
