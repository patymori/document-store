import unittest
from unittest.mock import Mock

from documentstore import adapters, domain, exceptions


class DocumentsBundleStoreTest(unittest.TestCase):
    def setUp(self):
        self.DBCollectionMock = Mock()
        self.DBCollectionMock.insert_one = Mock()
        self.DBCollectionMock.find_one = Mock()

    def test_add(self):
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        bundles.add(bundle)
        expected = bundle.manifest
        expected["_id"] = "0034-8910-rsp-48-2"
        self.DBCollectionMock.insert_one.assert_called_once_with(expected)

    def test_add_bundle_with_divergent_ids(self):
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundle = domain.DocumentsBundle(
            manifest={"_id": "1", "id": "0034-8910-rsp-48-2"}
        )
        bundles.add(bundle)
        expected = bundle.manifest
        self.DBCollectionMock.insert_one.assert_called_once_with(expected)

    def test_add_raises_exception_if_already_exists(self):
        import pymongo

        self.DBCollectionMock.insert_one.side_effect = pymongo.errors.DuplicateKeyError(
            ""
        )
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertRaises(exceptions.AlreadyExists, bundles.add, bundle)

    def test_fetch_raises_exception_if_does_not_exist(self):
        self.DBCollectionMock.find_one.return_value = None
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        self.assertRaises(exceptions.DoesNotExist, bundles.fetch, "0034-8910-rsp-48-2")

    def test_fetch(self):
        self.DBCollectionMock.find_one.return_value = {"_id": "0034-8910-rsp-48-2"}
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundles.fetch("0034-8910-rsp-48-2")
        self.DBCollectionMock.find_one.assert_called_once_with(
            {"_id": "0034-8910-rsp-48-2"}
        )

    def test_fetch_returns_documents_bundle(self):
        manifest = {"_id": "0034-8910-rsp-48-2", "id": "0034-8910-rsp-48-2"}
        self.DBCollectionMock.find_one.return_value = manifest
        bundles = adapters.DocumentsBundleStore(self.DBCollectionMock)
        bundle = bundles.fetch("0034-8910-rsp-48-2")
        # XXX: Teste incompleto, pois não testa o retorno de forma precisa
        self.assertEqual(bundle.id(), "0034-8910-rsp-48-2")
        self.assertEqual(bundle.manifest, manifest)
