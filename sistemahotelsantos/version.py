"""
Arquivo centralizado de versionamento
"""

__version__ = "5.0.2"
__version_info__ = (5, 0, 2)
__author__ = "Gabriel Ramos"
__license__ = "MIT"

def get_version():
    return __version__

def get_version_tuple():
    return __version_info__