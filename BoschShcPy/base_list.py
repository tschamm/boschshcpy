# Copyright(c) 2014, MessageBird
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES
#  LOSS OF USE, DATA, OR PROFITS
#  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Code mostly taken from messagebird API, see LICENCE

from BoschShcPy.base import Base


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
