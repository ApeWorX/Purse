from typing import TYPE_CHECKING, Any

# NOTE: Added to `typing` in 3.11+
from typing_extensions import Self

from ape.contracts import (
    ContractInstance,
)
from ape.api.address import BaseAddress
from ape.contracts.base import (
    ContractCallHandler,
    ContractEvent,
    ContractEventWrapper,
    ContractTransactionHandler,
)
from ape.utils import ManagerAccessMixin, cached_property, ZERO_ADDRESS
from ape.types import AddressType, ContractLog, HexBytes
from .accessory import AccessoryMethod, Accessory
from .package import MANIFEST

if TYPE_CHECKING:
    from ape.api import AccountAPI
    from ape.api.transactions import ReceiptAPI


class Purse(BaseAddress, ManagerAccessMixin):
    def __init__(
        self,
        account: "AccountAPI | BaseAddress | AddressType",
        *accessories: "Accessory",
    ):
        from ape.api import AccountAPI

        self._address = self.conversion_manager.convert(account, AddressType)

        if isinstance(account, AccountAPI):
            self.wallet = account

        self.accessories = set(accessories)

        # Installed accessories in wallet, indexed by method ID
        self._cached_accessories_by_method_id = {
            method.method: accy for accy in accessories for method in accy.methods
        }
        self._last_indexed = 0

    @classmethod
    def initialize(
        cls,
        account: "AccountAPI",
        *accessories: "Accessory",
        singleton: ContractInstance | None = None,
    ) -> Self:
        assert singleton, "Needs support for package version"
        account.set_delegate(
            singleton,
            data=singleton.update_accessories.encode_input(
                [method.model_dump() for accy in accessories for method in accy.methods]
            ),
        )

        return cls(account, *accessories)

    @property
    def address(self) -> AddressType:
        return self._address

    @cached_property
    def wallet(self) -> "AccountAPI | None":
        if self.address in self.accounts_manager:
            return self.accounts_manager[self.address]

        return None

    def disable(self):
        # TODO: Remove all accessories at the same time?
        self.wallet.remove_delegate()

    @cached_property
    def contract(self) -> ContractInstance:
        contract_type = MANIFEST.Purse.model_copy(deep=True)

        # NOTE: Re-initialize every time accessories change to update contract_type in cache
        # TODO: Find some way to support diamond-like proxies in Ape?
        for accy in self.accessories:
            contract_type.abi.extend(accy.contract.contract_type.abi)

        # NOTE: Update local cache to avoid issues in parsing events
        self.chain_manager.contracts.contract_types[self.address] = contract_type

        return self.chain_manager.contracts.instance_at(
            self.address,
            contract_type=contract_type,
        )

    def _update_cache_from_logs(self, *logs: "ContractLog"):
        from purse.accessory import Accessory

        for log in logs:
            if (
                log.contract_address == self.address
                and log.event_name == "AccessoryUpdated"
            ):
                old = AccessoryMethod(method=log.method, accessory=log.old_accessory)
                new = AccessoryMethod(method=log.method, accessory=log.new_accessory)

                if new.accessory != ZERO_ADDRESS:
                    try:
                        accessory = next(
                            accy
                            for accy in self.accessories
                            if accy.address == new.accessory
                        )

                    except StopIteration:
                        self.accessories.add(accessory := Accessory(new.accessory))

                    self._cached_accessories_by_method_id[new.method] = accessory

                elif old.accessory != ZERO_ADDRESS:
                    if old.method in self._cached_accessories_by_method_id:
                        del self._cached_accessories_by_method_id[old.method]

                    try:
                        accessory = next(
                            accy
                            for accy in self.accessories
                            if accy.address == old.accessory
                        )

                    except StopIteration:
                        continue

                    if all(
                        method.method not in self._cached_accessories_by_method_id
                        for method in accessory.methods
                    ):
                        self.accessories.remove(accessory)

                self._last_indexed = log.block.number

    def has_accessory(self, accessory: "Accessory | AddressType") -> bool:
        from .accessory import Accessory

        if isinstance(accessory, Accessory):
            return accessory in self._cached_accessories_by_method_id.values() or any(
                self.contract.accessoryByMethodId(method.method) == accessory.address
                for method in accessory.methods
            )

        return self.has_accessory(Accessory(accessory))

    def add_accessories(
        self,
        *accessories: "Accessory",
        **txn_args,
    ) -> "ReceiptAPI":
        if not accessories:
            raise RuntimeError("Must provide at least one accessory")

        updates: list[dict] = [
            method.model_dump() for accy in accessories for method in accy.methods
        ]

        if "sender" not in txn_args and self.wallet:
            txn_args["sender"] = self.wallet

        receipt = self.contract.update_accessories(updates, **txn_args)

        self._update_cache_from_logs(*receipt.events)

        return receipt

    def remove_methods(
        self,
        *methods: "str | HexBytes",
        **txn_args,
    ) -> "ReceiptAPI":
        if not methods:
            raise RuntimeError("Must provide at least one accessory method")

        updates: list[dict] = [
            AccessoryMethod(accessory=ZERO_ADDRESS, method=method).model_dump()
            for method in methods
        ]

        if "sender" not in txn_args and self.wallet:
            txn_args["sender"] = self.wallet

        receipt = self.contract.update_accessories(updates, **txn_args)

        self._update_cache_from_logs(*receipt.events)

        return receipt

    def remove_accessories(
        self,
        *accessories: "Accessory",
        **txn_args,
    ) -> "ReceiptAPI":
        return self.remove_methods(
            *(m.method for accy in accessories for m in accy.methods),
            **txn_args,
        )

    def __getattr__(self, name: str) -> Any:
        if (attr := getattr(self.contract, name, None)) is not None:
            return attr

        # TODO: Create a better way to handle Diamond-style proxies
        for accy in self.accessories:
            match getattr(accy.contract, name, None):
                case ContractEvent() as attr:
                    self.contract.contract_type.abi.append(attr.abi)
                    attr.contract = self.contract

                    if name in self.contract._events_:
                        self.contract._events_[name].append(attr)
                    else:
                        self.contract._events_[name] = [attr]

                    return attr

                case ContractEventWrapper() as attr:
                    self.contract.contract_type.abi.extend(attr.abis)
                    attr.contract = self.contract

                    if name in self.contract._events_:
                        self.contract._events_[name].append(attr)
                    else:
                        self.contract._events_[name] = [attr]

                    return attr

                case ContractCallHandler() as attr:
                    self.contract.contract_type.abi.extend(attr.abis)
                    attr.contract = self.contract

                    if name in self.contract._view_methods_:
                        self.contract._view_methods_[name].append(attr)
                    else:
                        self.contract._view_methods_[name] = [attr]

                    return attr

                case ContractTransactionHandler() as attr:
                    self.contract.contract_type.abi.extend(attr.abis)
                    attr.contract = self.contract

                    if name in self.contract._mutable_methods_:
                        self.contract._mutable_methods_[name].append(attr)
                    else:
                        self.contract._mutable_methods_[name] = [attr]

                    return attr

        raise AttributeError(
            f"Method {name} not a registered accessory method or event"
        )

    def install(self, bot):
        """
        Dynamically maintain the set of all accessories installed for ``self``.

        Manages internal cache of an instance ``self`` of this class.
        """
        from silverback.types import TaskType

        async def load_purses_by_accessory(snapshot):
            df = self.contract.AccessoryUpdated.query(
                "method,old_accessory,new_accessory"
            )
            self._update_cache_from_logs(*df)

        load_purses_by_accessory.__name__ = (
            f"purse:main:{load_purses_by_accessory.__name__}"
        )
        bot.broker_task_decorator(TaskType.STARTUP)(load_purses_by_accessory)

        async def update_accessory(log):
            self._update_cache_from_logs(log)

        update_accessory.__name__ = f"purse:main:{update_accessory.__name__}"
        bot.broker_task_decorator(
            TaskType.EVENT_LOG, container=self.contract_AccessoryUpdated
        )(update_accessory)
