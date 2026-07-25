# Contributing

Thanks for your interest in contributing to an **Aswincloud** project! This guide applies org-wide; individual repos may add their own notes in a local `CONTRIBUTING.md`.

## Getting started

1. **Fork** the repository (or create a branch if you're a collaborator).
2. **Clone** your fork and create a topic branch:
   ```bash
   git checkout -b feat/short-description
   ```
3. Make your change, following the existing code style in that repo.
4. **Commit** with a clear message (see below).
5. **Open a pull request** against `main`.

## Branch naming

Use a short, prefixed branch name:

| Prefix | For |
| ------ | --- |
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation only |
| `chore/` | Tooling, deps, housekeeping |
| `refactor/` | Code changes with no behavior change |

## Commit messages

Write in the imperative mood and keep the subject under ~72 characters:

```
Add rate limiting to the webhook handler

Longer explanation of what and why, if needed. Wrap at ~72 cols.
```

Conventional Commits (`feat:`, `fix:`, `docs:` …) are welcome but not required.

## Pull requests

Our repositories use a **merge queue** and **required reviews**. When you open a PR:

- Fill in the **PR template** checklist.
- Keep PRs focused — one logical change per PR is easier to review.
- Make sure **CI checks pass**. Required checks also run in the merge queue.
- A maintainer will review. Once **approved and all checks pass**, a maintainer clicks **"Merge when ready"** and the PR enters the merge queue, which merges it to `main` automatically once it's green at the front of the queue.
- Branches are squash-merged and deleted automatically.

## Reporting bugs & requesting features

Use the **issue templates** (Bug report / Feature request) on the repository's **Issues** tab. For **security issues**, do **not** open a public issue — see [SECURITY.md](SECURITY.md).

## Code of Conduct

By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

Unless a repository states otherwise, contributions are accepted under that repository's license (most are **MIT**). By contributing, you agree your contributions are licensed under the same terms.
