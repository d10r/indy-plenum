import base58
import pytest
from plenum.bls.bls_key_register_pool_manager import BlsKeyRegisterPoolManager
from plenum.common.constants import NODE, TXN_TYPE, BLS_KEY, DATA
from plenum.common.util import randomString
from plenum.test.bls.helper import sdk_change_bls_key

nodeCount = 4


@pytest.fixture()
def node(txnPoolNodeSet):
    return txnPoolNodeSet[0]


@pytest.fixture()
def pool_node_txns(poolTxnData):
    node_txns = []
    for txn in poolTxnData["txns"]:
        if txn[TXN_TYPE] == NODE:
            node_txns.append(txn)
    return node_txns


@pytest.fixture()
def bls_key_register_ledger(node):
    return BlsKeyRegisterPoolManager(node.poolManager)


def test_current_committed_root(bls_key_register_ledger, node):
    committed_root = bls_key_register_ledger.get_pool_root_hash_committed()
    assert committed_root
    assert committed_root == node.poolManager.state.committedHeadHash


def test_get_key_for_current_root(bls_key_register_ledger, txnPoolNodeSet, pool_node_txns):
    for i in range(nodeCount):
        bls_key = bls_key_register_ledger.get_key_by_name(
            txnPoolNodeSet[i].name)
        assert bls_key
        assert bls_key == pool_node_txns[i][DATA][BLS_KEY]


def test_get_key_for_current_root_explicitly(bls_key_register_ledger, txnPoolNodeSet, pool_node_txns):
    for i in range(nodeCount):
        bls_key = bls_key_register_ledger.get_key_by_name(txnPoolNodeSet[i].name,
                                                          bls_key_register_ledger.get_pool_root_hash_committed())
        assert bls_key
        assert bls_key == pool_node_txns[i][DATA][BLS_KEY]


def test_get_key_for_old_root_keys_changed(bls_key_register_ledger,
                                           pool_node_txns,
                                           txnPoolNodeSet,
                                           node,
                                           looper,
                                           sdk_wallet_steward,
                                           sdk_pool_handle):
    old_bls_key = pool_node_txns[0][DATA][BLS_KEY]
    new_bls_key = base58.b58encode(randomString(128).encode()).decode("utf-8")
    old_pool_root_hash = node.poolManager.state.committedHeadHash

    # change BLS keys

    sdk_change_bls_key(looper, txnPoolNodeSet,
                       node,
                       sdk_pool_handle,
                       sdk_wallet_steward,
                       add_wrong=False,
                       new_bls=new_bls_key)

    new_pool_root_hash = node.poolManager.state.committedHeadHash
    assert old_pool_root_hash != new_pool_root_hash

    # get old and new keys
    bls_key = bls_key_register_ledger.get_key_by_name(node.name,
                                                      old_pool_root_hash)
    assert bls_key
    assert bls_key == old_bls_key

    bls_key = bls_key_register_ledger.get_key_by_name(node.name,
                                                      new_pool_root_hash)
    assert bls_key
    assert bls_key == new_bls_key
