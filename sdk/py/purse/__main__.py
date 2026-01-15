from typing import TYPE_CHECKING
from ape.api.address import Address
import click

from ape.cli import (
    ApeCliContextObject,
    ConnectedProviderCommand,
    account_option,
    ape_cli_context,
)
from ape.contracts import ContractContainer
from ape.types import AddressType
from createx import CreateX
from eth_utils.crypto import keccak
from purse import Purse, Accessory

from .package import ACCESSORIES, DEPLOYMENTS, MANIFEST

if TYPE_CHECKING:
    from ape.api import AccountAPI


@click.group()
def cli():
    """Commands for managing a Purse-enabled wallet"""


@cli.command(cls=ConnectedProviderCommand)
@ape_cli_context()
@click.argument("address")
def check(cli_ctx: ApeCliContextObject, address: str):
    """Check if ADDRESS has Purse delegate enabled, then check version of accessories."""

    if address in cli_ctx.account_manager.aliases:
        account = cli_ctx.account_manager.load(address)

    else:
        account = Address(cli_ctx.conversion_manager.convert(address, AddressType))

    if not (delegate := account.delegate):
        click.secho("No delegate detected", fg="yellow")
        return 1

    elif not (singleton := DEPLOYMENTS.get(keccak(delegate.code).hex())):
        click.secho("Account is not delegated to Purse", fg="red")
        return 1

    elif singleton != (latest := list(DEPLOYMENTS.values())[-1]):
        click.secho(
            f"Not using the latest version of Purse, please upgrade to {latest}",
            fg="yellow",
        )

    else:
        click.secho("Delegated to latest version of Purse!", fg="green")

    purse = Purse(account)

    if not (accessory_deployments := ACCESSORIES.get(singleton, {})):
        click.secho(f"No known accessories for version at {singleton}", fg="yellow")
        return 1

    for accessory_name, accessory_addresses in accessory_deployments.items():
        for address in accessory_addresses:
            if purse.has_accessory(accessory := Accessory(address)):
                if address == (latest := accessory_addresses[-1]):
                    click.secho(
                        f"Account has latest accessory '{accessory_name}' for Purse version",
                        fg="green",
                    )
                else:
                    click.secho(
                        f"Account has an older accessory '{accessory_name}'"
                        f" and should be upgraded to {latest}",
                        fg="yellow",
                    )

                if not all(
                    purse.contract.accessoryByMethodId(method.method)
                    == accessory.address
                    for method in accessory.methods
                ):
                    click.secho(
                        "Account has not installed all neccessary methods for accessory!",
                        fg="red",
                    )

                break

        else:
            click.secho(
                f"Account doesn't have accessory '{accessory_name}'", fg="green"
            )


@cli.command(cls=ConnectedProviderCommand)
@ape_cli_context()
@account_option()
@click.argument("accessories", nargs=-1)
def enable(cli_ctx, account: "AccountAPI", accessories: list[str]):
    """Enable Purse w/ 1 or more Accessories added"""

    singleton = cli_ctx.chain_manager.contracts.instance_at(
        list(DEPLOYMENTS.values())[-1],
        contract_type=MANIFEST.Purse,
    )
    valid_choices = ACCESSORIES.get(singleton.address, {})
    accessories: list[Accessory] = [
        Accessory(valid_choices.get(name, [])[-1]) for name in accessories
    ]

    # TODO: Why doesn't `KeyfileAccount.sign_authorization` display warning?
    accessories_str = "\n- " + "\n- ".join(a.address for a in accessories)
    if click.confirm(f"Enable {singleton} with accessories:{accessories_str}\n\n"):
        Purse.initialize(account, *accessories, singleton=singleton)


@cli.command(cls=ConnectedProviderCommand)
@account_option()
def disable(account: "AccountAPI"):
    """Remove Purse from your account"""

    purse = Purse(account)
    purse.disable()


@cli.group()
def sudo():
    """Manage System Contracts"""


@sudo.group()
def deploy():
    """Deploy the Purse system contracts and accessories using CreateX"""


@deploy.command(cls=ConnectedProviderCommand)
@account_option()
def singleton(account):
    """Deploy the Purse singleton contract using CreateX"""

    try:
        createx = CreateX()
    except RuntimeError:
        createx = CreateX.inject()

    deployment = createx.deploy(
        ContractContainer(MANIFEST.Purse),
        redeploy_protection=False,
        sender_protection=False,
        sender=account,
        salt="Purse",
    )
    click.secho(f"Purse singleton deployed to {deployment}", fg="green")


@deploy.command(cls=ConnectedProviderCommand)
@account_option()
@click.argument("accessory")
def accessory(account, accessory):
    """Deploy a Purse accessory from this project"""

    if not (Accessory := ContractContainer(MANIFEST.get_contract_type(accessory))):
        raise click.UsageError(f"'{accessory}' is not a valid accessory.")

    try:
        createx = CreateX()
    except RuntimeError:
        createx = CreateX.inject()

    deployment = createx.deploy(
        Accessory,
        redeploy_protection=False,
        sender_protection=False,
        sender=account,
        salt=f"Purse {accessory}",
    )
    click.secho(f"Accessory '{accessory}' deployed to {deployment}", fg="green")


if __name__ == "__main__":
    cli()
