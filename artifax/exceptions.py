class CircularDependencyError(Exception):
    """ Exception to be thrown when artifacts can not be built due to the fact
    that there is at least one closed loop in its graph representation which
    means we can not determine an evaluation order for the artifact nodes"""


class UnresolvedDependencyError(Exception):
    """ This exception is thrown when not all of a node's depencies can be found
    in the artifax graph. If you do want any of your nodes to resolve to a partial
    function, you need to set the allow_partial_functions flag in the build
    method/function to True."""


class InvalidSolverError(Exception):
    """ Thrown when requested solver is not available. """
