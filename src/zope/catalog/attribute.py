#############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Index interface-defined attributes
"""
__docformat__ = 'restructuredtext'

import zope.interface
from zope.catalog.interfaces import IAttributeIndex

@zope.interface.implementer(IAttributeIndex)
class AttributeIndex(object):
    """Index interface-defined attributes

       Mixin for indexing a particular attribute of an object after
       first adapting the object to be indexed to an interface.

       The class is meant to be mixed with a base class that defines an
       index_doc method:

         >>> class BaseIndex(object):
         ...     def __init__(self):
         ...         self.data = []
         ...     def index_doc(self, id, value):
         ...         self.data.append((id, value))

       The class does two things. The first is to get a named field
       from an object:

         >>> class Data:
         ...     def __init__(self, v):
         ...         self.x = v

         >>> class Index(AttributeIndex, BaseIndex):
         ...     pass

         >>> index = Index('x')
         >>> index.index_doc(11, Data(1))
         >>> index.index_doc(22, Data(2))
         >>> index.data
         [(11, 1), (22, 2)]

       A method can be indexed:

         >>> Data.z = lambda self: self.x + 20
         >>> index = Index('z', field_callable=True)
         >>> index.index_doc(11, Data(1))
         >>> index.index_doc(22, Data(2))
         >>> index.data
         [(11, 21), (22, 22)]

       But you'll get an error if you try to index a method without
       setting field_callable:

         >>> index = Index('z')
         >>> index.index_doc(11, Data(1))

       The class can also adapt an object to an interface:

         >>> from zope.interface import Interface
         >>> class I(Interface):
         ...     pass

         >>> class Data:
         ...     def __init__(self, v):
         ...         self.x = v
         ...     def __conform__(self, iface):
         ...         if iface is I:
         ...             return Data2(self.x)

         >>> class Data2:
         ...     def __init__(self, v):
         ...         self.y = v*v

         >>> index = Index('y', I)
         >>> index.index_doc(11, Data(3))
         >>> index.index_doc(22, Data(2))
         >>> index.data
         [(11, 9), (22, 4)]

       When you define an index class, you can define a default
       interface and/or a default interface:

         >>> class Index(AttributeIndex, BaseIndex):
         ...     default_interface = I
         ...     default_field_name = 'y'

         >>> index = Index()
         >>> index.index_doc(11, Data(3))
         >>> index.index_doc(22, Data(2))
         >>> index.data
         [(11, 9), (22, 4)]

       """

    default_field_name = None
    default_interface = None

    def __init__(self, field_name=None, interface=None, field_callable=False,
                 *args, **kwargs):
        super(AttributeIndex, self).__init__(*args, **kwargs)
        if field_name is None and self.default_field_name is None:
            raise ValueError("Must pass a field_name")
        if field_name is None:
            self.field_name = self.default_field_name
        else:
            self.field_name = field_name
        if interface is None:
            self.interface = self.default_interface
        else:
            self.interface = interface
        self.field_callable = field_callable

    def index_doc(self, docid, object):
        if self.interface is not None:
            object = self.interface(object, None)
            if object is None:
                return None

        value = getattr(object, self.field_name, None)

        if value is not None and self.field_callable:
            #do not eat the exception raised below
            value = value()

        if value is None:
            #unindex the previous value!
            super(AttributeIndex, self).unindex_doc(docid)
            return None

        return super(AttributeIndex, self).index_doc(docid, value)
