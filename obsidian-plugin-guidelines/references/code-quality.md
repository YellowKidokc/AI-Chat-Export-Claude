# Code Quality and Best Practices

Standards for security, platform compatibility, async patterns, and API usage in Obsidian plugins.

## Security

### Don't use innerHTML or outerHTML

Using `innerHTML` or `outerHTML` with user-provided or external data creates XSS vulnerabilities. Use Obsidian's DOM helpers or `textContent` instead.

```typescript
// WRONG - XSS risk
element.innerHTML = `<span>${userInput}</span>`;

// WRONG - XSS risk
element.outerHTML = `<div class="wrapper">${content}</div>`;

// CORRECT - safe text content
element.textContent = userInput;

// CORRECT - Obsidian helpers
const span = element.createSpan({ text: userInput });

// CORRECT - for complex HTML, use DOM APIs
const wrapper = element.createDiv({ cls: 'wrapper' });
wrapper.createSpan({ text: content });
```

### Sanitize external data

When displaying data from external sources (APIs, files, user input), always treat it as untrusted:

```typescript
// CORRECT - use textContent for user data
const title = containerEl.createEl('h3');
title.textContent = externalData.title;

// CORRECT - use Obsidian helpers
containerEl.createSpan({ text: externalData.description });
```

## Platform compatibility

### Don't use regex lookbehind

Regex lookbehind assertions (`(?<=...)` and `(?<!...)`) are not supported on iOS Safari versions below 16.4. This causes crashes on older iPhones and iPads.

```typescript
// WRONG - breaks on iOS < 16.4
const result = text.match(/(?<=@)\w+/);
const result = text.replace(/(?<!\\)#/g, '');

// CORRECT - use capture groups instead
const match = text.match(/@(\w+)/);
const result = match ? match[1] : null;

// CORRECT - use alternative patterns
const result = text.replace(/(^|[^\\])#/g, '$1');
```

### Use Platform API for OS detection

Obsidian provides a Platform API that works correctly across all platforms, including mobile.

```typescript
import { Platform } from 'obsidian';

// CORRECT
if (Platform.isMobile) {
  // Mobile-specific behavior
}

if (Platform.isDesktop) {
  // Desktop-specific behavior
}

if (Platform.isMacOS) {
  // macOS-specific behavior
}

if (Platform.isWin) {
  // Windows-specific behavior
}

// WRONG - doesn't work reliably, especially on mobile
if (navigator.platform.includes('Mac')) { }
if (navigator.userAgent.includes('Windows')) { }
```

### Use requestUrl() instead of fetch()

Obsidian's `requestUrl()` function bypasses CORS restrictions that would otherwise prevent plugins from making HTTP requests. Standard `fetch()` calls may fail due to CORS policies.

```typescript
import { requestUrl } from 'obsidian';

// CORRECT
const response = await requestUrl({
  url: 'https://api.example.com/data',
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const data = response.json;

// CORRECT - POST request
const response = await requestUrl({
  url: 'https://api.example.com/submit',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ key: 'value' })
});

// WRONG - may fail due to CORS
const response = await fetch('https://api.example.com/data');
```

## Async/await patterns

### Use async/await instead of Promise chains

`async`/`await` is easier to read, debug, and handle errors with.

```typescript
// CORRECT
async function processFiles(files: TFile[]) {
  const results: string[] = [];
  for (const file of files) {
    try {
      const content = await this.app.vault.read(file);
      results.push(content);
    } catch (e) {
      console.error(`Failed to read ${file.path}:`, e);
    }
  }
  return results;
}

// WRONG - Promise chains
function processFiles(files: TFile[]) {
  return Promise.all(
    files.map(file =>
      this.app.vault.read(file)
        .then(content => content)
        .catch(e => {
          console.error(`Failed to read ${file.path}:`, e);
          return null;
        })
    )
  );
}
```

### Handle errors properly

