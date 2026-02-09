# Plugin Submission Requirements

Requirements for submitting an Obsidian plugin to the community directory.

## Plugin ID rules

The plugin ID (in `manifest.json`) has strict naming requirements enforced by the validation bot:

- Must **not** contain "obsidian" (in any case)
- Must **not** end with "plugin" (in any case)

```json
// CORRECT
{ "id": "timestamp-inserter" }
{ "id": "daily-notes-companion" }

// WRONG
{ "id": "obsidian-timestamp" }
{ "id": "timestamp-plugin" }
{ "id": "obsidian-notes-plugin" }
```

## Plugin name rules

The plugin name (in `manifest.json`) has strict naming requirements:

- Must **not** contain "Obsidian" (in any case)
- Must **not** end with "Plugin" (in any case)
- Must **not** start with "Obsi" or end with "dian"

```json
// CORRECT
{ "name": "Timestamp Inserter" }
{ "name": "Daily Notes Companion" }

// WRONG
{ "name": "Obsidian Timestamp" }
{ "name": "Timestamp Plugin" }
{ "name": "Obsidian Notes Plugin" }
{ "name": "ObsiNotes" }
{ "name": "Notesidian" }
```

## Description rules

The plugin description in `manifest.json`:

- Must **not** contain "Obsidian"
- Must **not** start with "This plugin", "A plugin", "An Obsidian plugin", etc.
- Must end with proper punctuation: `.` `?` `!` `)`

```json
// CORRECT
{ "description": "Insert timestamps into your notes with customizable formats." }
{ "description": "Track daily habits and visualize progress over time." }

// WRONG
{ "description": "An Obsidian plugin that inserts timestamps" }
{ "description": "This plugin helps you track habits" }
{ "description": "Insert timestamps into your notes" }  // missing punctuation
```

## Repository structure

A properly structured plugin repository contains:

```
my-plugin/
├── manifest.json        # Plugin metadata (required)
├── main.ts              # Plugin entry point
├── styles.css           # Plugin styles (optional)
├── package.json         # Node.js package manifest
├── tsconfig.json        # TypeScript configuration
├── esbuild.config.mjs   # Build configuration
├── .eslintrc.json       # ESLint configuration (recommended)
├── .gitignore           # Git ignore rules
├── versions.json        # Version compatibility mapping
└── README.md            # Plugin documentation
```

### manifest.json

```json
{
  "id": "my-plugin-id",
  "name": "My Plugin Name",
  "version": "1.0.0",
  "minAppVersion": "0.15.0",
  "description": "A concise description of what the plugin does.",
  "author": "Your Name",
  "authorUrl": "https://github.com/yourusername",
  "isDesktopOnly": false
}
```

Fields:
- `id`: Unique plugin identifier (see naming rules above)
- `name`: Display name (see naming rules above)
- `version`: Semantic version (see below)
- `minAppVersion`: Minimum Obsidian version required
- `description`: Concise description (see rules above)
- `author`: Your name or username
- `authorUrl`: Link to your profile or site
- `isDesktopOnly`: Set `true` only if the plugin cannot work on mobile

### versions.json

Maps plugin versions to minimum Obsidian versions:

```json
{
  "1.0.0": "0.15.0",
  "1.1.0": "0.15.0",
  "2.0.0": "1.0.0"
}
```

## Semantic versioning

Follow [SemVer](https://semver.org/):

- **MAJOR** (1.0.0 -> 2.0.0): Breaking changes (settings format changes, removed features)
- **MINOR** (1.0.0 -> 1.1.0): New features, backwards compatible
- **PATCH** (1.0.0 -> 1.0.1): Bug fixes, backwards compatible

The version in `manifest.json`, `package.json`, and `versions.json` must be consistent.

## Submission process

1. **Create a GitHub release** with the following assets:
   - `main.js` - compiled plugin code
   - `manifest.json` - plugin metadata
   - `styles.css` - plugin styles (if applicable)

2. **Submit a pull request** to [obsidianmd/obsidian-releases](https://github.com/obsidianmd/obsidian-releases):
   - Add your plugin to `community-plugins.json`
   - Include: id, name, author, description, repo

3. **Validation bot** will check your submission automatically for:
   - Naming rule compliance
   - Description formatting
   - Required files in release
   - manifest.json structure

## Pre-submission testing checklist

- [ ] Plugin loads without errors
- [ ] Plugin unloads cleanly (no leftover event listeners, DOM elements, or intervals)
- [ ] All commands work correctly
- [ ] Settings save and load properly
- [ ] Settings persist after plugin reload
- [ ] No `console.log` in `onload`/`onunload`
- [ ] All sample/template code removed
- [ ] Works on both desktop and mobile (unless `isDesktopOnly: true`)
- [ ] No hardcoded paths (using `normalizePath`, `vault.configDir`)
- [ ] No iOS-incompatible features (regex lookbehind, etc.)
- [ ] All interactive elements are keyboard accessible
- [ ] Icon buttons have ARIA labels
- [ ] CSS uses Obsidian variables (not hardcoded values)
- [ ] CSS is scoped to plugin selectors
- [ ] No `innerHTML`/`outerHTML` usage
- [ ] manifest.json version matches package.json version
- [ ] versions.json is up to date
- [ ] README.md describes features and usage
- [ ] All files needed for the release are built and included
