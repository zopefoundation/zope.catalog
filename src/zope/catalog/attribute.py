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
       ``index_doc`` method and an ``unindex_doc`` method:

         >>> class BaseIndex(object):
         ...     def __init__(self):
         ...         self.data = []
         ...     def index_doc(self, id, value):
         ...         self.data.append((id, value))
         ...     def unindex_doc(self, id):
         ...         for n, (iid, _) in enumerate(self.data):
         ...             if id == iid:
         ...                 del self.data[n]
         ...                 break

       The class does two things. The first is to get a named field
       from an object:

         >>> class Data(object):
         ...     def __init__(self, v):
         ...         self.x = v

         >>> from zope.catalog.attribute import AttributeIndex
         >>> class Index(AttributeIndex, BaseIndex):
         ...     pass

         >>> index = Index('x')
         >>> index.index_doc(11, Data(1))
         >>> index.index_doc(22, Data(2))
         >>> index.data
         [(11, 1), (22, 2)]

       If the field value is ``None``, indexing it removes it from the
       index:

         >>> index.index_doc(11, Data(None))
         >>> index.data
         [(22, 2)]

       If the field names a method (any callable object), the results
       of calling that field can be indexed:

         >>> def z(self): return self.x + 20
         >>> Data.z = z
         >>> index = Index('z', field_callable=True)
         >>> index.index_doc(11, Data(1))
         >>> index.index_doc(22, Data(2))
         >>> index.data
         [(11, 21), (22, 22)]

       Of course, if you neglect to set ``field_callable`` when you
       index a method, it's likely that most concrete index implementations
       will raise an exception, but this class will happily pass that callable
       on:

         >>> index = Index('z')
         >>> data = Data(1)
         >>> index.index_doc(11, data)
         >>> index.data
         [(11, <bound method ...>>)]


       The class can also adapt an object to an interface before getting the
       field:

         >>> from zope.interface import Interface
         >>> class I(Interface):
         ...     pass

         >>> class Data(object):
         ...     def __init__(self, v):
         ...         self.x = v
         ...     def __conform__(self, iface):
         ...         if iface is I:
         ...             return Data2(self.x)

         >>> class Data2(object):
         ...     def __init__(self, v):
         ...         self.y = v * v

         >>> index = Index('y', I)
         >>> index.index_doc(11, Data(3))
         >>> index.index_doc(22, Data(2))
         >>> index.data
         [(11, 9), (22, 4)]

       If adapting to the interface fails, the object is not indexed:

         >>> class I2(Interface): pass
         >>> I2(Data(3), None) is None
         True
         >>> index = Index('y', I2)
         >>> index.index_doc(11, Data(3))
         >>> index.data
         []

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

    #: Subclasses can set this to a string if they want to allow
    #: construction without passing the ``field_name``.
    default_field_name = None
    #: Subclasses can set this to an interface (a callable taking
    #: the object do index and the default value to return)
    #: if they want to allow construction that doesn't provide an
    #: ``interface``.
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
        """
        Derives the value to index for *object*.

        Uses the interface passed to the constructor to adapt the
        object, and then gets the field (calling it if
        ``field_callable`` was set). If the value thus found is ``None``,
        calls ``unindex_doc``. Otherwise, passes the *docid* and the value to
        the superclass's implementation of ``index_doc``.
        """
        if self.interface is not None:
            object = self.interface(object, None)
            if object is None:
                return None

        value = getattr(object, self.field_name, None)

        if value is not None and self.field_callable:
            # do not eat the exception raised below
            value = value()

        if value is None:
            # unindex the previous value!
            super(AttributeIndex, self).unindex_doc(docid)
            return None

        return super(AttributeIndex, self).index_doc(docid, value)
