import pytest
from magma import clear_cachedFunctions
import magma.backend.coreir_


@pytest.fixture(autouse=True)
def magma_test():
    import magma.config
    clear_cachedFunctions()
    magma.backend.coreir_.__reset_context()
