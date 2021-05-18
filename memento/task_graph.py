from typing import Dict, List


class Node:
    def __init__(self, identifier: str, dependencies: List[str]):
        self._identifier = identifier
        self._dependencies: List[str] = dependencies

    @property
    def identifier(self):
        return self._identifier
    
    @property
    def dependencies(self):
        return self._dependencies


class TaskGraph:
    def __init__(self):
        self._nodes: Dict[str, Node] = {}

    def add_node(self, node: Node):
        self._nodes[node.identifier] = node

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError(f"'key' must be an instance of 'str' but was '{type(key)}'")

        if not isinstance(value, Node):
            raise TypeError(f"'value' must be an instance of 'Node' but was '{type(key)}'")

        self._nodes[key] = value

    def __getitem__(self, item):
        return self._nodes[item]


"""

{
    id: 1,
    params: {
        foo: [a, b, c]
    }
}
=> outputs are 1, 2, 3

{
    dependencies: [1],
    params: {
        boo: [d, e, f]
    }
}

translates into:

{
    params: {
        1: [1, 2, 3],
        boo: [d, e, f]        
    }
}

"""



