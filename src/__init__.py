"""Auxiliar module to run Poetry commands."""
from .stickerimport import app as stickerimport_app
from .pack import app as pack_app


def import_pack():
    """Run sticker-import"""
    stickerimport_app()

def add_pack():
    """Run sticker-pack"""
    pack_app()
