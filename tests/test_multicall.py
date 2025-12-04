import ape
import pytest


@pytest.fixture()
def purse(singleton, owner, multicall, encode_accessory_data):
    with owner.delegate_to(
        singleton,
        # NOTE: Add multicall as an accessory at the same time
        data=singleton.update_accessories.encode_input(
            encode_accessory_data(multicall.execute)
        ),
    ) as purse:
        yield purse


def test_empty_multicall(owner, purse, multicall):
    purse(data=multicall.execute.encode_input([]), sender=owner)


def test_single_multicall(owner, purse, multicall, accounts):
    a = accounts[1]
    bal_a = a.balance
    purse(
        data=multicall.execute.encode_input(
            [
                dict(target=a, value="1 ether", data=b""),
            ]
        ),
        sender=owner,
    )
    assert a.balance - bal_a == ape.convert("1 ether", int)


def test_many_multicall(owner, purse, multicall, accounts):
    a, b, c = accounts[1:4]
    bal_a = a.balance
    bal_b = b.balance
    bal_c = c.balance

    purse(
        data=multicall.execute.encode_input(
            [
                dict(target=a, value="1 ether", data=b""),
                dict(target=b, value="2 ether", data=b""),
                dict(target=c, value="3 ether", data=b""),
            ]
        ),
        sender=owner,
    )

    assert a.balance - bal_a == ape.convert("1 ether", int)
    assert b.balance - bal_b == ape.convert("2 ether", int)
    assert c.balance - bal_c == ape.convert("3 ether", int)


def test_only_owner_can_multicall(purse, multicall, other):
    assert purse.address != other.address

    with ape.reverts(message="Multicall:!authorize"):
        tx = purse(
            data=multicall.execute.encode_input(
                [
                    dict(target=other, value="1 ether", data=b""),
                ]
            ),
            sender=other,
        )
        tx.show_trace()
