Automatic indexing with events
==============================

.. testsetup::

   from zope.catalog.tests import placefulSetUp
   root = placefulSetUp()

.. testcleanup::

   from zope.catalog.tests import placefulTearDown
   placefulTearDown()

In order to automatically keep the catalog up-to-date any objects that
are added to a intid utility are indexed automatically. Also when an
object gets modified it is reindexed by listening to IObjectModified
events.

Let us create a fake catalog to demonstrate this behaviour. We only
need to implement the index_doc method for this test.

.. doctest::

    >>> from zope.catalog.interfaces import ICatalog
    >>> from zope import interface, component
    >>> @interface.implementer(ICatalog)
    ... class FakeCatalog(object):
    ...     indexed = []
    ...     def index_doc(self, docid, obj):
    ...         self.indexed.append((docid, obj))
    >>> cat = FakeCatalog()
    >>> component.provideUtility(cat)

We also need an intid util and a keyreference adapter.

.. doctest::

    >>> from zope.intid import IntIds
    >>> from zope.intid.interfaces import IIntIds
    >>> intids = IntIds()
    >>> component.provideUtility(intids, IIntIds)
    >>> from zope.keyreference.testing import SimpleKeyReference
    >>> component.provideAdapter(SimpleKeyReference)

    >>> from  zope.container.contained import Contained
    >>> class Dummy(Contained):
    ...     def __init__(self, name):
    ...         self.__name__ = name
    ...     def __repr__(self):
    ...         return '<Dummy %r>' % str(self.__name__)

We have a subscriber to IIntidAddedEvent.

.. doctest::

    >>> from zope.catalog import catalog
    >>> from zope.intid.interfaces import IntIdAddedEvent
    >>> d1 = Dummy(u'one')
    >>> id1 = intids.register(d1)
    >>> catalog.indexDocSubscriber(IntIdAddedEvent(d1, None))

Now we have indexed the object.

.. doctest::

    >>> cat.indexed.pop()
    (..., <Dummy 'one'>)

When an object is modified an objectmodified event should be fired by
the application. Here is the handler for such an event.

.. doctest::

    >>> from zope.lifecycleevent import ObjectModifiedEvent
    >>> catalog.reindexDocSubscriber(ObjectModifiedEvent(d1))
    >>> len(cat.indexed)
    1
    >>> cat.indexed.pop()
    (..., <Dummy 'one'>)

Preventing automatic indexing
-----------------------------

Sometimes it is not accurate to automatically index an object. For
example when a lot of indexes are in the catalog and only
specific indexes needs to be updated. There are marker interfaces to
achieve this.

.. doctest::

    >>> from zope.catalog.interfaces import INoAutoIndex

If an object provides this interface it is not automatically indexed.

.. doctest::

    >>> interface.alsoProvides(d1, INoAutoIndex)
    >>> catalog.indexDocSubscriber(IntIdAddedEvent(d1, None))
    >>> len(cat.indexed)
    0

    >>> from zope.catalog.interfaces import INoAutoReindex

If an object provides this interface it is not automatically reindexed.

.. doctest::

    >>> interface.alsoProvides(d1, INoAutoReindex)
    >>> catalog.reindexDocSubscriber(ObjectModifiedEvent(d1))
    >>> len(cat.indexed)
    0
