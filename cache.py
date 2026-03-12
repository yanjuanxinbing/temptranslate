class LRU:
    __slots__ = ('capacity', 'cache', 'head', 'tail', 'size')

    class Node:
        __slots__ = ('key', 'value', 'prev', 'next')

        def __init__(self, key=None, value=None):
            self.key = key
            self.value = value
            self.prev = None
            self.next = None

    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self.cache = {}
        self.head = self.Node()
        self.tail = self.Node()
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    def _add_to_head(self, node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _move_to_head(self, node):
        self._remove_node(node)
        self._add_to_head(node)

    def get(self, key) -> str | None:
        node = self.cache.get(key)

        if not node:
            return None

        self._move_to_head(node)
        return node.value

    def put(self, key, value):
        node = self.Node(key, value)
        self.cache[key] = node
        self._add_to_head(node)
        self.size += 1

        if self.size > self.capacity:
            node = self.tail.prev
            self._remove_node(node)
            del self.cache[node.key]
            self.size -= 1