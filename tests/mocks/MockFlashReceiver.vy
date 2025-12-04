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
    data: Bytes[65535],
) -> bytes32:
    # NOTE: Make sure this contract has enough balance prior to calling
    extcall token.approve(msg.sender, amount + fee)
    return keccak256("ERC3156FlashBorrower.onFlashLoan")
