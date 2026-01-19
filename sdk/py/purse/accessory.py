import string
from typing import TYPE_CHECKING, Any
from ape.api.address import BaseAddress
from ape.contracts import ContractInstance
from ape.types import AddressType
from ape.utils import ManagerAccessMixin
from ape.utils.misc import cached_property
from eth_pydantic_types import abi
from eth_utils.crypto import keccak
from ethpm_types.abi import MethodABI
from pydantic import BaseModel, field_validator

if TYPE_CHECKING:
    from .main import Purse


class AccessoryMethod(BaseModel):
    method: abi.bytes4
    accessory: abi.address

    @field_validator("method", mode="before")
    def convert_selector_to_method_id(cls, value: Any) -> Any:
        if isinstance(value, str) and not all(c in string.hexdigits for c in value):
            return keccak(text=value)[:4].hex()

        return value

    def __hash__(self) -> int:
        return int(self.accessory.lower().replace("0x", "") + self.method.hex(), 16)


class Accessory(BaseAddress, ManagerAccessMixin):
    def __init__(self, address: AddressType | ContractInstance, *purses: "Purse"):
        self._address = self.conversion_manager.convert(address, AddressType)

        if isinstance(address, ContractInstance):
            self.contract = address

        # Installed purses, indexed by purse address
        self.purses: dict[AddressType, "Purse"] = {
            purse.address: purse for purse in purses
        }

    @property
    def address(self) -> AddressType:
        return self._address

    # TODO: `Accessory.load_package_type(package: uri or PackageManifest, contract_name: str)`

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.address}>"

    def __hash__(self) -> int:
        return int(self.address.lower().replace("0x", ""), 16)

    def __eq__(self, other: Any):
        if isinstance(other, Accessory):
            return self.address == other.address

        return self.conversion_manager.convert(other, AddressType) == self.address

    @cached_property
    def contract(self) -> ContractInstance:
        return self.chain_manager.contracts.instance_at(self.address)

    @cached_property
    def methods(self) -> list[AccessoryMethod]:
        """List of all methods required to install this accessory"""

        return [
            AccessoryMethod(method=abi.selector, accessory=self.address)
            for abi in self.contract.contract_type.abi
            if isinstance(abi, MethodABI)
        ]

    def install(self, bot):
        """
        Dynamically load and maintain the set of all Purse(s) using Accessory ``self``.

        Manages ``self.purses``, which is state of type ``set[Purse]``.
        """
        from .main import Purse
        from .package import MANIFEST

        PurseContractType = MANIFEST.Purse

        @bot.on_startup()
        async def load_purses_by_accessory(_ss):
            df = PurseContractType.AccessoryUpdated.query(
                "datetime,contract_address,old_accessory,new_accessory",
            )
            # TODO: Prune "replacements" (where a newer row undoes an older one)

            # NOTE: Use `set` for `O(1)` __contains__ check
            self.purses = {
                row.contract_address: Purse(row.contract_address) for row in df
            }

        @bot.on_(PurseContractType.AccessoryUpdated, old_accessory=self.address)
        async def remove_purse(log):
            if log.contract_address in self.purses:
                del self.purses[log.contract_address]

        @bot.on_(PurseContractType.AccessoryUpdated, new_accessory=self.address)
        async def add_purse(log):
            if log.contract_address not in self.purses:
                self.purses[log.contract_address] = Purse(log.contract_address)
