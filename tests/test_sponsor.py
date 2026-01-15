import pytest

from purse import Purse


@pytest.fixture()
def purse(singleton, owner, sponsor):
    return Purse.initialize(owner, sponsor, singleton=singleton)


def test_sponsor_plain_eth_transfer(purse, dummy, owner):
    # Generate random ETH amount > 0 (fuzz with hypothesis)
    # Call sponsor with no data and value > 0
    # Verify dummy received and processed ETH
    pass


def test_sponsor_eth_attached_to_call(purse, dummy, owner):
    # Fuzz random bytes data with hypothesis and random eth value
    # Sponsor a call with calldata and value
    # Check dummy recorded the data hash
    pass


def test_sponsor_target_is_purse_self(purse, owner):
    # Send a call to self with ETH, triggering __default__ (reentrant)
    # Expect successful processing (no revert, maybe check call depth if possible)
    pass


def test_sponsor_reverts_if_signature_expired(purse, owner):
    # Construct an expired signature using a timestamp in the past
    # Use ape reverts to check the Sponsor:!expired-signature error is bubbled up
    pass


def test_sponsor_reverts_if_nonce_used_is_incorrect(purse, owner):
    # Fetch the correct nonce
    # Loop and use wrong nonce (off-by-one)
    # Use ape reverts, check Sponsor:!unauthorized-signer erro
    pass


def test_sponsor_reverts_signer_is_unauthorized(purse, other):
    # Mallory signs instead of the owner
    # Use ape reverts, check Sponsor:!unauthorized-signer erro
    pass
