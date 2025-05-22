# pragma version 0.4.2
# pragma nonreentrancy on
from ethereum.ercs import IERC20

interface IERC3156FlashBorrower:
    def onFlashLoan(
        initiator: address,
        token: IERC20,
        amount: uint256,
        fee: uint256,
        data: Bytes[65535],
    ) -> bytes32: nonpayable

interface IERC3156:
    def maxFlashLoan(token: IERC20) -> uint256: view
    def flashFee(token: IERC20, amount: uint256) -> uint256: view
    def flashLoan(
        receiver: IERC3156FlashBorrower,
        token: IERC20,
        amount: uint256,
        data: Bytes[65535],
    ) -> bool: nonpayable

implements: IERC3156


# TODO: Configure which tokens are allowed to be transferred?

@view
@external
def maxFlashLoan(token: IERC20) -> uint256:
    return staticcall token.balanceOf(self)


@view
def _fee(token: IERC20, amount: uint256) -> uint256:
    # TODO: Make this configurable?
    return amount // 100  # 1% fee


@view
@external
def flashFee(token: IERC20, amount: uint256) -> uint256:
    return self._fee(token, amount)


@external
def flashLoan(
    receiver: IERC3156FlashBorrower,
    token: IERC20,
    amount: uint256,
    data: Bytes[65535],
) -> bool:
    # Send our tokens to receiver
    assert extcall token.transfer(receiver.address, amount, default_return_value=True)

    # Tell receiver about the flashloan
    fee: uint256 = self._fee(token, amount)
    assert (
        # NOTE: `msg.sender` is original caller of delegatecall
        extcall receiver.onFlashLoan(msg.sender, token, amount, fee, data)
        # NOTE: Magic value per ERC-3156
        == keccak256("ERC3156FlashBorrower.onFlashLoan")
    )

    # Get our tokens back
    assert extcall token.transferFrom(receiver.address, self, amount + fee, default_return_value=True)

    return True
