Catalogs
========

Catalogs provide management of collections of related indexes with a
basic search algorithm.  Let's look at an example:

    >>> from zope.catalog.catalog import Catalog
    >>> cat = Catalog()

We can add catalog indexes to catalogs.  A catalog index is, among
other things, an attribute index. It indexes attributes of objects. To
see how this works, we'll create a demonstration attribute index. Our
attribute index will simply keep track of objects that have a given
attribute value.  The `catalog` package provides an attribute-index
mix-in class that is meant to work with a base indexing class. First,
we'll write the base index class:

    >>> import persistent, BTrees.OOBTree, BTrees.IFBTree, BTrees.IOBTree
    >>> import zope.interface, zope.index.interfaces

    >>> @zope.interface.implementer(
    ...         zope.index.interfaces.IInjection,
    ...         zope.index.interfaces.IIndexSearch,
    ...         zope.index.interfaces.IIndexSort,
    ...         )
    ... class BaseIndex(persistent.Persistent):
    ...
    ...     def clear(self):
    ...         self.forward = BTrees.OOBTree.OOBTree()
    ...         self.backward = BTrees.IOBTree.IOBTree()
    ...
    ...     __init__ = clear
    ...
    ...     def index_doc(self, docid, value):
    ...         if docid in self.backward:
    ...             self.unindex_doc(docid)
    ...         self.backward[docid] = value
    ...
    ...         set = self.forward.get(value)
    ...         if set is None:
    ...             set = BTrees.IFBTree.IFTreeSet()
    ...             self.forward[value] = set
    ...         set.insert(docid)
    ...
    ...     def unindex_doc(self, docid):
    ...         value = self.backward.get(docid)
    ...         if value is None:
    ...             return
    ...         self.forward[value].remove(docid)
    ...         del self.backward[docid]
    ...
    ...     def apply(self, value):
    ...         set = self.forward.get(value)
    ...         if set is None:
    ...             set = BTrees.IFBTree.IFTreeSet()
    ...         return set
    ...
    ...     def sort(self, docids, limit=None, reverse=False):
    ...         for i, docid in enumerate(sorted(docids, key=self.backward.get, reverse=reverse)):
    ...             yield docid
    ...             if limit and i >= (limit - 1):
    ...                 break

The class implements `IInjection` to allow values to be indexed and
unindexed and `IIndexSearch` to support searching via the `apply`
method.

Now, we can use the AttributeIndex mixin to make this an attribute
index:

    >>> import zope.catalog.attribute
    >>> import zope.catalog.interfaces
    >>> import zope.container.contained

    >>> @zope.interface.implementer(zope.catalog.interfaces.ICatalogIndex)
    ... class Index(zope.catalog.attribute.AttributeIndex, 
    ...             BaseIndex,
    ...             zope.container.contained.Contained,
    ...             ):
    ...    pass

Unfortunately, because of the way we currently handle containment
constraints, we have to provide `ICatalogIndex`, which extends
`IContained`. We subclass `Contained` to get an implementation for
`IContained`. 

Now let's add some of these indexes to our catalog.  Let's create some
indexes.  First we'll define some interfaces providing data to index:

    >>> class IFavoriteColor(zope.interface.Interface):
    ...     color = zope.interface.Attribute("Favorite color")

    >>> class IPerson(zope.interface.Interface):
    ...     def age():
    ...         """Return the person's age, in years"""

We'll create color and age indexes:

    >>> cat['color'] = Index('color', IFavoriteColor)
    >>> cat['age'] = Index('age', IPerson, True)
    >>> cat['size'] = Index('sz')

The indexes are created with:

- the name of the of the attribute to index

- the interface defining the attribute, and

- a flag indicating whether the attribute should be called, which
  defaults to false.

If an interface is provided, then we'll only be able to index an
object if it can be adapted to the interface, otherwise, we'll simply
try to get the attribute from the object. If the attribute isn't
present, then we'll ignore the object.

