from ethereum.ercs import IERC20

implements: IERC20

totalSupply: public(uint256)
balanceOf: public(HashMap[address, uint256])
allowance: public(HashMap[address, HashMap[address, uint256]])


@deploy
def __init__():
    self.totalSupply = 100 * 10 ** 18
    self.balanceOf[msg.sender] = 100 * 10 ** 18


@external
def transfer(receiver: address, amount: uint256) -> bool:
    self.balanceOf[msg.sender] -= amount
    self.balanceOf[receiver] += amount
    log IERC20.Transfer(sender=msg.sender, receiver=receiver, value=amount)
    return True


@external
def approve(spender: address, amount: uint256) -> bool:
    self.allowance[msg.sender][spender] = amount
    log IERC20.Approval(owner=msg.sender, spender=spender, value=amount)
    return True


@external
def transferFrom(owner: address, receiver: address, amount: uint256) -> bool:
    self.allowance[owner][msg.sender] -= amount
    self.balanceOf[owner] -= amount
    self.balanceOf[receiver] += amount
    log IERC20.Transfer(sender=owner, receiver=receiver, value=amount)
    return True


@external
def mint(receiver: address, amount: uint256):
    self.totalSupply += amount
    self.balanceOf[receiver] += amount
    log IERC20.Transfer(sender=empty(address), receiver=receiver, value=amount)


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


@view
@external
def maxFlashLoan(token: IERC20) -> uint256:
    if token.address == self:
        return max_value(uint256) - self.totalSupply

    return 0


@view
@external
def flashFee(token: IERC20, amount: uint256) -> uint256:
    return 0


@external
def flashLoan(
    receiver: IERC3156FlashBorrower,
    token: IERC20,
    amount: uint256,
    data: Bytes[65535],
) -> bool:
    assert token.address == self

    # Send our tokens to receiver
    self.totalSupply += amount
    self.balanceOf[receiver.address] += amount
    log IERC20.Transfer(sender=empty(address), receiver=receiver.address, value=amount)

    assert (
        # NOTE: `msg.sender` is original caller of delegatecall
        extcall receiver.onFlashLoan(msg.sender, IERC20(self), amount, 0, data)
        # NOTE: Magic value per ERC-3156
        == keccak256("ERC3156FlashBorrower.onFlashLoan")
    ), "Flashloan receiver not valid"

    # Get our tokens back (mimic a real flash lender)
    self.allowance[receiver.address][self] -= amount
    self.totalSupply -= amount
    self.balanceOf[receiver.address] -= amount
    log IERC20.Transfer(sender=receiver.address, receiver=empty(address), value=amount)

    return True
