# Overleaf synchronization workflow

> **Agent restriction:** `docs/energy_patterns_clim_dyn/` is a protected, read-only backup.
> Danilo works on the manuscript in Overleaf and brings an updated backup into this repository
> only occasionally. Agents must not modify, regenerate, compile, synchronize, rename, delete,
> or copy files into that directory. The commands below document the owner's manual backup
> procedure; they are not authorized agent actions.

## Authority boundaries

- **Overleaf is canonical for manuscript text, figures, bibliography, styles, and all other
  manuscript project files.**
- **GitHub is canonical for code, processed data, analyses, and computational results.**
- `docs/energy_patterns_clim_dyn/` is a historical snapshot of Overleaf, not a manuscript
  workspace and not a destination for generated results.
- Only Danilo updates that snapshot. Agents may treat it as read-only reference material but
  must perform all computational and figure work elsewhere in the repository.
- The Overleaf project and the GitHub repository have independent Git histories. They must
  not be merged with `--allow-unrelated-histories` or reconciled through a force push.
- Repository results may be transferred into the manuscript only as an explicit, reviewed
  scientific update performed in Overleaf. Updating the repository backup remains a separate,
  manual action by Danilo.

## Safe synchronization gate

Danilo may run the audit before and after a manual backup update:

```bash
python scripts/overleaf_sync.py audit
```

The audit fetches `overleaf/main`, compares its complete file tree with
`docs/energy_patterns_clim_dyn`, and reports file-level divergence using Git blob hashes. It
does not modify the manuscript. Agents may use this audit only for a read-only status report;
they must not follow it with a write operation.

When Overleaf contains canonical changes that Danilo wants to preserve as a new repository
backup, he may review the reported paths and then run:

```bash
python scripts/overleaf_sync.py pull --apply --write-state
```

This command is owner-operated and must not be run by an agent. The pull is intentionally
one-way. It refuses to run if the repository manuscript directory
contains local changes or files absent from Overleaf, copies only the paths present in the
Overleaf tree, and verifies all hashes afterward. It never commits or pushes.

Updating Overleaf with approved computational results remains a manual, owner-reviewed operation:

1. Start from `overleaf/main` in a dedicated checkout.
2. Apply only the approved text, figure, and table changes backed by repository results.
3. Compile and validate cross-references, figures, tables, and reported values.
4. Commit with the source result paths and scientific decision in the message.
5. Push normally to `overleaf/main`; never use a destructive force push.
6. When a new backup is desired, Danilo mirrors the resulting canonical Overleaf tree into
   the repository with the guarded pull.

## Initial audit — 2026-09-27

- GitHub `main`: `3830c4afddc98ee90676a56482f1bfeace101a39`
- Overleaf `main`: `66af879d9a5544ea2e1fce1e67310088f8a265ba`
- Common ancestor: none; histories are independent.
- Manuscript inventory: 18 files on each side.
- Content comparison: all 18 files are byte-identical.
- Conflicts: none.
- Decision: no merge and no manuscript rewrite were necessary. The Overleaf snapshot is
  already mirrored exactly in `docs/energy_patterns_clim_dyn`.