Now, let's create some objects and index them:

    >>> @zope.interface.implementer(IPerson)
    ... class Person:
    ...     def __init__(self, age):
    ...         self._age = age
    ...     def age(self):
    ...         return self._age

    >>> @zope.interface.implementer(IFavoriteColor)
    ... class Discriminating:
    ...     def __init__(self, color):
    ...         self.color = color

    >>> class DiscriminatingPerson(Discriminating, Person):
    ...     def __init__(self, age, color):
    ...         Discriminating.__init__(self, color)
    ...         Person.__init__(self, age)

    >>> class Whatever:
    ...     def __init__(self, **kw):
    ...         self.__dict__.update(kw)

    >>> o1 = Person(10)
    >>> o2 = DiscriminatingPerson(20, 'red')
    >>> o3 = Discriminating('blue')
    >>> o4 = Whatever(a=10, c='blue', sz=5)
    >>> o5 = Whatever(a=20, c='red', sz=6)
    >>> o6 = DiscriminatingPerson(10, 'blue')

    >>> cat.index_doc(1, o1)
    >>> cat.index_doc(2, o2)
    >>> cat.index_doc(3, o3)
    >>> cat.index_doc(4, o4)
    >>> cat.index_doc(5, o5)
    >>> cat.index_doc(6, o6)

We search by providing query mapping objects that have a key for every
index we want to use:

    >>> list(cat.apply({'age': 10}))
    [1, 6]
    >>> list(cat.apply({'age': 10, 'color': 'blue'}))
    [6]
    >>> list(cat.apply({'age': 10, 'color': 'blue', 'size': 5}))
    []
    >>> list(cat.apply({'size': 5}))
    [4]

We can unindex objects:

    >>> cat.unindex_doc(4)
    >>> list(cat.apply({'size': 5}))
    []

and reindex objects:

    >>> o5.sz = 5
    >>> cat.index_doc(5, o5)
    >>> list(cat.apply({'size': 5}))
    [5]

If we clear the catalog, we'll clear all of the indexes:

    >>> cat.clear()
    >>> [len(index.forward) for index in cat.values()]
    [0, 0, 0]

Note that you don't have to use the catalog's search methods. You can
access its indexes directly, since the catalog is a mapping:

    >>> [(name, cat[name].field_name) for name in cat]
    [(u'age', 'age'), (u'color', 'color'), (u'size', 'sz')]

Catalogs work with int-id utilities, which are responsible for
maintaining id <-> object mappings.  To see how this works, we'll
create a utility to work with our catalog:

    >>> import zope.intid.interfaces
    >>> @zope.interface.implementer(zope.intid.interfaces.IIntIds)
    ... class Ids:
    ...     def __init__(self, data):
    ...         self.data = data
    ...     def getObject(self, id):
    ...         return self.data[id]
    ...     def __iter__(self):
    ...         return self.data.iterkeys()
    >>> ids = Ids({1: o1, 2: o2, 3: o3, 4: o4, 5: o5, 6: o6})
    
    >>> from zope.component import provideUtility
    >>> provideUtility(ids, zope.intid.interfaces.IIntIds)

With this utility in place, catalogs can recompute indexes:

    >>> cat.updateIndex(cat['size'])
    >>> list(cat.apply({'size': 5}))
    [4, 5]

Of course, that only updates *that* index:

    >>> list(cat.apply({'age': 10}))
    []

We can update all of the indexes:

    >>> cat.updateIndexes()
    >>> list(cat.apply({'age': 10}))
    [1, 6]
    >>> list(cat.apply({'color': 'red'}))
    [2]
    

There's an alternate search interface that returns "result sets".
Result sets provide access to objects, rather than object ids:

    >>> result = cat.searchResults(size=5)
    >>> len(result)
    2
    >>> list(result) == [o4, o5]
    True

The searchResults method also provides a way to sort, limit and reverse
results.

When not using sorting, limiting and reversing are done by simple slicing
and list reversing.

    >>> list(cat.searchResults(size=5, _reverse=True)) == [o5, o4]
    True

    >>> list(cat.searchResults(size=5, _limit=1)) == [o4]
    True

    >>> list(cat.searchResults(size=5, _limit=1, _reverse=True)) == [o5]
    True

However, when using sorting by index, the limit and reverse parameters
are passed to the index ``sort`` method so it can do it efficiently.

