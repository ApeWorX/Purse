# pragma version 0.4.3
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

# @custom:storage-location erc7201:purse.accessories.Flashlend
# keccak256(abi.encode(uint256(keccak256("purse.accessories.Flashlend")) - 1)) & ~bytes32(uint256(0xff))
feeBasis: HashMap[IERC20, uint256]  # 0x578c22acf65ce07623403df1f4aaaea33129ac33b22142a968e7c121335322


# NOTE: Can watch for generic events of this type to find Purses that have "opted-in" to flashloans
event FlashFeeUpdated:
    token: indexed(IERC20)
    milli_bps: uint256


@view
@external
def maxFlashLoan(token: IERC20) -> uint256:
    if self.feeBasis[token] == 0:
        return 0

    return staticcall token.balanceOf(self)


@view
def _fee(token: IERC20, amount: uint256) -> uint256:
    return self.feeBasis[token] * amount // 10_000_000


@view
@external
def flashFee(token: IERC20, amount: uint256) -> uint256:
    return self._fee(token, amount)


@external
def setFlashFee(token: IERC20, feeBasis: uint256):
    assert feeBasis <= 10_000_000, "Flashlend:incorrect-fee-basis"
    # NOTE: Can only work in a EIP-7702 context from Purse
    assert tx.origin == self, "Flashlend:!authorized"

    self.feeBasis[token] = feeBasis
    log FlashFeeUpdated(token=token, milli_bps=feeBasis)


@external
# NOTE: Non-reentrant
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
    assert fee > 0, "Flashlend:!token-allowed"
    assert (
        # NOTE: `msg.sender` is original caller of delegatecall
        extcall receiver.onFlashLoan(msg.sender, token, amount, fee, data)
        # NOTE: Magic value per ERC-3156
        == keccak256("ERC3156FlashBorrower.onFlashLoan")
    ), "Flashlend:!receiver-returndata-invalid"

    # Get our tokens back
    assert extcall token.transferFrom(
        receiver.address,
        self,
        amount + fee,
        default_return_value=True,
    )

    return True
