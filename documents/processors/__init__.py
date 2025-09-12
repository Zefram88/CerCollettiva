# documents/processors/__init__.py
from .gaudi import GaudiProcessor

__all__ = ["GaudiProcessor"]

PROCESSORS = {
    "GAUDI": GaudiProcessor,
    # Altri processori...
}


def get_processor(document_type):
    """Restituisce il processore appropriato per il tipo di documento"""
    return PROCESSORS.get(document_type)
