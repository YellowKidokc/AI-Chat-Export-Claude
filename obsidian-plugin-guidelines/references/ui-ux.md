# UI/UX Standards

Consistent UI and UX patterns make plugins feel native to Obsidian and reduce user confusion.

## Sentence case for all UI text

Use sentence case (capitalize only the first word and proper nouns) for all user-facing text: commands, settings, headings, buttons, notices, and tooltips.

```typescript
// CORRECT
this.addCommand({
  id: 'open-daily-note',
  name: 'Open daily note',
});

// WRONG - Title Case
this.addCommand({
  id: 'open-daily-note',
  name: 'Open Daily Note',
});
```

Examples:
- "Advanced settings" not "Advanced Settings"
- "Export as PDF" not "Export As PDF"
- "Toggle sidebar" not "Toggle Sidebar"
- "Show line numbers" not "Show Line Numbers"

## Command naming

### No "command" in names or IDs

Obsidian already displays commands in the command palette. Including "command" is redundant.

```typescript
// CORRECT
{ id: 'insert-timestamp', name: 'Insert timestamp' }

// WRONG
{ id: 'insert-timestamp-command', name: 'Insert timestamp command' }
```

### No plugin ID in command IDs

Obsidian automatically namespaces command IDs with the plugin ID. Including it manually creates duplication like `my-plugin:my-plugin-do-thing`.

```typescript
// CORRECT - Obsidian creates "my-plugin:insert-timestamp"
{ id: 'insert-timestamp', name: 'Insert timestamp' }

// WRONG - results in "my-plugin:my-plugin-insert-timestamp"
{ id: 'my-plugin-insert-timestamp', name: 'Insert timestamp' }
```

### No default hotkeys

Setting default hotkeys risks conflicting with other plugins or the user's custom bindings. Let users configure their own hotkeys.

```typescript
// CORRECT
this.addCommand({
  id: 'do-thing',
  name: 'Do thing',
  callback: () => this.doThing(),
});

// WRONG - don't set default hotkeys
this.addCommand({
  id: 'do-thing',
  name: 'Do thing',
  hotkeys: [{ modifiers: ['Ctrl'], key: 'T' }],
  callback: () => this.doThing(),
});
```

## Settings best practices

### Use .setHeading() for section headings

Obsidian provides a dedicated API for settings section headings. Don't create manual HTML headings.

```typescript
// CORRECT
new Setting(containerEl).setName('Appearance').setHeading();

new Setting(containerEl)
  .setName('Theme color')
  .setDesc('Choose the accent color for the plugin.')
  .addColorPicker((cp) =>
    cp.setValue(this.plugin.settings.color).onChange(async (value) => {
      this.plugin.settings.color = value;
      await this.plugin.saveSettings();
    })
  );

// WRONG - manual HTML heading
containerEl.createEl('h2', { text: 'Appearance' });
```

### Don't use generic heading names

Avoid headings like "General", "Settings", or the plugin name. These add no information.

```typescript
// CORRECT - descriptive section names
new Setting(containerEl).setName('Appearance').setHeading();
new Setting(containerEl).setName('Behavior').setHeading();
new Setting(containerEl).setName('Export options').setHeading();

// WRONG - uninformative
new Setting(containerEl).setName('General').setHeading();
new Setting(containerEl).setName('Settings').setHeading();
new Setting(containerEl).setName('My Plugin').setHeading();
```

### Provide descriptions for settings

Use `.setDesc()` to explain what each setting does. Users shouldn't have to guess.

```typescript
new Setting(containerEl)
  .setName('Auto-save interval')
  .setDesc('How often to automatically save changes, in seconds. Set to 0 to disable.')
  .addText((text) =>
    text
      .setPlaceholder('30')
      .setValue(String(this.plugin.settings.autoSaveInterval))
      .onChange(async (value) => {
        const num = parseInt(value, 10);
        if (!isNaN(num) && num >= 0) {
          this.plugin.settings.autoSaveInterval = num;
          await this.plugin.saveSettings();
        }
      })
  );
```

## Notices

Use `Notice` for user-facing messages. Keep them concise.

```typescript
// CORRECT
new Notice('File exported successfully.');
new Notice('Could not find the template file.');

// WRONG - too verbose
new Notice('The export operation has been completed successfully and the file has been saved to your designated output directory.');
```

## Modal best practices

- Set focus to the first interactive element when the modal opens
- Allow closing with Escape (this is default behavior)
- Keep modals focused on a single task
- Use `contentEl` for content, not `modalEl`

```typescript
export class MyModal extends Modal {
  onOpen() {
    const { contentEl } = this;
    contentEl.empty();

    contentEl.createEl('p', { text: 'Enter a value:' });

    const input = new TextComponent(contentEl);
    input.inputEl.focus();

    new Setting(contentEl)
      .addButton((btn) =>
        btn
          .setButtonText('Confirm')
          .setCta()
          .onClick(() => {
            this.handleConfirm(input.getValue());
            this.close();
          })
      );
  }

  onClose() {
    this.contentEl.empty();
  }
}
```

## DOM helpers

Use Obsidian's built-in DOM creation helpers instead of `document.createElement`:

```typescript
// CORRECT
const wrapper = containerEl.createDiv({ cls: 'my-plugin-wrapper' });
const label = wrapper.createSpan({ text: 'Status:', cls: 'my-plugin-label' });
const icon = wrapper.createEl('button', {
  attr: { 'aria-label': 'Refresh' },
  cls: 'my-plugin-refresh-btn'
});

// WRONG
const wrapper = document.createElement('div');
wrapper.className = 'my-plugin-wrapper';
containerEl.appendChild(wrapper);
```

Available helpers:
- `createDiv({ cls?, text?, attr? })`
- `createSpan({ cls?, text?, attr? })`
- `createEl(tag, { cls?, text?, attr? })`
- `empty()` - removes all children
