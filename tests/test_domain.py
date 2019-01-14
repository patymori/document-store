import unittest
import functools
from copy import deepcopy

from documentstore import domain, exceptions

SAMPLE_MANIFEST = {
    "id": "0034-8910-rsp-48-2-0275",
    "versions": [
        {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": [
                    (
                        "2018-08-05T23:03:44.971230Z",
                        "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                    ),
                    (
                        "2018-08-05T23:08:41.590174Z",
                        "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                    ),
                ]
            },
            "timestamp": "2018-08-05T23:02:29.392990Z",
        },
        {
            "data": "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": [
                    (
                        "2018-08-05T23:30:29.392995Z",
                        "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                    )
                ]
            },
            "timestamp": "2018-08-05T23:30:29.392990Z",
        },
    ],
}


def fake_utcnow():
    return "2018-08-05T22:33:49.795151Z"


class UnittestMixin:
    def _assert_raises_with_message(self, type, message, func, *args):
        try:
            func(*args)
        except type as exc:
            self.assertEqual(str(exc), message)
        else:
            self.assertTrue(False)


new_bundle = functools.partial(domain.BundleManifest.new, now=fake_utcnow)


class DocumentTests(unittest.TestCase):
    def make_one(self):
        _manifest = deepcopy(SAMPLE_MANIFEST)
        return domain.Document(manifest=_manifest)

    def test_manifest_is_generated_on_init(self):
        document = domain.Document(doc_id="0034-8910-rsp-48-2-0275")
        self.assertTrue(isinstance(document.manifest, dict))

    def test_manifest_as_arg_on_init(self):
        existing_manifest = {"id": "0034-8910-rsp-48-2-0275", "versions": []}
        document = domain.Document(manifest=existing_manifest)
        self.assertEqual(existing_manifest, document.manifest)

    def test_manifest_with_unknown_schema_is_allowed(self):
        existing_manifest = {"versions": []}
        document = domain.Document(manifest=existing_manifest)
        self.assertEqual(existing_manifest, document.manifest)

    def test_missing_doc_id_return_empty_string(self):
        existing_manifest = {"versions": []}
        document = domain.Document(manifest=existing_manifest)
        self.assertEqual(document.doc_id(), "")

    def test_doc_id(self):
        document = domain.Document(doc_id="0034-8910-rsp-48-2-0275")
        self.assertEqual(document.doc_id(), "0034-8910-rsp-48-2-0275")

    def test_new_version_of_data(self):
        document = self.make_one()
        self.assertEqual(len(document.manifest["versions"]), 2)

        document.new_version(
            "/rawfiles/5e3ad9c6cd6b8/0034-8910-rsp-48-2-0275.xml",
            assets_getter=lambda data_url, timeout: (None, []),
        )
        self.assertEqual(len(document.manifest["versions"]), 3)

    def test_get_latest_version(self):
        document = self.make_one()
        latest = document.version()
        self.assertEqual(
            latest["data"], "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml"
        )

    def test_get_latest_version_when_there_isnt_any(self):
        document = domain.Document(doc_id="0034-8910-rsp-48-2-0275")
        self.assertRaises(ValueError, lambda: document.version())

    def test_get_oldest_version(self):
        document = self.make_one()
        oldest = document.version(0)
        self.assertEqual(
            oldest["data"], "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml"
        )

    def test_version_only_shows_newest_assets(self):
        document = self.make_one()
        oldest = document.version(0)
        expected = {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif"
            },
            "timestamp": "2018-08-05T23:02:29.392990Z",
        }
        self.assertEqual(oldest, expected)

    def test_new_version_automaticaly_references_latest_known_assets(self):
        manifest = {
            "id": "0034-8910-rsp-48-2-0275",
            "versions": [
                {
                    "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
                    "assets": {
                        "0034-8910-rsp-48-2-0275-gf01.gif": [
                            (
                                "2018-08-05T23:03:44.971230Z",
                                "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif",
                            ),
                            (
                                "2018-08-05T23:03:49.971250Z",
                                "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
                            ),
                        ]
                    },
                }
            ],
        }

        document = domain.Document(manifest=manifest)
        document.new_version(
            "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml",
            assets_getter=lambda data_url, timeout: (
                None,
                [("0034-8910-rsp-48-2-0275-gf01.gif", None)],
            ),
        )
        latest = document.version()
        self.assertEqual(
            latest["assets"]["0034-8910-rsp-48-2-0275-gf01.gif"],
            "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif",
        )

    def test_version_at_later_time(self):
        """
        No manifesto `SAMPLE_MANIFEST`, a versão mais recente possui foi
        produzida nos seguintes instantes: a) dados em 2018-08-05 23:30:29.392990
        e b) ativo digital em 2018-08-05 23:30:29.392995.
        """
        document = self.make_one()
        target = document.version_at("2018-12-31")
        expected = {
            "data": "/rawfiles/2d3ad9c6bc656/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": "/rawfiles/bf139b9aa3066/0034-8910-rsp-48-2-0275-gf01.gif"
            },
            "timestamp": "2018-08-05T23:30:29.392990Z",
        }
        self.assertEqual(target, expected)

    def test_version_at_given_time(self):
        document = self.make_one()
        target = document.version_at("2018-08-05T23:04:00Z")
        expected = {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {
                "0034-8910-rsp-48-2-0275-gf01.gif": "/rawfiles/8e644999a8fa4/0034-8910-rsp-48-2-0275-gf01.gif"
            },
            "timestamp": "2018-08-05T23:02:29.392990Z",
        }
        self.assertEqual(target, expected)

    def test_version_at_time_between_data_and_asset_registration(self):
        document = self.make_one()
        target = document.version_at("2018-08-05T23:03:43Z")
        expected = {
            "data": "/rawfiles/7ca9f9b2687cb/0034-8910-rsp-48-2-0275.xml",
            "assets": {"0034-8910-rsp-48-2-0275-gf01.gif": ""},
            "timestamp": "2018-08-05T23:02:29.392990Z",
        }
        self.assertEqual(target, expected)

    def test_version_at_time_prior_to_data_registration(self):
        document = self.make_one()
        self.assertRaises(ValueError, lambda: document.version_at("2018-07-01"))

    def test_version_at_non_UCT_time_raises_exception(self):
        document = self.make_one()
        self.assertRaises(
            ValueError, lambda: document.version_at("2018-08-05 23:03:44")
        )


