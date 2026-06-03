# Contributing to llm-wiki-v2

Thank you for your interest in contributing!

## Project structure

```
llm-wiki-v2/
├── SKILL.md              # Core skill definition & workflow documentation
├── lib/                  # Python libraries (confidence, search, quality, etc.)
├── scripts/              # Shell script workflow runners
├── templates/            # Page templates (entity, topic, source, etc.)
├── deps/                 # Bundled third-party tools
├── platforms/            # Platform-specific entry files
├── .github/
│   └── ISSUE_TEMPLATE/   # Bug report / feature request / question templates
└── docs/                 # Additional documentation
```

## What to contribute

**High-value contributions:**
- New Python libraries in `lib/` (search backends, scoring algorithms, etc.)
- New workflow scripts in `scripts/`
- Improvements to SKILL.md workflow documentation
- Bug fixes with tests
- Documentation improvements (English and Chinese)

**Not this repo:**
- llm-wiki **v1** development → see the `v1` branch
- Graph UI (knowledge-graph.html) → maintained separately

## Development workflow

### Local setup

```bash
git clone https://github.com/sdyckjq-lab/llm-wiki-skill.git
cd llm-wiki-skill
git checkout -b feature/my-feature  # or bugfix/issue-number
```

### Testing your changes

```bash
# Test Python libraries
python lib/your_module.py  # run the module's main/test block

# Test shell scripts
bash scripts/your-script.sh --dry-run <test-wiki-root>

# Test with a real knowledge base
bash install.sh --platform openclaw --target-dir /tmp/test-llm-wiki
```

### Coding standards

- **Python**: PEP 8, type hints where possible, docstrings for public functions
- **Shell**: `set -euo pipefail`, check return codes, use `$()` not backticks
- **Documentation**: Update SKILL.md if you change or add a workflow; add tests if you add logic
- **Frontmatter**: All v2 pages must use YAML frontmatter (not HTML comment style)

## Pull request process

1. **Fork** the repo and create a branch: `feature/xxx` or `bugfix/xxx`
2. **Test** your changes locally
3. **Update docs** — SKILL.md workflow section, README, CHANGELOG
4. **Open PR** with the PR template filled out
5. Link the related issue: `Fixes #123` or `Ref #123`

## Commit message convention

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Examples:
- `feat(search): add BM25 ranking with jieba tokenization`
- `fix(migrate): handle BOM character in v1 frontmatter`
- `docs: add v2 workflow reference table to README`

## Issue guidelines

- **Bug reports**: Include version, platform, exact steps to reproduce, and any error output
- **Feature requests**: Describe the problem solved, not just the proposed solution
- **Questions**: Check README.md and CHANGELOG.md first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
