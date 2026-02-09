# CSS Styling Best Practices

Obsidian plugins should use Obsidian's CSS variable system and properly scope their styles to avoid conflicts with other plugins and themes.

## Use a styles.css file

All plugin styles belong in a `styles.css` file at the root of the plugin. Obsidian automatically loads this file. Never create `<style>` or `<link>` elements manually.

```typescript
// WRONG - creating style elements
const style = document.createElement('style');
style.textContent = '.my-class { color: red; }';
document.head.appendChild(style);

// WRONG - creating link elements
const link = document.createElement('link');
link.rel = 'stylesheet';
link.href = 'styles.css';
document.head.appendChild(link);

// CORRECT - just put styles in styles.css, Obsidian loads it automatically
```

## Use Obsidian CSS variables

Obsidian provides a comprehensive set of CSS variables that automatically adapt to the user's theme, whether light or dark. Hardcoding colors, sizes, or fonts breaks theme compatibility.

### Colors

```css
/* CORRECT */
.my-plugin-container {
  color: var(--text-normal);
  background: var(--background-primary);
  border: 1px solid var(--background-modifier-border);
}

.my-plugin-muted {
  color: var(--text-muted);
}

.my-plugin-accent {
  color: var(--interactive-accent);
}

/* WRONG */
.my-plugin-container {
  color: #333;
  background: white;
  border: 1px solid #ddd;
}
```

### Common color variables

| Variable | Use case |
|----------|----------|
| `--text-normal` | Primary text |
| `--text-muted` | Secondary/dimmed text |
| `--text-faint` | Tertiary/very dim text |
| `--text-accent` | Accent-colored text |
| `--text-on-accent` | Text on accent backgrounds |
| `--background-primary` | Main background |
| `--background-secondary` | Sidebar/secondary areas |
| `--background-modifier-border` | Borders |
| `--background-modifier-hover` | Hover states |
| `--background-modifier-active-hover` | Active hover states |
| `--interactive-accent` | Interactive accent (buttons, links) |
| `--interactive-accent-hover` | Interactive accent on hover |

### Typography

```css
/* CORRECT */
.my-plugin-text {
  font-size: var(--font-ui-medium);
  font-family: var(--font-interface);
}

.my-plugin-code {
  font-family: var(--font-monospace);
  font-size: var(--font-ui-small);
}

/* WRONG */
.my-plugin-text {
  font-size: 14px;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}
```

### Common typography variables

| Variable | Use case |
|----------|----------|
| `--font-interface` | UI text |
| `--font-text` | Content/note text |
| `--font-monospace` | Code |
| `--font-ui-smaller` | Small UI text |
| `--font-ui-small` | Standard small text |
| `--font-ui-medium` | Standard medium text |
| `--font-ui-large` | Large UI text |

### Spacing

Follow Obsidian's 4px spacing grid using size variables:

```css
/* CORRECT */
.my-plugin-item {
  padding: var(--size-4-2); /* 8px */
  margin-bottom: var(--size-4-3); /* 12px */
  gap: var(--size-4-4); /* 16px */
}

/* WRONG */
.my-plugin-item {
  padding: 7px;
  margin-bottom: 13px;
  gap: 15px;
}
```

### Common size variables

| Variable | Value |
|----------|-------|
| `--size-4-1` | 4px |
| `--size-4-2` | 8px |
| `--size-4-3` | 12px |
| `--size-4-4` | 16px |
| `--size-4-5` | 20px |
| `--size-4-6` | 24px |
| `--size-4-8` | 32px |
| `--size-4-12` | 48px |

### Border radius

```css
/* CORRECT */
.my-plugin-card {
  border-radius: var(--radius-m);
}

.my-plugin-pill {
  border-radius: var(--radius-xl);
}

/* WRONG */
.my-plugin-card {
  border-radius: 4px;
}
```

| Variable | Use case |
|----------|----------|
| `--radius-s` | Small elements |
| `--radius-m` | Cards, containers |
| `--radius-l` | Large containers |
| `--radius-xl` | Pills, tags |

## Scope CSS to plugin containers

Always prefix CSS selectors with a plugin-specific class to avoid affecting other plugins or Obsidian's core UI.

```css
/* CORRECT - scoped to plugin */
.my-plugin-container .item {
  display: flex;
  align-items: center;
}

.my-plugin-modal .header {
  font-weight: var(--font-weight-bold);
}

/* WRONG - too broad, affects everything */
.item {
  display: flex;
  align-items: center;
}

.header {
  font-weight: bold;
}
```

## Don't assign styles via JavaScript

Move all styling to CSS. Inline styles via JavaScript make theming impossible and are harder to maintain.

```typescript
// WRONG
const el = containerEl.createDiv();
el.style.color = 'red';
el.style.padding = '8px';
el.style.backgroundColor = '#f0f0f0';

// CORRECT
const el = containerEl.createDiv({ cls: 'my-plugin-highlight' });
```

```css
/* In styles.css */
.my-plugin-highlight {
  color: var(--text-accent);
  padding: var(--size-4-2);
  background-color: var(--background-secondary);
}
```

## Don't manually switch themes

CSS variables automatically adapt when the user switches between light and dark themes. Never try to detect or manually handle theme switching.

```css
/* WRONG - manual theme handling */
.theme-dark .my-plugin-box {
  background: #1e1e1e;
}
.theme-light .my-plugin-box {
  background: #ffffff;
}

/* CORRECT - CSS variables handle it */
.my-plugin-box {
  background: var(--background-primary);
}
```

## Focus and interaction styles

```css
/* Focus indicator (mandatory for accessibility) */
.my-plugin-button:focus-visible {
  outline: 2px solid var(--interactive-accent);
  outline-offset: 2px;
}

/* Hover state */
.my-plugin-item:hover {
  background: var(--background-modifier-hover);
}

/* Active state */
.my-plugin-item:active,
.my-plugin-item.is-active {
  background: var(--background-modifier-active-hover);
}

/* Disabled state */
.my-plugin-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

## Modal styling

```css
.my-plugin-modal {
  background: var(--modal-background);
  color: var(--text-normal);
  padding: var(--size-4-4);
  border-radius: var(--radius-m);
}

.my-plugin-modal .modal-title {
  font-size: var(--font-ui-large);
  font-weight: var(--font-weight-bold);
  margin-bottom: var(--size-4-3);
}
```
