# io/

Filesystem access bound to the workspace resolver + authority model.

- `workspace.py` — `WorkspaceResolver` (canonical root + safe resolution:
  traversal, absolute paths, symlink/UNC escapes blocked; semantic aliases
  `vault/ council/ skills/ core/ learn/` map to their canonical `.jarvis/`
  locations) and `SafeIO` (reads always allowed; **writes require an
  `Authority` whose scope covers the target, else `MUTATION_DENIED`**).

The boundary is explicit and inspectable: the kernel never writes outside
an authorized scope, and no path can escape the workspace roots.