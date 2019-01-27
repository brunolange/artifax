class CircularDependencyError(Exception):
    """ Exception to be thrown when artifacts can not be built due to the fact
    that there is at least one closed loop in its graph representation which
    means we can not determine an evaluation order for the artifact nodes"""
    pass
