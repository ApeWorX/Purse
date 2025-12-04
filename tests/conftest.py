from pathlib import Path

import pytest
from ape.contracts import ContractInstance, ContractMethodHandler


@pytest.fixture(scope="session")
def owner(accounts):
    return accounts[0]


@pytest.fixture(scope="session")
def other(accounts):
    return accounts[-1]


@pytest.fixture(scope="session")
def singleton(project, owner):
    return owner.deploy(project.Purse)


@pytest.fixture(scope="session")
def mocks():
    from ape import Project

    return Project(
        Path(__file__).parent,
        config_override=dict(contracts_folder="mocks"),
    )


@pytest.fixture(scope="session")
def token(mocks, owner):
    return owner.deploy(mocks.MockToken)


@pytest.fixture()
def purse(singleton, owner):
    with owner.delegate_to(singleton) as purse:
        yield purse


@pytest.fixture(scope="session")
def multicall(project, owner):
    return owner.deploy(project.Multicall)


@pytest.fixture(scope="session")
def create2_deployer(project, owner):
    return owner.deploy(project.Create)


@pytest.fixture(scope="session")
def sponsor(project, owner):
    return owner.deploy(project.Sponsor)


@pytest.fixture(scope="session")
def encode_accessory_data():
    def encode_accessory_data(
        *methods: str | ContractMethodHandler,
        accessory: ContractInstance | None = None,
    ) -> list[dict]:
        if accessory:
            return [
                dict(
                    accessory=accessory,
                    method=method,
                )
                for method in methods
            ]

        else:
            return [
                dict(
                    accessory=method.contract,
                    method=method.contract.contract_type.method_identifiers.get(
                        abi.selector
                    ),
                )
                for method in methods
                if not isinstance(method, str)
                for abi in method.abis
            ]

    return encode_accessory_data