class BundleManifestTest(UnittestMixin, unittest.TestCase):
    def test_new(self):
        fake_date = fake_utcnow()
        expected = {
            "id": "0034-8910-rsp-48-2",
            "created": fake_date,
            "updated": fake_date,
            "items": [],
            "metadata": {},
        }
        self.assertEqual(new_bundle("0034-8910-rsp-48-2"), expected)

    def test_new_set_same_value_to_created_updated(self):
        documents_bundle = domain.BundleManifest.new("0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle["created"], documents_bundle["updated"])

    def test_set_metadata(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "publication_year", "2018"
        )
        self.assertEqual(documents_bundle["metadata"]["publication_year"], "2018")
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_set_metadata_overwrites_existing_value(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "publication_year", "2018"
        )
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "publication_year", "2019"
        )
        self.assertEqual(documents_bundle["metadata"]["publication_year"], "2019")
        self.assertEqual(len(documents_bundle["metadata"]), 1)

    def test_set_metadata_to_preexisting_set(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "publication_year", "2018"
        )
        documents_bundle = domain.BundleManifest.set_metadata(
            documents_bundle, "volume", "25"
        )
        self.assertEqual(documents_bundle["metadata"]["publication_year"], "2018")
        self.assertEqual(documents_bundle["metadata"]["volume"], "25")
        self.assertEqual(len(documents_bundle["metadata"]), 2)

    def test_add_item(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertEqual(
            documents_bundle["items"][-1], "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_add_item_raises_exception_if_item_already_exists(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0275"
        )
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            "cannot add documents bundle item "
            '"/documents/0034-8910-rsp-48-2-0275": the item already exists',
            domain.BundleManifest.add_item,
            documents_bundle,
            "/documents/0034-8910-rsp-48-2-0275",
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))

    def test_insert_item(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0775"
        )
        documents_bundle = domain.BundleManifest.insert_item(
            documents_bundle, 0, "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertEqual(
            documents_bundle["items"][0], "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertEqual(
            documents_bundle["items"][1], "/documents/0034-8910-rsp-48-2-0775"
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_insert_item_raises_exception_if_item_already_exists(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0775"
        )
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            "cannot insert documents bundle item "
            '"/documents/0034-8910-rsp-48-2-0775": the item already exists',
            domain.BundleManifest.insert_item,
            documents_bundle,
            0,
            "/documents/0034-8910-rsp-48-2-0775",
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))

    def test_insert_item_follows_python_semantics(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0475"
        )
        documents_bundle = domain.BundleManifest.insert_item(
            documents_bundle, -10, "/documents/0034-8910-rsp-48-2-0275"
        )
        self.assertEqual(
            documents_bundle["items"][0], "/documents/0034-8910-rsp-48-2-0275"
        )
        documents_bundle = domain.BundleManifest.insert_item(
            documents_bundle, 10, "/documents/0034-8910-rsp-48-2-0975"
        )
        self.assertEqual(
            documents_bundle["items"][-1], "/documents/0034-8910-rsp-48-2-0975"
        )

    def test_remove_item(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        documents_bundle = domain.BundleManifest.add_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0475"
        )
        documents_bundle = domain.BundleManifest.remove_item(
            documents_bundle, "/documents/0034-8910-rsp-48-2-0475"
        )
        self.assertNotIn(
            "/documents/0034-8910-rsp-48-2-0475", documents_bundle["items"]
        )
        self.assertTrue(current_updated < documents_bundle["updated"])

    def test_remove_item_raises_exception_if_item_does_not_exist(self):
        documents_bundle = new_bundle("0034-8910-rsp-48-2")
        current_updated = documents_bundle["updated"]
        current_item_len = len(documents_bundle["items"])
        self._assert_raises_with_message(
            exceptions.DoesNotExist,
            "cannot remove documents bundle item "
            '"/documents/0034-8910-rsp-48-2-0775": the item does not exist',
            domain.BundleManifest.remove_item,
            documents_bundle,
            "/documents/0034-8910-rsp-48-2-0775",
        )
        self.assertEqual(current_updated, documents_bundle["updated"])
        self.assertEqual(current_item_len, len(documents_bundle["items"]))


