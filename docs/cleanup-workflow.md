# GraphFakos Cleanup Workflow

Use this workflow when a change is primarily cleanup, simplification, or
maintainability work. It keeps broad quality claims tied to reviewable evidence.

## Choose the right scope

1. Use a post-authoring pass for the files changed by one feature.
2. Use a bounded sweep for one package area or an explicit file set.
3. Use a broad sweep only when every claimed source, test, or script file will
   receive an explicit review disposition.
4. Keep test cleanup separate when it changes test structure or coverage proof.

Small local cleanup does not need a tracker. Broad cleanup needs a fresh
inventory and a ledger kept outside the committed package surface.

## Freeze the inventory

Before editing:

1. inspect the current worktree and preserve unrelated changes,
2. list the current tracked files with `git ls-files`,
3. split source, tests, scripts, and docs when more than one tree is in scope,
4. record the exact file count and do not add silent scope later.

A broad claim cannot rely on remembered files or a hand-picked hotspot list.

## Record every disposition

Use one ledger row per claimed file:

`path | area | before LOC | after LOC | disposition | rationale | validation`

Allowed dispositions are:

1. `trim` for a behavior-preserving simplification,
2. `keep` when the current code already earns its shape,
3. `defer-owned:<issue>` when another active change owns the file,
4. `defer-later:<reason>` when evidence does not justify editing now.

Close only when every inventory row has a disposition and the remaining count
is zero.

## Simplify without weakening contracts

Prefer deleting pass-through wrappers, duplicate glue, fake abstractions,
unneeded commentary, and repeated ownership. Preserve public DTOs, provider
boundaries, static fallback behavior, accessibility, and documented imports.

For GraphFakos UI changes, keep the graph primary and run browser proof when
interaction, responsive layout, or JavaScript behavior changes.

## Validate

Use the narrowest useful loop while editing, then close with:

```bash
make check
```

Run `make browser-e2e` for browser-facing viewer changes and
`make release-check` for package or release-surface changes. Refresh the
inventory if the worktree changes during validation, and report any unrelated
failure separately instead of absorbing it into the cleanup.
