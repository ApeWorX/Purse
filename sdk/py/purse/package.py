from importlib import resources

from ape.types import AddressType
from ethpm_types import PackageManifest

MANIFEST = PackageManifest.model_validate_json(
    resources.files(__package__).joinpath("manifest.json").read_text()
)

# codehash of Purse version => Purse singleton deployment address
DEPLOYMENTS: dict[str, AddressType] = {
    "c614b11e5f5e7d2201f54b65f0aae877b2d6c952f2e80b89cdd3fe23a0ea53ee": (
        "0xD2c583A9001e0d94536c6f57cA34fe975F318848"
    ),
    "cd1b5f99b57e7ba51f7df5ff3734747d821897bc0b21e5c6e6739ab7cabf3a1a": (
        "0x2C04E8A873849DdaD69D3892a9B850A492877782"
    ),
    # NOTE: Last item in dict is "latest" (add future versions below)
}

# Accessory name => Purse delegate address => Accessory deployment address
ACCESSORIES: dict[AddressType, dict[str, list[AddressType]]] = {
    "0xD2c583A9001e0d94536c6f57cA34fe975F318848": {
        "Multicall": [
            "0x0084b926D31e0E7FAD77a9f7E07eBa57015bcac8",
        ]
    },
    "0x2C04E8A873849DdaD69D3892a9B850A492877782": {
        "Create": [
            # NOTE: Last item in list is "latest" (add future versions below)
            "0x780c840277E8B8cf62a7aE3aF4Dd5b9467ADC649",
        ],
        "Flashloan": [
            # NOTE: Last item in list is "latest" (add future versions below)
            "0x3DfcDeF53aa20914a636B81eF29410b79f728E0e",
        ],
        "Multicall": [
            # NOTE: Last item in list is "latest" (add future versions below)
            "0x9FF116bCc5AEdaa4fC7b81b9a476Bc351A260CcE",
        ],
        "Sponsor": [
            # NOTE: Last item in list is "latest" (add future versions below)
            "0x0Fc81C99adc9F052E079e9f05542Ca40366703e9",
        ],
    },
}
