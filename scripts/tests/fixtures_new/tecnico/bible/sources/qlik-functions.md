# Script and chart functions (excerpt)

## String aggregation

`Concat(expression [, delimiter [, sort_weight]])` returns the aggregated string
concatenation of all the values of the expression.

## Inter-record functions

`Peek(field_name [, row_no [, table_name]])` returns the value of a field in a
row that has already been loaded. `Previous(expression)` reads the previous
input record.

## Aggregation

`Sum()`, `Count()`, `Only()`, `Aggr()` and `FirstSortedValue()` aggregate over
the records of the current dimension.

```qlik
Orders:
LOAD Region, Sum(Sales) AS TotalSales
RESIDENT RawOrders
GROUP BY Region;

STORE Orders INTO [lib://Data/orders.qvd] (qvd);
```
