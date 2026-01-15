import ape
import pytest

from purse import Purse


@pytest.fixture()
def purse(singleton, owner, multicall):
    return Purse.initialize(owner, multicall, singleton=singleton)


def test_empty_multicall(purse):
    purse.execute([], sender=purse.wallet)


def test_single_multicall(purse, accounts):
    a = accounts[1]
    bal_a = a.balance
    purse.execute(
        [dict(target=a, value="1 ether", data=b"")],
        sender=purse.wallet,
    )
    assert a.balance - bal_a == ape.convert("1 ether", int)


def test_many_multicall(purse, accounts):
    a, b, c = accounts[1:4]
    bal_a = a.balance
    bal_b = b.balance
    bal_c = c.balance

    purse.execute(
        [
            dict(target=a, value="1 ether", data=b""),
            dict(target=b, value="2 ether", data=b""),
            dict(target=c, value="3 ether", data=b""),
        ],
        sender=purse.wallet,
    )

    assert a.balance - bal_a == ape.convert("1 ether", int)
    assert b.balance - bal_b == ape.convert("2 ether", int)
    assert c.balance - bal_c == ape.convert("3 ether", int)


def test_only_owner_can_multicall(purse, other):
    assert purse.address != other.address

    with ape.reverts(message="Multicall:!authorize"):
        purse.execute(
            [dict(target=other, value="1 ether", data=b"")],
            sender=other,
        )
