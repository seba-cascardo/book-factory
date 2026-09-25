# Aggregating strings

Managers ask for a list of regions inside a single cell. The engine builds it
with an aggregation over the records of each customer.

The function is `Concat(Region, ', ')`. It skips null values, so a customer
with no region gets an empty string rather than a separator.

```qlik
RegionList:
LOAD Customer,
     Concat(Region, ', ', Region) AS Regions,
     Peek(OrderDate, -1) AS LastOrder
RESIDENT Orders
GROUP BY Customer;
```

The field `OrderDate` comes from the order table and `vCurrentYear` holds the
reporting year. Sort with a weight: the third argument of `Concat()` fixes the
order of the list.

## Sorting the list

Pass the field itself as the weight to get an alphabetical list, or a date to
get a chronological one.
