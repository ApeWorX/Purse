import ape
from ape.utils.misc import ZERO_ADDRESS
import pytest

from eth_abi import abi

from purse import Purse


@pytest.fixture()
def purse(singleton, owner, flashloan, flashlend):
    return Purse.initialize(owner, flashloan, flashlend, singleton=singleton)


def test_flashloan(purse, token, other):
    assert token.allowance(purse, other) == 0
    with ape.reverts(expected_message="Flashloan:!authorized"):
        purse.onFlashLoan(purse, token, 1_000, 0, b"", sender=other)
    assert token.allowance(purse, other) == 0

    tx = token.flashLoan(
        purse,
        token,
        1_000,
        # NOTE: View call is a no-op, should work
        abi.encode(["address", "uint256"], [purse.address, 0])
        + purse.maxFlashLoan.encode_input(token),
        sender=purse,
    )
    assert tx.events == [
        token.Transfer(sender=ZERO_ADDRESS, receiver=purse, value=1_000),
        token.Approval(owner=purse, spender=token, value=1_000),
        token.Transfer(sender=purse, receiver=ZERO_ADDRESS, value=1_000),
    ]


@pytest.fixture(scope="module")
def flash_receiver(mocks, owner):
    return owner.deploy(mocks.MockFlashReceiver)


def test_flashlend(purse, token, flash_receiver):
    assert purse.maxFlashLoan(token) == 0
    assert purse.flashFee(token, 1_000_000) == 0

    with ape.reverts(expected_message="Flashlend:!token-allowed"):
        purse.flashLoan(flash_receiver, token, token.balanceOf(purse) // 100, b"")

    purse.setFlashFee(token, 10_000)  # 10k mbps = 10 bps = 0.1%

    assert purse.maxFlashLoan(token) == token.balanceOf(purse)
    assert purse.flashFee(token, 10_000_000) == 10_000

    token.mint(flash_receiver, int(1e18), sender=purse)
    purse.flashLoan(
        flash_receiver,
        token,
        prev_bal := token.balanceOf(purse),
        b"",
    )
    assert token.balanceOf(purse) == prev_bal + int(prev_bal * (10_000 / 10_000_000))
