from boschshc.base import Base


class Links(Base):

    def __init__(self):
        self.first = None
        self.previous = None
        self.next = None
        self.last = None


class BaseList(Base):

    def __init__(self, item_type):
        """When setting items, they are instantiated as objects of type item_type."""
        self.limit = None
        self.offset = None
        self.count = None
        self.totalCount = None
        self._items = None

        self.itemType = item_type

    def load(self, data):
#         print (self.itemType())
        items = []
        for dict_item in data:
            items.append(self.itemType().load(dict_item))
        self._items = items
        return self

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, value):
        """Create typed objects from the dicts."""
        items = []
        for item in value:
            items.append(self.itemType().load(item))

        self._items = items

    def __str__(self):
        items_count = 0 if self.items is None else len(self.items)
        return "%s with %d items.\n" % (str(self.__class__), items_count)
