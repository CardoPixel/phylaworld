# Contributing to Phylaworld

First off: thank you for considering contributing to Phylaworld. This is a
community-first, open-source project built on free and open software — every
contribution, no matter how small, moves the world forward.

Please take a moment to read this guide. It keeps the project healthy and makes
everyone's work easier to review and merge.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Good First Issues & Where to Start](#good-first-issues--where-to-start)
- [Project Setup (Development)](#project-setup-development)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Requesting Features / Raising Issues](#requesting-features--raising-issues)
  - [Writing Code (GDScript)](#writing-code-gdscript)
  - [Creating Art](#creating-art)
  - [Creating Audio](#creating-audio)
  - [Writing Documentation](#writing-documentation)
  - [AI-Assisted Contributions](#ai-assisted-contributions)
- [Style Guide](#style-guide)
- [Testing & Verification](#testing--verification)
- [Pull Request Process](#pull-request-process)
- [Commit Messages](#commit-messages)
- [Versioning & Changelog](#versioning--changelog)
- [License & Legal](#license--legal)

## Code of Conduct

All participants are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).
Please report unacceptable behavior to the community leaders.

## Good First Issues & Where to Start

- Look for issues labeled `good first issue` and `help wanted`.
- Introduce yourself on our [Discord / Forums] before diving in.
- If you're unsure where something is in the codebase, ask — nobody here was
  born knowing it.

## Project Setup (Development)

1. Install [Godot 4.x](https://godotengine.org/download).
2. Clone the repository.
3. Open `project.godot` in Godot.
4. Run the project from the editor.

You don't need to build Godot from source — the editor is the build environment.

## How Can I Contribute?

### Reporting Bugs

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.yml). A good
bug report includes:

- The **Godot version** and **platform** (Windows, Linux, Android, Web).
- **Steps to reproduce**, clearly numbered.
- What you **expected** vs what **actually happened**.
- Any **error output** from the Godot debugger or terminal.
- Screenshots or videos if they help.

If you found a **security vulnerability**, do **not** open a public issue — see
[SECURITY.md](SECURITY.md).

### Requesting Features / Raising Issues

Use the [General Issue template](.github/ISSUE_TEMPLATE/general_issue.yml).
Before opening a new issue, search existing issues — it may already be
discussed.

### Writing Code (GDScript)

- Check existing issues and discussions for a design agreed upon by maintainers.
- Keep changes **focused and atomic** — one fix or feature per PR.
- Follow the [Style Guide](#style-guide) below.
- Verify your code — see [Testing & Verification](#testing--verification).

### Creating Art

- **Pixel art sprites, tiles, and animations**: Aseprite is the preferred tool.
  Provide the `.aseprite` source when you can, not only the exported PNGs.
- **Concept / key art**: Krita, GIMP, or Blender.
- Follow the project's resolution, palette, and layer conventions (once
  published, these will be in `docs/`).
- Keep source files available so future contributors can iterate.

### Creating Audio

The music/SFX pipeline is still being decided (candidates: FamiStudio,
Dn-FamiTracker, Ardour, LMMS). Until the pipeline is finalized, check with the
team before contributing audio assets.

### Writing Documentation

Typos, guides, and doc improvements are very welcome. Root-level docs live in
`docs/`. Keep README and this file accurate when you change things.

### AI-Assisted Contributions

**This project is explicitly AI-friendly.** Contributions produced or assisted
by AI tools (code, art, audio, docs, prompts, pipelines) are welcome.

- **Disclose it.** When AI was significantly involved, say so in the PR
  description — it helps reviewers verify assumptions.
- **Review the output.** The author is responsible for correctness and style,
  whether the text was typed by hand or generated.
- **Verify before submitting.** AI output must pass the same checks as any
  other contribution.

## Style Guide

- **GDScript**: Follow the official
  [GDScript style guide](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_styleguide.html).
  Match the conventions of the files you touch.
- **Naming**: Use descriptive, consistent names throughout.
- **Comments**: Explain *why*, not *what*. Update comments when you change code.
- **Scenes/resources**: Prefer godot-native formats (`.tscn`, `.tres`) and
  res:// paths.

## Testing & Verification

- After changing a script, open it in the Godot editor and check the script
  panel for parse errors before committing.
- Run the game and exercise the feature you touched.
- If the project has a test suite under `res://tests/`, run it and keep it
  green.

## Pull Request Process

1. Fork the repository and create a branch with a descriptive name
   (e.g. `fix/tamer-collision`, `feat/creature-breeding`).
2. Make your changes in focused commits.
3. Open a Pull Request using the
   [PR template](.github/pull_request_template.md).
4. Fill out the template completely and clearly.
5. A maintainer will review. Expect feedback — iterate, don't take it
   personally.
6. Verify the automated checks pass (if CI is configured) and that you
   followed this guide.

Keep PRs small. Large PRs are harder to review and merge slowly; when in doubt,
split the work.

## Commit Messages

Phylaworld uses **gitmoji + Conventional Commits**:

```
<gitmoji> <type>(<scope>): <subject>
```

- Start the subject with a relevant [gitmoji](https://gitmoji.dev) emoji.
- Use a Conventional Commits `<type>` — `feat`, `fix`, `docs`, `refactor`,
  `perf`, `test`, `build`, `ci`, `chore`, or `revert`.
- Add an optional `<scope>` in parentheses when the change is area-specific,
  e.g. `feat(battle)`, `fix(taming)`.
- Use the imperative mood and keep the subject line under 72 characters.
- Mark breaking changes with a `!` after the type/scope (e.g. `feat(api)!`)
  or a `BREAKING CHANGE:` footer.
- Add a body explaining *what* and *why* when needed.
- One logical change per commit.

### Examples

- `🐛 fix(taming): prevent wild creatures despawning mid-tame`
- `✨ feat(battle): add elemental weather effects`
- `💥 feat(research)!: require lab structures for trait analysis`
- `📝 docs(readme): clarify platform support`

## Versioning & Changelog

- The project follows [Semantic Versioning](https://semver.org)
  (`MAJOR.MINOR.PATCH`).
- The current version lives in `version.json` at the repository root — a
  single, tool-friendly source of truth that other tools can read without
  parsing the whole project.
- On every merge/commit to `main` (including merges from `dev`), a GitHub
  Actions workflow analyses the conventional commits since the last release
  and automatically:
  - bumps **MAJOR** for breaking changes (`!` or `BREAKING CHANGE:`; bumped as
    **MINOR** while the project is at `0.x`),
  - bumps **MINOR** for `feat` commits,
  - bumps **PATCH** for everything else,
  - appends a section to `CHANGELOG.md` in the
    [Conventional Changelog](https://github.com/conventional-changelog/conventional-changelog)
    style, and creates a `vX.Y.Z` tag.
- Commits pushed to `dev` **never** trigger a version bump.
- For the version to be derived correctly, always write conventional commit
  messages — see [Commit Messages](#commit-messages).

## License & Legal

By contributing, you agree that your contribution is licensed to the project
under the [GNU AGPL v3](LICENSE) license. Copyright belongs to the Phylaworld
Contributors. If you contribute art, audio, or assets, make sure you have the
right to share them; third-party assets must be under a compatible free
license.

If you have questions about licensing, ask in the Discussions forum before
submitting.

---

*Thanks again for building this world with us.*