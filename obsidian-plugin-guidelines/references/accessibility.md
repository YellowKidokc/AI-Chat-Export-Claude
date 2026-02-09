# Accessibility (A11y)

Accessibility is **mandatory** for Obsidian plugins. All interactive elements must be usable with keyboard, screen readers, and touch devices. This is not optional.

## Keyboard navigation

Every interactive element must be operable with keyboard alone. Users who rely on keyboard navigation or assistive technology must be able to use all plugin features.

### Make all interactive elements keyboard accessible

```typescript
// CORRECT - button element is natively keyboard accessible
const button = containerEl.createEl('button', {
  text: 'Save',
  cls: 'my-plugin-save-btn'
});
button.addEventListener('click', () => this.save());

// CORRECT - if using a non-button element, add keyboard support
const item = containerEl.createDiv({ cls: 'my-plugin-item' });
item.setAttribute('tabindex', '0');
item.setAttribute('role', 'button');
item.addEventListener('click', () => this.selectItem());
item.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    this.selectItem();
  }
});

// WRONG - div with click handler but no keyboard support
const item = containerEl.createDiv({ cls: 'my-plugin-item' });
item.addEventListener('click', () => this.selectItem());
```

### Keyboard patterns for common widgets

| Widget | Keys |
|--------|------|
| Button | Enter, Space |
| Link | Enter |
| List navigation | Arrow Up/Down |
| Tab switching | Arrow Left/Right |
| Modal dismiss | Escape |
| Dropdown | Arrow Up/Down, Enter, Escape |
| Checkbox | Space |

## ARIA labels

Provide ARIA labels for all elements that don't have visible text content, especially icon-only buttons.

```typescript
// CORRECT
const button = containerEl.createEl('button', {
  attr: {
    'aria-label': 'Open settings',
    'data-tooltip-position': 'top'
  },
  cls: 'my-plugin-settings-btn'
});
setIcon(button, 'settings');

// WRONG - icon button with no label
const button = containerEl.createEl('button', {
  cls: 'my-plugin-settings-btn'
});
setIcon(button, 'settings');
// Screen reader says: "button" - user has no idea what it does
```

### ARIA roles

Use appropriate ARIA roles when semantic HTML isn't sufficient:

```typescript
// List
const list = containerEl.createDiv({ attr: { role: 'list' } });
const item = list.createDiv({
  attr: {
    role: 'listitem',
    'aria-label': 'File: notes.md'
  }
});

// Status message
const status = containerEl.createDiv({
  attr: {
    role: 'status',
    'aria-live': 'polite'
  }
});
status.setText('3 files processed');
```

## Focus management

### Focus indicators

Every focusable element must have a visible focus indicator. Use `:focus-visible` to show indicators only for keyboard navigation (not mouse clicks).

```css
/* CORRECT */
.my-plugin-button:focus-visible {
  outline: 2px solid var(--interactive-accent);
  outline-offset: 2px;
}

.my-plugin-item:focus-visible {
  box-shadow: 0 0 0 2px var(--interactive-accent);
  border-radius: var(--radius-s);
}

/* WRONG - removes focus indicator entirely */
.my-plugin-button:focus {
  outline: none;
}

/* WRONG - shows focus ring on mouse click too */
.my-plugin-button:focus {
  outline: 2px solid blue;
}
```

### Modal focus management

When opening a modal, focus should move to the modal and be trapped inside it. When closing, focus should return to the trigger element.

```typescript
export class MyModal extends Modal {
  private triggerEl: HTMLElement;

  constructor(app: App, triggerEl: HTMLElement) {
    super(app);
    this.triggerEl = triggerEl;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();

    const input = new TextComponent(contentEl);
    // Focus first interactive element
    input.inputEl.focus();
  }

  onClose() {
    this.contentEl.empty();
    // Return focus to trigger
    this.triggerEl.focus();
  }
}
```

### Focus order

Ensure interactive elements appear in a logical tab order that matches the visual layout. Don't use `tabindex` values greater than 0.

```typescript
// CORRECT - use tabindex="0" to add to natural tab order
element.setAttribute('tabindex', '0');

// WRONG - positive tabindex disrupts natural order
element.setAttribute('tabindex', '5');
```

## Tooltips

Use Obsidian's tooltip system via `data-tooltip-position` attribute combined with `aria-label`.

```typescript
// CORRECT
const button = containerEl.createEl('button', {
  attr: {
    'aria-label': 'Copy to clipboard',
    'data-tooltip-position': 'top'
  }
});

// Tooltip positions: 'top', 'bottom', 'left', 'right'
```

## Screen reader support

### Live regions

Use ARIA live regions for dynamic content updates that screen readers should announce.

```typescript
// Status updates
const statusEl = containerEl.createDiv({
  attr: {
    role: 'status',
    'aria-live': 'polite'
  }
});

// Update later - screen reader announces the change
statusEl.setText('Export complete: 15 files processed');

// For urgent updates
const alertEl = containerEl.createDiv({
  attr: {
    role: 'alert',
    'aria-live': 'assertive'
  }
});
alertEl.setText('Error: File not found');
```

### Hidden text for screen readers

When visual context makes something clear but screen readers need more info:

```css
.my-plugin-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

```typescript
const srText = button.createSpan({ cls: 'my-plugin-sr-only' });
srText.setText('Opens in new window');
```

## Mobile and touch accessibility

### Minimum touch target size

All interactive elements must be at least 44x44 CSS pixels for comfortable touch interaction.

```css
/* CORRECT */
.my-plugin-button {
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.my-plugin-list-item {
  min-height: 44px;
  padding: var(--size-4-2) var(--size-4-3);
}

/* WRONG - too small for touch */
.my-plugin-button {
  width: 24px;
  height: 24px;
}
```

### Touch-friendly spacing

Ensure adequate spacing between touch targets to prevent accidental taps:

```css
.my-plugin-action-bar {
  display: flex;
  gap: var(--size-4-2); /* 8px minimum between touch targets */
}
```

## Accessibility checklist

Use this checklist when reviewing plugin accessibility:

- [ ] All interactive elements are reachable via Tab key
- [ ] All interactive elements can be activated via keyboard (Enter/Space)
- [ ] Icon-only buttons have `aria-label` attributes
- [ ] Focus indicators are visible using `:focus-visible`
- [ ] Modals trap focus and return it on close
- [ ] Dynamic content uses `aria-live` regions
- [ ] Touch targets are at least 44x44px
- [ ] Color is not the only way to convey information
- [ ] All text has sufficient contrast (use CSS variables to ensure this)
- [ ] Lists use proper `role="list"` and `role="listitem"`
- [ ] Custom widgets follow WAI-ARIA patterns
- [ ] The plugin is fully usable without a mouse
