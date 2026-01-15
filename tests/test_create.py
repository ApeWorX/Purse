import pytest
from ape.utils import ZERO_ADDRESS

from purse import Purse


@pytest.fixture()
def purse(singleton, owner, create2_deployer):
    return Purse.initialize(owner, create2_deployer, singleton=singleton)


@pytest.fixture(scope="module")
def container(project):
    return project.Multicall  # NOTE: Just random choice


@pytest.fixture(scope="module")
def blueprint(container, owner):
    return owner.declare(container).contract_address


@pytest.mark.parametrize("salt", [b"", b"Custom Salt"])
def test_create_blueprint(purse, blueprint, salt):
    if len(salt) < 32:
        salt = salt + b"\x00" * (32 - len(salt))

    tx = purse.create(b"", blueprint, salt, sender=purse.wallet)

    assert tx.events == [
        purse.DeploymentFromBlueprint(blueprint=blueprint, salt=salt, args=b""),
    ]


@pytest.mark.parametrize("salt", [b"", b"Custom Salt"])
def test_raw_create(purse, container, salt):
    if len(salt) < 32:
        salt = salt + b"\x00" * (32 - len(salt))

    initcode = container.contract_type.get_deployment_bytecode()

    tx = purse.create(initcode, ZERO_ADDRESS, salt, sender=purse.wallet)

    assert tx.events == [
        purse.Deployment(salt=salt, initcode=initcode),
    ]
