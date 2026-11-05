class PhaseInWorldError(ValueError):
    pass

class TrueGrimLostError(AssertionError):
    pass

class FinalizeDidNotSettleError(Exception):
    """A bug in finalize, not an invalid world. It deliberately isn't a RuntimeError or
    ValueError, because branching treats those as "this world is impossible" and drops the world."""
    pass