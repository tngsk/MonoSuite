"""Explicit importer registry; no dynamic discovery or external plugins."""
from .mono_import import import_document
from .craft_import import import_bundle
from .deckset_import import import_document as import_deckset


def native_document(source, output):
    return source


IMPORTERS = {'space': native_document, 'mono': import_document, 'craft': import_bundle, 'deckset': import_deckset}
