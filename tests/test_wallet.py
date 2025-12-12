from ape import convert, reverts
from ape.utils import ZERO_ADDRESS


def test_init(singleton, purse, owner):
    # assert owner.delegate == singleton
    assert purse.address == owner.address
    assert purse.contract_type == singleton.contract_type


def test_can_transfer(purse, accounts):
    # NOTE: Make sure reentrancy doesn't lock us out of sending ether
    balance = purse.balance
    accounts[-1].transfer(purse, "1 ether")
    assert purse.balance - balance == convert("1 ether", int)


def test_add_rm_accessory(owner, purse, multicall, encode_accessory_data):
    # TODO: Add `.method_id(args_str)` to `ContractMethodHandler`
    accessory_data = encode_accessory_data(multicall.execute)
    method_id = accessory_data[0]["method"]
    assert purse.accessoryByMethodId(method_id) == ZERO_ADDRESS

    purse.update_accessories(accessory_data, sender=owner)
    assert purse.accessoryByMethodId(method_id) == multicall

    accessory_data[0]["accessory"] = ZERO_ADDRESS
    purse.update_accessories(accessory_data, sender=owner)
    assert purse.accessoryByMethodId(method_id) == ZERO_ADDRESS


def test_cant_call_arbitrary(owner, purse):
    with reverts(message="Purse:!no-accessory-found"):
        purse(data="0xa1b2c3d", sender=owner)
