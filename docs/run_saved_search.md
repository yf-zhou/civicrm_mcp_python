# Running a Saved Search

One way to have the LLM run a Saved Search using the existing tools (2025-12-01) is to have it first retrieve the search using `civicrm.search`, and then convert it into an API `get` operation for use with `civicrm.batch`.

An example call may look like: 

```
I have a Saved Search in CiviCRM called Bookkeeping Transactions. Please retrieve that Saved Search, then recreate the search as an API GET call and run it using the api batch tool. Limit the number of results to 25.
```