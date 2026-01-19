# pragma version 0.4.3

# NOTE: Maximum possible `raw_create` initcode size
MAX_CODE_SIZE: constant(uint16) = 41592

event Deployment:
    deployment: indexed(address)
    salt: indexed(bytes32)
    initcode: Bytes[MAX_CODE_SIZE]

event DeploymentFromBlueprint:
    deployment: indexed(address)
    blueprint: indexed(address)
    salt: indexed(bytes32)
    args: Bytes[MAX_CODE_SIZE]


@external
def create(
    initcode_or_args: Bytes[MAX_CODE_SIZE] = b"",
    blueprint: address = empty(address),
    salt: bytes32 = empty(bytes32),
    forwarded_value: uint256 = 0,
) -> address:
    deployment: address = empty(address)

    if blueprint != empty(address):
        if salt != empty(bytes32):
            deployment = create_from_blueprint(
                blueprint,
                initcode_or_args,
                raw_args=True,
                value=forwarded_value,
                salt=salt,
            )

        else:
            deployment = create_from_blueprint(
                blueprint,
                initcode_or_args,
                raw_args=True,
                value=forwarded_value,
            )

        log DeploymentFromBlueprint(
            deployment=deployment,
            blueprint=blueprint,
            salt=salt,
            args=initcode_or_args,
        )

    else:
        if salt != empty(bytes32):
            deployment = raw_create(
                initcode_or_args,
                value=forwarded_value,
                salt=salt,
            )
        else:
            deployment = raw_create(
                initcode_or_args,
                value=forwarded_value,
            )

        log Deployment(
            deployment=deployment,
            salt=salt,
            initcode=initcode_or_args,
        )

    assert deployment != empty(address), "Create:!deployment"
    return deployment
