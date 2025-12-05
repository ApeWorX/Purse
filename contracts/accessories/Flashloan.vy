# pragma version 0.4.3
# pragma nonreentrancy on
"""
@title Purse Accessory - ERC3156 Flashloan Callback
@author Purse contributors
@dev
    This contract implements the `ERC3156FlashBorrower` interface and logic,
    so that the Purse can handle the flash loan context and continue operation
    by performing the encoded call provided with the callback data.

    It should not be possible for anyone besides the Purse itself to call this,
    as that would allow aribtrary approvals to malicious addresses, as well as
    enable arbitrary delegate calls more generally, if it was improperly handled.
"""
from ethereum.ercs import IERC20

interface IERC3156FlashBorrower:
    def onFlashLoan(
        initiator: address,
        token: IERC20,
        amount: uint256,
        fee: uint256,
        data: Bytes[65535],
    ) -> bytes32: nonpayable


implements: IERC3156FlashBorrower


@external
def onFlashLoan(
    initiator: address,
    token: IERC20,
    amount: uint256,
    fee: uint256,
    data: Bytes[1 + 65535 + 32 * 2],
) -> bytes32:
    """
    @notice Handle the ERC3156 Flashloan Callback
    @param initiator The initiator of the flash loan (ignored, should be `self`)
    @param token The token used for the flash loan
    @param amount The amount of `token` that is loaned
    @param fee The amount of `token` that must be repaid for borrowing `amount`
    @param data The encoded internal call to make, encoded as `to|value|data`
    @return The magic value `keccak256("ERC3156FlashBorrower.onFlashLoan")`
    """
    # NOTE: Only purse is allowed to do this
    assert tx.origin == self, "Flashloan:!authorized"

    # NOTE: Ensure that appropriate amount of allowance is made available to caller
    assert extcall token.approve(msg.sender, amount + fee, default_return_value=True)

    # Perform encoded call as Purse
    to: address = empty(address)
    amt: uint256 = 0
    to, amt = abi_decode(slice(data, 0, 32*2), (address, uint256))
    raw_call(to, slice(data, 32*2, len(data)), value=amt)

    # NOTE: Magic value per ERC-3156
    return keccak256("ERC3156FlashBorrower.onFlashLoan")
