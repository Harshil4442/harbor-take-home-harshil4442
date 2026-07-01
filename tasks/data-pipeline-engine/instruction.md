Hey, I've been working on this data pipeline engine and it's mostly working but there are a few bugs I need help fixing.

First, when we validate a record against a schema, it handles flat fields fine, but if a field is defined as an object with its own properties, the validator just checks if it's a dictionary and completely ignores the nested properties. It should really be recursively validating those nested fields too so things don't slip through.

Also, the error recovery seems broken. We have a quarantine strategy that's supposed to move a failing record to a quarantine list and then continue processing the rest of the records. But right now, it correctly adds the record to quarantine and then just stops the whole pipeline as if it was in fail-fast mode.

Another issue is with the aggregation stage. When we group records and compute an average, it's dividing the sum by the total number of records across all groups, rather than the count of records in that specific group. This throws off the averages entirely whenever we have groups of different sizes.

Finally, in the transformation stage, we can define computed fields using arithmetic expressions. The problem is that all computed fields are evaluated against a snapshot of the original record. So if one computed field relies on the result of a previously computed field in the same transform list, it just sees zero instead of the updated value. It needs to evaluate each expression against the record as updated by the previous transforms.

Can you fix these issues for me? All the entry points you'll need are in the pipeline module (engine, validator, handler, aggregate, transform, config).
