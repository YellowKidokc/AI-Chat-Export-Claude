# Common Patterns

Practical code examples for common Obsidian plugin tasks, following all guidelines.

## Plugin with settings

The most common plugin structure: a main plugin class with settings and a settings tab.

```typescript
import {
  App, Editor, MarkdownView, Notice, Plugin,
  PluginSettingTab, Setting, TFile, normalizePath
} from 'obsidian';

interface TimestampSettings {
  dateFormat: string;
  showNotice: boolean;
}

const DEFAULT_SETTINGS: TimestampSettings = {
  dateFormat: 'YYYY-MM-DD HH:mm',
  showNotice: true,
};

export default class TimestampPlugin extends Plugin {
  settings: TimestampSettings;

  async onload() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());

    this.addCommand({
      id: 'insert-timestamp',
      name: 'Insert timestamp',
      editorCallback: (editor: Editor) => {
        const timestamp = new Date().toISOString();
        editor.replaceSelection(timestamp);
        if (this.settings.showNotice) {
          new Notice('Timestamp inserted.');
        }
      },
    });

    this.addSettingTab(new TimestampSettingTab(this.app, this));
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
}

class TimestampSettingTab extends PluginSettingTab {
  plugin: TimestampPlugin;

  constructor(app: App, plugin: TimestampPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    new Setting(containerEl)
      .setName('Date format')
      .setDesc('Format string for inserted timestamps.')
      .addText((text) =>
        text
          .setPlaceholder('YYYY-MM-DD HH:mm')
          .setValue(this.plugin.settings.dateFormat)
          .onChange(async (value) => {
            this.plugin.settings.dateFormat = value;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName('Show notice')
      .setDesc('Display a notice after inserting a timestamp.')
      .addToggle((toggle) =>
        toggle
          .setValue(this.plugin.settings.showNotice)
          .onChange(async (value) => {
            this.plugin.settings.showNotice = value;
            await this.plugin.saveSettings();
          })
      );
  }
}
```

## Proper command registration

```typescript
// Editor command - only available when an editor is active
this.addCommand({
  id: 'wrap-selection-bold',
  name: 'Wrap selection in bold',
  editorCallback: (editor: Editor) => {
    const selection = editor.getSelection();
    editor.replaceSelection(`**${selection}**`);
  },
});

// Check callback - conditionally available
this.addCommand({
  id: 'process-current-file',
  name: 'Process current file',
  checkCallback: (checking: boolean) => {
    const file = this.app.workspace.getActiveFile();
    if (file && file.extension === 'md') {
      if (!checking) {
        this.processFile(file);
      }
      return true;
    }
    return false;
  },
});

// Simple callback - always available
this.addCommand({
  id: 'open-dashboard',
  name: 'Open dashboard',
  callback: () => {
    this.activateView();
  },
});
```

## Safe file type narrowing

```typescript
// Get a file and check its type
const abstractFile = this.app.vault.getAbstractFileByPath(userPath);

if (!abstractFile) {
  new Notice('File not found.');
  return;
}

if (abstractFile instanceof TFile) {
  const content = await this.app.vault.read(abstractFile);
  // Process file content...
}

if (abstractFile instanceof TFolder) {
  for (const child of abstractFile.children) {
    if (child instanceof TFile && child.extension === 'md') {
      // Process markdown files in folder...
    }
  }
}
```

## Event handling with automatic cleanup

```typescript
async onload() {
  // Vault events
  this.registerEvent(
    this.app.vault.on('create', (file) => {
      if (file instanceof TFile) {
        this.handleFileCreated(file);
      }
    })
  );

  this.registerEvent(
    this.app.vault.on('modify', (file) => {
      if (file instanceof TFile) {
        this.handleFileModified(file);
      }
    })
  );

  this.registerEvent(
    this.app.vault.on('delete', (file) => {
      if (file instanceof TFile) {
        this.handleFileDeleted(file);
      }
    })
  );

  this.registerEvent(
    this.app.vault.on('rename', (file, oldPath) => {
      if (file instanceof TFile) {
        this.handleFileRenamed(file, oldPath);
      }
    })
  );

  // Workspace events
  this.registerEvent(
    this.app.workspace.on('file-open', (file) => {
      if (file) {
        this.handleFileOpened(file);
      }
    })
  );

  this.registerEvent(
    this.app.workspace.on('active-leaf-change', (leaf) => {
      if (leaf) {
        this.handleLeafChange(leaf);
      }
    })
  );

  // DOM events
  this.registerDomEvent(document, 'keydown', (evt: KeyboardEvent) => {
    if (evt.key === 'Escape') {
      this.handleEscape();
    }
  });

  // Periodic tasks
  this.registerInterval(
    window.setInterval(() => this.periodicCheck(), 60000)
  );
}
```

