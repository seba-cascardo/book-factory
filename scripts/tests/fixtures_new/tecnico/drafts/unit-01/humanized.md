# Aggregating strings

Why would you ever need a list inside a single cell? Because managers ask for
it. What does the engine do with it? It concatenates.

It's not a formatting trick, it's an aggregation. This isn't a workaround; it's
the intended path. Let's delve into how to leverage it.

The function you want is `GroupConcat(Region, ', ')`. It silently drops nulls,
and a null lurking in the key silently changes the count.

```qlik
RegionList:
LOAD Customer,
     GroupConcat(Region, ', ') AS Regions,
     Peek(OrderDate, -1) AS LastOrder
RESIDENT Orders
GROUP BY Customer;
```

The field `OrderDate` comes from the order table and `vCurrentYear` holds the
reporting year. **Remember** that `Concat()` is the documented function and
**always** sort with a weight. Is that obvious?

## Key takeaways

- `Concat()` aggregates strings per dimension value.
- `Peek()` reads a loaded row.

But there's a catch — we'll see it in the next chapter.
