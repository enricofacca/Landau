# Reuse registry

`components.toml` indexes useful code/assets that survived an experimental study without necessarily being promoted to `src/`.

Typical examples: benchmark harnesses, mesh utilities, solvers that are correct but too slow, diagnostic scripts, partial algorithms, or alternative implementations useful for cross-checking.

The study record is never deleted. The registry points back to the originating study and records limitations so a later stage can reuse the asset without rediscovering its history.
