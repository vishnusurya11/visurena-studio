"""The Command Center's board (decision 2026-09-25, C10 + C11): a web view of
the department tables with the owner's hand.  `app.make_app` builds it, `views`
are the tested layer, `models` the JSON contract, `library_paths` the one guard
on the artefact route, `actions` the hand: each POST under /act/ is one call
into studio/work_orders through a separate writable connection.  Nothing in
this package runs a step, spawns a process, writes a file or writes a row
except through that one call."""