Let's index more objects to work with:

    >>> o7 = DiscriminatingPerson(7, 'blue')
    >>> o8 = DiscriminatingPerson(3, 'blue')
    >>> o9 = DiscriminatingPerson(14, 'blue')
    >>> o10 = DiscriminatingPerson(1, 'blue')
    >>> ids.data.update({7: o7, 8: o8, 9: o9, 10: o10})
    >>> cat.index_doc(7, o7)
    >>> cat.index_doc(8, o8)
    >>> cat.index_doc(9, o9)
    >>> cat.index_doc(10, o10)

Now we can search all people who like blue, ordered by age:

    >>> results = list(cat.searchResults(color='blue', _sort_index='age'))
    >>> results == [o3, o10, o8, o7, o6, o9]
    True

    >>> results = list(cat.searchResults(color='blue', _sort_index='age', _limit=3))
    >>> results == [o3, o10, o8]
    True

    >>> results = list(cat.searchResults(color='blue', _sort_index='age', _reverse=True))
    >>> results == [o9, o6, o7, o8, o10, o3]
    True

    >>> results = list(cat.searchResults(color='blue', _sort_index='age', _reverse=True, _limit=4))
    >>> results == [o9, o6, o7, o8]
    True

The index example we looked at didn't provide document scores.  Simple
indexes normally don't, but more complex indexes might give results
scores, according to how closely a document matches a query.  Let's
create a new index, a "keyword index" that indexes sequences of
values:

    >>> @zope.interface.implementer(
    ...         zope.index.interfaces.IInjection,
    ...         zope.index.interfaces.IIndexSearch,
    ...         )
    ... class BaseKeywordIndex(persistent.Persistent):
    ...
    ...     def clear(self):
    ...         self.forward = BTrees.OOBTree.OOBTree()
    ...         self.backward = BTrees.IOBTree.IOBTree()
    ...
    ...     __init__ = clear
    ...
    ...     def index_doc(self, docid, values):
    ...         if docid in self.backward:
    ...             self.unindex_doc(docid)
    ...         self.backward[docid] = values
    ...
    ...         for value in values:
    ...             set = self.forward.get(value)
    ...             if set is None:
    ...                 set = BTrees.IFBTree.IFTreeSet()
    ...                 self.forward[value] = set
    ...             set.insert(docid)
    ...
    ...     def unindex_doc(self, docid):
    ...         values = self.backward.get(docid)
    ...         if values is None:
    ...             return
    ...         for value in values:
    ...             self.forward[value].remove(docid)
    ...         del self.backward[docid]
    ...
    ...     def apply(self, values):
    ...         result = BTrees.IFBTree.IFBucket()
    ...         for value in values:
    ...             set = self.forward.get(value)
    ...             if set is not None:
    ...                 _, result = BTrees.IFBTree.weightedUnion(result, set)
    ...         return result

    >>> @zope.interface.implementer(zope.catalog.interfaces.ICatalogIndex)
    ... class KeywordIndex(zope.catalog.attribute.AttributeIndex, 
    ...                    BaseKeywordIndex,
    ...                    zope.container.contained.Contained,
    ...                    ):
    ...    pass

Now, we'll add a hobbies index:

    >>> cat['hobbies'] = KeywordIndex('hobbies')
    >>> o1.hobbies = 'camping', 'music'
    >>> o2.hobbies = 'hacking', 'sailing'
    >>> o3.hobbies = 'music', 'camping', 'sailing'
    >>> o6.hobbies = 'cooking', 'dancing'
    >>> cat.updateIndexes()

When we apply the catalog:

    >>> cat.apply({'hobbies': ['music', 'camping', 'sailing']})
    BTrees.IFBTree.IFBucket([(1, 2.0), (2, 1.0), (3, 3.0)])

We found objects 1-3, because they each contained at least some of the
words in the query.  The scores represent the number of words that
matched. If we also include age:

    >>> cat.apply({'hobbies': ['music', 'camping', 'sailing'], 'age': 10})
    BTrees.IFBTree.IFBucket([(1, 3.0)])

The score increased because we used an additional index.  If an index
doesn't provide scores, scores of 1.0 are assumed.

