"""Exceptions for the artifax package
"""

__author__ = "Bruno Lange"
__email__ = "blangeram@gmail.com"
__license__ = "MIT"


class CircularDependencyError(Exception):
    """Exception to be thrown when artifacts can not be built due to the fact
    that there is at least one closed loop in its graph representation which
    means we can not determine an evaluation order for the artifact nodes"""


class UnresolvedDependencyError(Exception):
    """This exception is thrown when not all of a node's dependencies can be found
    in the artifax graph. If you do want any of your nodes to resolve to a partial
    function, you need to set the allow_partial_functions flag in the build
    method/function to True."""

    def __init__(self, message=None, nodes=None):
        super().__init__(message)
        self.nodes = nodes

    def __str__(self):
        if not self.nodes:
            return super().__str__()
        return "Missing dependencies: {}".format(self.nodes)


class InvalidSolverError(Exception):
    """Thrown when requested solver is not available."""
