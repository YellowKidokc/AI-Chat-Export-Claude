# Obsidian Plugin Development Guidelines

Comprehensive guidelines for developing Obsidian plugins following official best practices, ESLint rules (`eslint-plugin-obsidianmd`), submission requirements, and accessibility standards.

## Quick start

For new plugin projects, use the interactive boilerplate generator:

```bash
node tools/create-plugin.js
```

This generates minimal, best-practice boilerplate with no sample code. It detects existing projects and only adds missing files. All generated code follows these guidelines automatically.

## Top 27 most critical rules

### Submission and naming (validation bot enforced)

| # | Rule | Enforcement |
|---|------|-------------|
| 1 | Plugin ID: no "obsidian", can't end with "plugin" | Validation bot |
| 2 | Plugin name: no "Obsidian", can't end with "Plugin" | Validation bot |
| 3 | Plugin name: can't start with "Obsi" or end with "dian" | Validation bot |
| 4 | Description: no "Obsidian", "This plugin", etc. | Validation bot |
| 5 | Description must end with `.?!)` punctuation | Validation bot |

### Memory and lifecycle

| # | Rule | Why |
|---|------|-----|
| 6 | Use `registerEvent()` for automatic cleanup | Prevents memory leaks |
| 7 | Don't store view references in plugin | Causes memory leaks |

### Type safety

| # | Rule | Why |
|---|------|-----|
| 8 | Use `instanceof` instead of type casting | Type safety for TFile/TFolder |

### UI/UX

| # | Rule | Why |
|---|------|-----|
| 9 | Use sentence case for all UI text | "Advanced settings" not "Advanced Settings" |
| 10 | No "command" in command names/IDs | Redundant |
| 11 | No plugin ID in command IDs | Obsidian auto-namespaces |
| 12 | No default hotkeys | Avoid conflicts |
| 13 | Use `.setHeading()` for settings headings | Not manual HTML |

### API best practices

| # | Rule | Why |
|---|------|-----|
| 14 | Use Editor API for active file edits | Preserves cursor position |
| 15 | Use `Vault.process()` for background file mods | Prevents conflicts |
| 16 | Use `normalizePath()` for user paths | Cross-platform compatibility |
| 17 | Use Platform API for OS detection | Not navigator |
| 18 | Use `requestUrl()` instead of `fetch()` | Bypasses CORS restrictions |
| 19 | No `console.log` in `onload`/`onunload` in production | Pollutes console |

### Styling

| # | Rule | Why |
|---|------|-----|
| 20 | Use Obsidian CSS variables | Respects user themes |
| 21 | Scope CSS to plugin containers | Prevents style conflicts |

### Accessibility (mandatory)

| # | Rule | Why |
|---|------|-----|
| 22 | Make all interactive elements keyboard accessible | Required |
| 23 | Provide ARIA labels for icon buttons | Required |
| 24 | Define clear focus indicators | Use `:focus-visible` |

### Security and compatibility

| # | Rule | Why |
|---|------|-----|
| 25 | Don't use `innerHTML`/`outerHTML` | Security risk (XSS) |
| 26 | Avoid regex lookbehind | iOS < 16.4 incompatibility |

### Code quality

| # | Rule | Why |
|---|------|-----|
| 27 | Remove all sample/template code | MyPlugin, SampleModal, etc. |

## Reference files

Detailed guidelines organized by topic:

| File | Topics covered |
|------|---------------|
| [Memory management and lifecycle](references/memory-lifecycle.md) | `registerEvent()`, `addCommand()`, `registerDomEvent()`, `registerInterval()`, view references, leaf cleanup |
| [Type safety](references/type-safety.md) | `instanceof` usage, avoiding `any`, `const`/`let` over `var` |
| [UI/UX standards](references/ui-ux.md) | Sentence case, command naming, settings best practices |
| [File and vault operations](references/file-vault-operations.md) | View access, Editor vs Vault API, atomic operations, path handling |
| [CSS styling](references/css-styling.md) | CSS variables, scoping, theme support, spacing |
| [Accessibility](references/accessibility.md) | Keyboard nav, ARIA, focus management, mobile/touch, screen readers |
| [Code quality](references/code-quality.md) | Security, platform compatibility, async patterns, DOM helpers |
| [Submission requirements](references/submission.md) | Repository structure, versioning, testing checklist |
| [Common patterns](examples/common-patterns.md) | Code examples for common tasks |

## Essential do's and don'ts

### Do

