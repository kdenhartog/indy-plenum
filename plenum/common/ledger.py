from copy import copy
from typing import List, Tuple

import base58

from ledger.stores.chunked_file_store import ChunkedFileStore
from ledger.stores.file_store import FileStore

from ledger.ledger import Ledger as _Ledger
from stp_core.common.log import getlogger


logger = getlogger()


class Ledger(_Ledger):
    @staticmethod
    def _defaultStore(dataDir,
                      logName,
                      ensureDurability,
                      defaultFile=None) -> FileStore:
        return ChunkedFileStore(dataDir,
                                logName,
                                isLineNoKey=True,
                                storeContentHash=False,
                                ensureDurability=ensureDurability,
                                defaultFile=defaultFile)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Merkle tree of containing transactions that have not yet been
        # committed but optimistically applied.
        self.uncommittedTxns = []
        self.uncommittedRootHash = None
        self.uncommittedTree = None

    @property
    def uncommitted_size(self) -> int:
        return self.size + len(self.uncommittedTxns)

    def appendTxns(self, txns: List):
        # These transactions are not yet committed so they do not go to
        # the ledger
        uncommittedSize = self.size + len(self.uncommittedTxns)
        self.uncommittedTree = self.treeWithAppliedTxns(txns,
                                                        self.uncommittedTree)
        self.uncommittedRootHash = self.uncommittedTree.root_hash
        self.uncommittedTxns.extend(txns)
        if txns:
            return (uncommittedSize+1, uncommittedSize+len(txns)), txns
        else:
            return (uncommittedSize, uncommittedSize), txns

    def commitTxns(self, count: int) -> Tuple[Tuple[int, int], List]:
        """
        The number of txns from the beginning of `uncommittedTxns` to commit
        :param count:
        :return: a tuple of 2 seqNos indicating the start and end of sequence
        numbers of the committed txns
        """
        committedSize = self.size
        committedTxns = []
        for txn in self.uncommittedTxns[:count]:
            txn.update(self.append(txn))
            committedTxns.append(txn)
        self.uncommittedTxns = self.uncommittedTxns[count:]
        if not self.uncommittedTxns:
            self.uncommittedTree = None
            self.uncommittedRootHash = None
        # Do not change `uncommittedTree` or `uncommittedRootHash`
        # if there are any `uncommittedTxns` since the ledger still has a
        # valid uncommittedTree and a valid root hash which are
        # different from the committed ones
        return (committedSize + 1, committedSize + count), committedTxns

    def appendCommittedTxns(self, txns: List):
        # Called while receiving committed txns from other nodes
        for txn in txns:
            self.append(txn)

    def discardTxns(self, count: int):
        """
        The number of txns in `uncommittedTxns` which have to be
        discarded
        :param count:
        :return:
        """
        old_hash = self.uncommittedRootHash
        self.uncommittedTxns = self.uncommittedTxns[:-count]
        if not self.uncommittedTxns:
            self.uncommittedTree = None
            self.uncommittedRootHash = None
        else:
            self.uncommittedTree = self.treeWithAppliedTxns(self.uncommittedTxns)
            self.uncommittedRootHash = self.uncommittedTree.root_hash
        logger.debug('Discarding {} txns and root hash {} and new root hash '
                     'is {}'.format(count, old_hash, self.uncommittedRootHash))

    def treeWithAppliedTxns(self, txns: List, currentTree=None):
        """
        Return a copy of merkle tree after applying the txns
        :param txns:
        :return:
        """
        currentTree = currentTree or self.tree
        # Copying the tree is not a problem since its a Compact Merkle Tree
        # so the size of the tree would be 32*(lg n) bytes where n is the
        # number of leaves (no. of txns)
        tempTree = copy(currentTree)
        for txn in txns:
            tempTree.append(self.serializeLeaf(txn))
        return tempTree

    def reset_uncommitted(self):
        self.uncommittedTxns = []
        self.uncommittedRootHash = None
        self.uncommittedTree = None

    @staticmethod
    def hashToStr(h):
        return base58.b58encode(h)

    @staticmethod
    def strToHash(s):
        return base58.b58decode(s)