## Atomic file modification

```typescript
// Background modification using Vault.process()
async addTagToFile(file: TFile, tag: string) {
  await this.app.vault.process(file, (content) => {
    // Add tag to the end of frontmatter
    if (content.startsWith('---')) {
      const endIndex = content.indexOf('---', 3);
      if (endIndex !== -1) {
        const frontmatter = content.slice(0, endIndex);
        const rest = content.slice(endIndex);
        return `${frontmatter}tags:\n  - ${tag}\n${rest}`;
      }
    }
    return content;
  });
}

// Better: use processFrontMatter for YAML operations
async addTagWithApi(file: TFile, tag: string) {
  await this.app.fileManager.processFrontMatter(file, (fm) => {
    if (!fm.tags) {
      fm.tags = [];
    }
    if (!fm.tags.includes(tag)) {
      fm.tags.push(tag);
    }
  });
}
```

## Custom view

```typescript
import { ItemView, WorkspaceLeaf } from 'obsidian';

const VIEW_TYPE = 'my-dashboard';

class DashboardView extends ItemView {
  getViewType(): string {
    return VIEW_TYPE;
  }

  getDisplayText(): string {
    return 'Dashboard';
  }

  getIcon(): string {
    return 'layout-dashboard';
  }

  async onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass('my-plugin-dashboard');

    const header = contentEl.createDiv({ cls: 'my-plugin-dashboard-header' });
    header.createEl('h3', { text: 'Dashboard' });

    const refreshBtn = header.createEl('button', {
      attr: {
        'aria-label': 'Refresh dashboard',
        'data-tooltip-position': 'bottom',
      },
      cls: 'my-plugin-refresh-btn',
    });
    refreshBtn.setText('Refresh');
    refreshBtn.addEventListener('click', () => this.refresh());

    const content = contentEl.createDiv({ cls: 'my-plugin-dashboard-content' });
    await this.renderContent(content);
  }

  async onClose() {
    this.contentEl.empty();
  }

  async refresh() {
    const content = this.contentEl.querySelector('.my-plugin-dashboard-content');
    if (content instanceof HTMLElement) {
      content.empty();
      await this.renderContent(content);
    }
  }

  private async renderContent(container: HTMLElement) {
    const files = this.app.vault.getMarkdownFiles();
    const list = container.createDiv({ attr: { role: 'list' } });

    for (const file of files.slice(0, 10)) {
      const item = list.createDiv({
        cls: 'my-plugin-dashboard-item',
        attr: {
          role: 'listitem',
          tabindex: '0',
          'aria-label': file.basename,
        },
      });
      item.createSpan({ text: file.basename });
      item.addEventListener('click', () => {
        this.app.workspace.openLinkText(file.path, '');
      });
      item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.app.workspace.openLinkText(file.path, '');
        }
      });
    }
  }
}

// In your plugin class:
// Register the view
async onload() {
  this.registerView(VIEW_TYPE, (leaf) => new DashboardView(leaf));

  this.addCommand({
    id: 'open-dashboard',
    name: 'Open dashboard',
    callback: () => this.activateView(),
  });
}

async activateView() {
  const { workspace } = this.app;

  let leaf = workspace.getLeavesOfType(VIEW_TYPE)[0];

  if (!leaf) {
    const rightLeaf = workspace.getRightLeaf(false);
    if (rightLeaf) {
      leaf = rightLeaf;
      await leaf.setViewState({ type: VIEW_TYPE, active: true });
    }
  }

  if (leaf) {
    workspace.revealLeaf(leaf);
  }
}
```

## Modal with keyboard support

```typescript
import { App, Modal, Setting, TextComponent } from 'obsidian';

class InputModal extends Modal {
  private result: string;
  private onSubmit: (result: string) => void;
  private triggerEl: HTMLElement;

  constructor(app: App, triggerEl: HTMLElement, onSubmit: (result: string) => void) {
    super(app);
    this.triggerEl = triggerEl;
    this.onSubmit = onSubmit;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass('my-plugin-input-modal');

    contentEl.createEl('p', { text: 'Enter a value:' });

    const input = new TextComponent(contentEl);
    input.setPlaceholder('Type here...');
    input.onChange((value) => (this.result = value));

    // Focus the input
    input.inputEl.focus();

    // Submit on Enter
    input.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        this.submit();
      }
    });

    new Setting(contentEl)
      .addButton((btn) =>
        btn
          .setButtonText('Cancel')
          .onClick(() => this.close())
      )
      .addButton((btn) =>
        btn
          .setButtonText('Submit')
          .setCta()
          .onClick(() => this.submit())
      );
  }

  private submit() {
    this.onSubmit(this.result);
    this.close();
  }

  onClose() {
    this.contentEl.empty();
    // Return focus to trigger element
    this.triggerEl.focus();
  }
}
```

