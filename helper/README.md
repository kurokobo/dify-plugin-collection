# Helper Scripts

## update_repository_readme.py

Updates the `README.md` at the root of the repository.

```bash
cd helper
uv run helper/update_repository_readme.py
```

This script searches for pairs of `<!-- ls: ... -->` and `<!-- /ls: ... -->` in the `README.md`, collects all plugin manifests in the specified directories, generates a list, and update the `README.md` with the generated list.