class DocumentsBundleTest(UnittestMixin, unittest.TestCase):
    def test_manifest_is_generated_on_init(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertTrue(isinstance(documents_bundle.manifest, dict))

    def test_manifest_as_arg_on_init(self):
        existing_manifest = new_bundle("0034-8910-rsp-48-2")
        documents_bundle = domain.DocumentsBundle(manifest=existing_manifest)
        self.assertEqual(existing_manifest, documents_bundle.manifest)

    def test_manifest_schema_is_not_validated_on_init(self):
        existing_manifest = {"versions": []}
        documents_bundle = domain.DocumentsBundle(manifest=existing_manifest)
        self.assertEqual(existing_manifest, documents_bundle.manifest)

    def test_id_returns_id(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.id(), "0034-8910-rsp-48-2")

    def test_publication_year_is_empty_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.publication_year, "")

    def test_set_publication_year(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.publication_year = "2018"
        self.assertEqual(documents_bundle.publication_year, "2018")
        self.assertEqual(
            documents_bundle.manifest["metadata"]["publication_year"], "2018"
        )

    def test_set_publication_year_convert_to_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.publication_year = 2018
        self.assertEqual(documents_bundle.publication_year, "2018")

    def test_set_publication_year_validates_four_digits_year(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self._assert_raises_with_message(
            ValueError,
            "cannot set publication_year with value " '"18": the value is not valid',
            setattr,
            documents_bundle,
            "publication_year",
            18,
        )

    def test_volume_is_empty_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.volume, "")

    def test_set_volume(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.volume = "25"
        self.assertEqual(documents_bundle.volume, "25")
        self.assertEqual(documents_bundle.manifest["metadata"]["volume"], "25")

    def test_set_volume_convert_to_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.volume = 25
        self.assertEqual(documents_bundle.volume, "25")

    def test_set_volume_content_is_not_validated(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.volume = "25.A"
        self.assertEqual(documents_bundle.volume, "25.A")

    def test_number_is_empty_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.number, "")

    def test_set_number(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.number = "3"
        self.assertEqual(documents_bundle.number, "3")
        self.assertEqual(documents_bundle.manifest["metadata"]["number"], "3")

    def test_set_number_convert_to_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.number = 3
        self.assertEqual(documents_bundle.number, "3")

    def test_set_number_content_is_not_validated(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.number = "3.A"
        self.assertEqual(documents_bundle.number, "3.A")

    def test_supplement_is_empty_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.supplement, "")

    def test_set_supplement(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.supplement = "3"
        self.assertEqual(documents_bundle.supplement, "3")
        self.assertEqual(documents_bundle.manifest["metadata"]["supplement"], "3")

    def test_set_supplement_convert_to_str(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.supplement = 3
        self.assertEqual(documents_bundle.supplement, "3")

    def test_set_supplement_content_is_not_validated(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.supplement = "3.A"
        self.assertEqual(documents_bundle.supplement, "3.A")

    def test_sections_is_empty_list(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.sections, [])

    def test_add_section(self):
        section = {"en": "Articles", "pt": "Artigos"}
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_section(section)
        self.assertEqual(section, documents_bundle.manifest["metadata"]["sections"][-1])

    def test_add_section_raises_exception_if_section_already_exists(self):
        section = {"en": "Articles", "pt": "Artigos"}
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_section(section)
        message_error = f"cannot add section {section}: the section already exists."
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            message_error,
            documents_bundle.add_section,
            section,
        )

    def test_remove_section(self):
        sections = [
            {"en": "Articles", "pt": "Artigos"},
            {"en": "Review", "pt": "Resenha"},
            {"en": "Essay", "pt": "Ensaio"},
        ]
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        for section in sections:
            documents_bundle.add_section(section)
        removed_section = sections[1]
        documents_bundle.remove_section(removed_section)
        self.assertNotIn(removed_section, documents_bundle.sections)

    def test_remove_section_raises_exception_if_section_does_not_exist(self):
        sections = [
            {"en": "Articles", "pt": "Artigos"},
            {"en": "Review", "pt": "Resenha"},
        ]
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        for section in sections:
            documents_bundle.add_section(section)
        removed_section = {"en": "Essay", "pt": "Ensaio"}
        message_error = (
            f"cannot remove section {removed_section}: the section does not exists."
        )
        self._assert_raises_with_message(
            exceptions.DoesNotExist,
            message_error,
            documents_bundle.remove_section,
            removed_section,
        )

    def test_sections_returns_added_sections_list(self):
        sections = [
            {"en": "Articles", "pt": "Artigos"},
            {"en": "Review", "pt": "Resenha"},
            {"en": "Essay", "pt": "Ensaio"},
        ]
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        for section in sections:
            documents_bundle.add_section(section)
        self.assertEqual(documents_bundle.sections, sections)

    def test_add_document(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        self.assertIn(
            "/documents/0034-8910-rsp-48-2-0275", documents_bundle.manifest["items"]
        )

    def test_add_document_raises_exception_if_item_already_exists(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            "cannot add documents bundle item "
            '"/documents/0034-8910-rsp-48-2-0275": the item already exists',
            documents_bundle.add_document,
            "/documents/0034-8910-rsp-48-2-0275",
        )

    def test_documents_returns_empty_list(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        self.assertEqual(documents_bundle.documents, [])

    def test_documents_returns_added_documents_list(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0276")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0277")
        self.assertEqual(
            documents_bundle.documents,
            [
                "/documents/0034-8910-rsp-48-2-0275",
                "/documents/0034-8910-rsp-48-2-0276",
                "/documents/0034-8910-rsp-48-2-0277",
            ],
        )

    def test_remove_document(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0276")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0277")
        documents_bundle.remove_document("/documents/0034-8910-rsp-48-2-0275")
        self.assertNotIn(
            "/documents/0034-8910-rsp-48-2-0275", documents_bundle.manifest["items"]
        )
        self.assertEqual(2, len(documents_bundle.manifest["items"]))

    def test_remove_document_raises_exception_if_item_does_not_exist(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0276")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0277")
        self._assert_raises_with_message(
            exceptions.DoesNotExist,
            "cannot remove documents bundle item "
            '"/documents/0034-8910-rsp-48-2-0275": the item does not exist',
            documents_bundle.remove_document,
            "/documents/0034-8910-rsp-48-2-0275",
        )

    def test_insert_document(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0276")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0277")
        documents_bundle.insert_document(1, "/documents/0034-8910-rsp-48-2-0271")
        self.assertEqual(
            "/documents/0034-8910-rsp-48-2-0271", documents_bundle.manifest["items"][1]
        )
        self.assertEqual(4, len(documents_bundle.manifest["items"]))

    def test_insert_document_raises_exception_if_item_already_exists(self):
        documents_bundle = domain.DocumentsBundle(id="0034-8910-rsp-48-2")
        documents_bundle.add_document("/documents/0034-8910-rsp-48-2-0275")
        self._assert_raises_with_message(
            exceptions.AlreadyExists,
            "cannot insert documents bundle item "
            '"/documents/0034-8910-rsp-48-2-0275": the item already exists',
            documents_bundle.insert_document,
            1,
            "/documents/0034-8910-rsp-48-2-0275",
        )