## Ribbon icon with accessibility

```typescript
async onload() {
  const ribbonIcon = this.addRibbonIcon('dice', 'Open random note', () => {
    this.openRandomNote();
  });

  // The addRibbonIcon method already handles aria-label from the tooltip parameter
  // Additional attributes if needed:
  ribbonIcon.setAttribute('data-tooltip-position', 'right');
}

async openRandomNote() {
  const files = this.app.vault.getMarkdownFiles();
  if (files.length === 0) {
    new Notice('No markdown files found.');
    return;
  }
  const randomFile = files[Math.floor(Math.random() * files.length)];
  await this.app.workspace.openLinkText(randomFile.path, '');
}
```

## Status bar item

```typescript
async onload() {
  const statusBarEl = this.addStatusBarItem();
  statusBarEl.setText('Words: 0');
  statusBarEl.addClass('my-plugin-status');

  this.registerEvent(
    this.app.workspace.on('active-leaf-change', async () => {
      await this.updateWordCount(statusBarEl);
    })
  );

  this.registerEvent(
    this.app.workspace.on('editor-change', async () => {
      await this.updateWordCount(statusBarEl);
    })
  );
}

async updateWordCount(statusBarEl: HTMLElement) {
  const file = this.app.workspace.getActiveFile();
  if (!file) {
    statusBarEl.setText('Words: --');
    return;
  }
  const content = await this.app.vault.cachedRead(file);
  const words = content.split(/\s+/).filter((w) => w.length > 0).length;
  statusBarEl.setText(`Words: ${words}`);
}
```

## File suggest in settings

```typescript
import { AbstractInputSuggest, App, TFile } from 'obsidian';

class FileSuggest extends AbstractInputSuggest<TFile> {
  private inputEl: HTMLInputElement;

  constructor(app: App, inputEl: HTMLInputElement) {
    super(app, inputEl);
    this.inputEl = inputEl;
  }

  getSuggestions(query: string): TFile[] {
    const lowerQuery = query.toLowerCase();
    return this.app.vault
      .getMarkdownFiles()
      .filter((file) => file.path.toLowerCase().includes(lowerQuery))
      .slice(0, 20);
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

// Usage in settings tab:
new Setting(containerEl)
  .setName('Template file')
  .setDesc('Path to the template file.')
  .addText((text) => {
    new FileSuggest(this.app, text.inputEl);
    text
      .setPlaceholder('path/to/template.md')
      .setValue(this.plugin.settings.templatePath)
      .onChange(async (value) => {
        this.plugin.settings.templatePath = value;
        await this.plugin.saveSettings();
      });
  });
```

## Network request

```typescript
import { requestUrl } from 'obsidian';

async fetchData(endpoint: string): Promise<unknown> {
  try {
    const response = await requestUrl({
      url: `https://api.example.com/${endpoint}`,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.status !== 200) {
      new Notice(`Request failed with status ${response.status}.`);
      return null;
    }

    return response.json;
  } catch (e) {
    console.error('Network request failed:', e);
    new Notice('Network request failed. Check your connection.');
    return null;
  }
}
```

## Themed CSS example

```css
/* styles.css */

/* Dashboard */
.my-plugin-dashboard {
  padding: var(--size-4-4);
}

.my-plugin-dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--size-4-4);
}

.my-plugin-dashboard-header h3 {
  margin: 0;
  font-size: var(--font-ui-large);
  color: var(--text-normal);
}

.my-plugin-refresh-btn {
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--interactive-normal);
  border: 1px solid var(--background-modifier-border);
  border-radius: var(--radius-s);
  color: var(--text-normal);
  cursor: pointer;
}

.my-plugin-refresh-btn:hover {
  background: var(--interactive-hover);
}

.my-plugin-refresh-btn:focus-visible {
  outline: 2px solid var(--interactive-accent);
  outline-offset: 2px;
}

/* List items */
.my-plugin-dashboard-item {
  display: flex;
  align-items: center;
  min-height: 44px;
  padding: var(--size-4-2) var(--size-4-3);
  border-radius: var(--radius-s);
  color: var(--text-normal);
  cursor: pointer;
}

.my-plugin-dashboard-item:hover {
  background: var(--background-modifier-hover);
}

.my-plugin-dashboard-item:focus-visible {
  box-shadow: 0 0 0 2px var(--interactive-accent);
}

/* Modal */
.my-plugin-input-modal {
  padding: var(--size-4-4);
}

.my-plugin-input-modal p {
  color: var(--text-normal);
  margin-bottom: var(--size-4-3);
}

/* Status bar */
.my-plugin-status {
  color: var(--text-muted);
  font-size: var(--font-ui-smaller);
}
```
