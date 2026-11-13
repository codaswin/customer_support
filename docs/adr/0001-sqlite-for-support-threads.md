# SQLite for Support Threads

Support Threads are persisted in a local SQLite file, via the standard-library `sqlite3` module.

Support Threads must survive a restart. SQLite needs no server or setup, which fits an assignment. The alternative was Postgres, which adds infrastructure for no benefit at this scale. Moving later is cheap because the store sits behind one small class.
