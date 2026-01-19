from pathlib import Path

import pytest

from purse import Accessory, Purse


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
    # NOTE: Empty purse for testing purposes
    return Purse.initialize(owner, singleton=singleton)


@pytest.fixture(scope="session")
def create2_deployer(project, owner):
    return Accessory(owner.deploy(project.Create))


@pytest.fixture(scope="session")
def multicall(project, owner):
    return Accessory(owner.deploy(project.Multicall))


@pytest.fixture(scope="session")
def sponsor(project, owner):
    return Accessory(owner.deploy(project.Sponsor))


@pytest.fixture(scope="module")
def flashloan(project, owner):
    return Accessory(owner.deploy(project.Flashloan))


@pytest.fixture(scope="module")
def flashlend(project, owner):
    return Accessory(owner.deploy(project.Flashlend))


@pytest.fixture(scope="session")
def dummy(compilers, owner):
    SRC = """# pragma version 0.4.1
last_call: public(Bytes[2048])

@external
@payable
def __default__():
    self.last_call = slice(msg.data, 0, 2048)
    """
    container = compilers.compile_source("vyper", SRC, contractName="Dummy")
    return Accessory(container.deploy(sender=owner))
