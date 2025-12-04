import pytest
from ape.utils import ZERO_ADDRESS


@pytest.fixture()
def purse(singleton, owner, create2_deployer, encode_accessory_data):
    with owner.delegate_to(
        singleton,
        # NOTE: Add multicall as an accessory at the same time
        data=singleton.update_accessories.encode_input(
            encode_accessory_data(
                create2_deployer.create,
            )
        ),
    ) as purse:
        # NOTE: So we can decode logs
        purse.contract_type.abi.extend(create2_deployer.contract_type.abi)
        yield purse


@pytest.fixture(scope="module")
def container(project):
    return project.Multicall  # NOTE: Just random choice


@pytest.fixture(scope="module")
def blueprint(container, owner):
    return owner.declare(container).contract_address


@pytest.mark.parametrize("salt", [b"", b"Custom Salt"])
def test_create_blueprint(purse, create2_deployer, blueprint, salt):
    if len(salt) < 32:
        salt = salt + b"\x00" * (32 - len(salt))

    tx = purse(
        data=create2_deployer.create.encode_input(b"", blueprint, salt),
        sender=purse,
    )
    assert tx.events == [
        purse.DeploymentFromBlueprint(blueprint=blueprint, salt=salt, args=b""),
    ]


@pytest.mark.parametrize("salt", [b"", b"Custom Salt"])
def test_raw_create(purse, create2_deployer, container, salt):
    if len(salt) < 32:
        salt = salt + b"\x00" * (32 - len(salt))

    initcode = container.contract_type.get_deployment_bytecode()

    tx = purse(
        data=create2_deployer.create.encode_input(initcode, ZERO_ADDRESS, salt),
        sender=purse,
    )
    assert tx.events == [
        purse.Deployment(salt=salt, initcode=initcode),
    ]
