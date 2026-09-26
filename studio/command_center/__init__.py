"""The Command Center's board (decision 2026-09-25, C10): a read-only web
view of the department tables.  `app.make_app` builds it, `views` are the
tested layer, `models` the JSON contract, `library_paths` the one guard on
the artefact route.  Nothing in this package runs a step, spawns a process,
writes a file or opens the database for writing."""