```typescript
// CORRECT - specific error handling
async onload() {
  try {
    this.settings = await this.loadSettings();
  } catch (e) {
    console.error('Failed to load settings, using defaults:', e);
    this.settings = { ...DEFAULT_SETTINGS };
  }
}

// CORRECT - user-facing error
async exportFile(file: TFile) {
  try {
    const content = await this.app.vault.read(file);
    await this.writeExport(content);
    new Notice('Export complete.');
  } catch (e) {
    new Notice('Export failed. Check the console for details.');
    console.error('Export failed:', e);
  }
}
```

## API usage

### Use this.app, not global app

The global `app` variable is available in Obsidian but using it creates tight coupling and makes code harder to test.

```typescript
// CORRECT
export default class MyPlugin extends Plugin {
  async onload() {
    const file = this.app.vault.getAbstractFileByPath('test.md');
  }
}

// WRONG
export default class MyPlugin extends Plugin {
  async onload() {
    const file = app.vault.getAbstractFileByPath('test.md');
  }
}
```

### Use AbstractInputSuggest for autocomplete

Obsidian provides `AbstractInputSuggest` for building autocomplete dropdowns. Don't build your own.

```typescript
import { AbstractInputSuggest, TFile } from 'obsidian';

class FileSuggest extends AbstractInputSuggest<TFile> {
  getSuggestions(query: string): TFile[] {
    return this.app.vault.getMarkdownFiles()
      .filter(file => file.path.toLowerCase().includes(query.toLowerCase()));
  }

  renderSuggestion(file: TFile, el: HTMLElement): void {
    el.setText(file.path);
  }

  selectSuggestion(file: TFile): void {
    this.inputEl.value = file.path;
    this.inputEl.trigger('input');
    this.close();
  }
}
```

## Console logging

### No console.log in onload/onunload

Console messages during plugin load/unload pollute the console for every user on every vault open. Only use console logging for errors and debugging that users can opt into.

```typescript
// WRONG
async onload() {
  console.log('My plugin loaded!');
}

async onunload() {
  console.log('My plugin unloaded!');
}

// CORRECT - no logging on load/unload
async onload() {
  // silently initialize
  this.settings = await this.loadSettings();
  this.addSettingTab(new MySettingTab(this.app, this));
}

// CORRECT - log errors when they happen
async processFile(file: TFile) {
  try {
    // ...
  } catch (e) {
    console.error('Failed to process file:', e);
  }
}
```

## DOM helpers

Use Obsidian's built-in DOM helpers instead of standard DOM APIs:

```typescript
// CORRECT - Obsidian helpers
const div = containerEl.createDiv({ cls: 'my-plugin-wrapper' });
const span = div.createSpan({ text: 'Hello' });
const heading = div.createEl('h3', { text: 'Section', cls: 'my-plugin-heading' });
const link = div.createEl('a', {
  text: 'Click here',
  href: 'https://example.com',
  attr: { target: '_blank' }
});

// Clear children
containerEl.empty();

// WRONG - standard DOM APIs
const div = document.createElement('div');
div.className = 'my-plugin-wrapper';
containerEl.appendChild(div);
```

## Remove sample/template code

Before submitting, remove all boilerplate from the sample plugin:

- `MyPlugin` class name (use a descriptive name)
- `SampleModal` class name
- `SampleSettingTab` class name
- `MyPluginSettings` interface name
- Sample commands (like "Open sample modal")
- Sample settings (like "mySetting")
- Template comments (like "// Remember to rename these classes")

```typescript
// WRONG - sample code still present
interface MyPluginSettings {
  mySetting: string;
}

export default class MyPlugin extends Plugin {
  // ...
}

class SampleModal extends Modal {
  // ...
}

// CORRECT - renamed to match your plugin
interface TimestampSettings {
  dateFormat: string;
}

export default class TimestampPlugin extends Plugin {
  // ...
}

class FormatPickerModal extends Modal {
  // ...
}
```