**Memory and lifecycle:**
- Use `registerEvent()`, `addCommand()`, `registerDomEvent()`, `registerInterval()`
- Return views/components directly (don't store unnecessarily)

**Type safety:**
- Use `instanceof` for type checking (not type casting)
- Use specific types or `unknown` instead of `any`
- Use `const` and `let` (not `var`)

**API usage:**
- Use `this.app` (not global `app`)
- Use Editor API for active file edits
- Use `Vault.process()` for background file modifications
- Use `FileManager.processFrontMatter()` for YAML
- Use `fileManager.trashFile()` for deletions
- Use `normalizePath()` for user-defined paths
- Use Platform API for OS detection
- Use `AbstractInputSuggest` for autocomplete
- Use direct file lookups (not vault iteration)
- Use `requestUrl()` instead of `fetch()` for network requests

**UI/UX:**
- Use sentence case for all UI text
- Use `.setHeading()` for settings headings
- Use Obsidian DOM helpers (`createDiv()`, `createSpan()`, `createEl()`)
- Use `window.setTimeout`/`setInterval` with `number` type

**Styling:**
- Move all styles to CSS
- Use Obsidian CSS variables for all styling
- Scope CSS to plugin containers
- Support both light and dark themes via CSS variables
- Follow Obsidian's 4px spacing grid

**Accessibility (mandatory):**
- Make all interactive elements keyboard accessible
- Provide ARIA labels for icon buttons
- Define clear focus indicators using `:focus-visible`
- Use `data-tooltip-position` for tooltips
- Ensure minimum touch target size (44x44px)
- Manage focus properly in modals
- Test with keyboard navigation

**Code quality:**
- Use `async`/`await` (not Promise chains)
- Remove all sample/template code
- Test on mobile (if not desktop-only)
- Follow semantic versioning
- Minimize console logging

### Don't

**Memory and lifecycle:**
- Don't store view references in plugin properties
- Don't pass plugin as component to `MarkdownRenderer`
- Don't detach leaves in `onunload()`

**Type safety:**
- Don't cast to `TFile`/`TFolder` (use `instanceof`)
- Don't use `any` type
- Don't use `var`

**API usage:**
- Don't use global `app` object
- Don't use `Vault.modify()` for active file edits
- Don't hardcode `.obsidian` path (use `vault.configDir`)
- Don't use `navigator.platform`/`userAgent` (use Platform API)
- Don't iterate vault when direct lookup exists
- Don't use `fetch()` (use `requestUrl()` instead)

**UI/UX:**
- Don't use Title Case in UI (use sentence case)
- Don't include "command" in command names/IDs
- Don't duplicate plugin ID in command IDs
- Don't set default hotkeys
- Don't create manual HTML headings (use `.setHeading()`)
- Don't use "General", "settings", or plugin name in settings headings

**Styling:**
- Don't assign styles via JavaScript
- Don't hardcode colors, sizes, or spacing (use CSS variables)
- Don't use broad CSS selectors (scope to plugin)
- Don't manually switch themes (CSS variables adapt automatically)
- Don't create `<link>` or `<style>` elements (use `styles.css` file)

**Security and compatibility:**
- Don't use `innerHTML`/`outerHTML` (XSS risk)
- Don't use regex lookbehind (iOS < 16.4 incompatibility)

**Accessibility:**
- Don't create inaccessible interactive elements
- Don't use icon buttons without ARIA labels
- Don't remove focus indicators without alternatives
- Don't make touch targets smaller than 44x44px

**Code quality:**
- Don't use Promise chains (use `async`/`await`)
- Don't use `document.createElement` (use Obsidian helpers)
- Don't keep sample class names (MyPlugin, SampleModal, etc.)
- Don't use `console.log` in `onload`/`onunload`

## Code review checklist

Use this when reviewing or writing code:

- [ ] Memory management: Are components and views properly managed?
- [ ] Type safety: Using `instanceof` instead of casts?
- [ ] UI text: Is everything in sentence case?
- [ ] Command naming: No redundant words?
- [ ] File operations: Using preferred APIs?
- [ ] Mobile compatibility: No iOS-incompatible features?
- [ ] Sample code: Removed all boilerplate?
- [ ] Manifest: Correct version, valid structure?
- [ ] Accessibility: Keyboard navigation, ARIA labels, focus indicators?
- [ ] Testing: Can you use the plugin without a mouse?
- [ ] Touch targets: Are all interactive elements at least 44x44px?
- [ ] Focus styles: Using `:focus-visible` and proper CSS variables?

## Additional resources

- **ESLint Plugin**: [eslint-plugin-obsidianmd](https://www.npmjs.com/package/eslint-plugin-obsidianmd) (install for automatic checking)
- **Obsidian API Docs**: https://docs.obsidian.md
- **Sample Plugin**: https://github.com/obsidianmd/obsidian-sample-plugin
- **Community**: Obsidian Discord, Forum
