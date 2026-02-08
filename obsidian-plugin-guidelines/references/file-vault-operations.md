# File and Vault Operations

Obsidian provides multiple APIs for working with files. Choosing the correct API prevents data loss, race conditions, and cursor position issues.

## Editor API vs Vault API

### Editor API: for active file edits

When the user is viewing a file and you want to modify it, use the Editor API. This preserves cursor position, undo history, and works correctly with live preview.

```typescript
// CORRECT - use editorCallback for active file operations
this.addCommand({
  id: 'insert-timestamp',
  name: 'Insert timestamp',
  editorCallback: (editor: Editor, view: MarkdownView) => {
    const cursor = editor.getCursor();
    editor.replaceSelection(new Date().toISOString());
  }
});

// Editor API methods
editor.getValue();                    // Get full content
editor.setValue(content);             // Replace full content
editor.getSelection();               // Get selected text
editor.replaceSelection(text);       // Replace selection
editor.replaceRange(text, from, to); // Replace a range
editor.getCursor();                  // Get cursor position
editor.setCursor(pos);               // Set cursor position
editor.getLine(n);                   // Get line content
editor.setLine(n, text);             // Set line content
```

### Vault.process(): for background file modifications

When modifying files that the user is not actively viewing, use `Vault.process()`. This performs atomic read-modify-write operations that prevent race conditions.

```typescript
// CORRECT - atomic read-modify-write
await this.app.vault.process(file, (content) => {
  return content.replace(/old/g, 'new');
});

// WRONG - non-atomic, can lose concurrent changes
const content = await this.app.vault.read(file);
const modified = content.replace(/old/g, 'new');
await this.app.vault.modify(file, modified);
```

### When to use which

| Scenario | API |
|----------|-----|
| User is editing the file (command palette, hotkey) | `editorCallback` / Editor API |
| Background batch processing | `Vault.process()` |
| Reading file content | `Vault.read()` or `Vault.cachedRead()` |
| Creating new files | `Vault.create()` |
| Deleting files | `fileManager.trashFile()` |
| Modifying frontmatter | `FileManager.processFrontMatter()` |

## Frontmatter operations

Use `FileManager.processFrontMatter()` to modify YAML frontmatter. This handles parsing and serialization correctly.

```typescript
// CORRECT
await this.app.fileManager.processFrontMatter(file, (fm) => {
  fm.tags = fm.tags || [];
  fm.tags.push('processed');
  fm.lastModified = new Date().toISOString();
});

// WRONG - manual YAML manipulation is error-prone
const content = await this.app.vault.read(file);
const modified = content.replace(/^---\n/, '---\ntags: [processed]\n');
await this.app.vault.modify(file, modified);
```

## File deletion

Use `fileManager.trashFile()` instead of `Vault.delete()`. This respects the user's trash settings (system trash vs. Obsidian trash vs. permanent delete).

```typescript
// CORRECT - respects user's trash preference
await this.app.fileManager.trashFile(file);

// WRONG - permanently deletes without respecting settings
await this.app.vault.delete(file);
```

## Path handling

### normalizePath()

Always use `normalizePath()` for user-provided paths. This handles path separator differences across platforms (Windows uses `\`, others use `/`).

```typescript
import { normalizePath } from 'obsidian';

// CORRECT
const path = normalizePath(userInput);
const file = this.app.vault.getAbstractFileByPath(path);

// CORRECT - for constructed paths
const templatePath = normalizePath(`${folder}/${filename}.md`);

// WRONG - may fail on Windows
const path = `${folder}/${filename}`;
```

### Don't hardcode .obsidian

Use `vault.configDir` to get the config directory path. Users can change this.

```typescript
// CORRECT
const configPath = normalizePath(`${this.app.vault.configDir}/plugins`);

// WRONG - .obsidian may not be the config dir
const configPath = '.obsidian/plugins';
```

## File lookups

### Use direct lookups instead of vault iteration

Obsidian provides efficient lookup methods. Don't iterate over all files to find one.

```typescript
// CORRECT - O(1) lookup
const file = this.app.vault.getAbstractFileByPath('path/to/file.md');
if (file instanceof TFile) {
  // found it
}

// CORRECT - get file by path, returns TFile | null
const file = this.app.vault.getFileByPath('path/to/file.md');

// CORRECT - get folder by path, returns TFolder | null
const folder = this.app.vault.getFolderByPath('path/to/folder');

// WRONG - O(n) iteration
const allFiles = this.app.vault.getMarkdownFiles();
const target = allFiles.find(f => f.path === 'path/to/file.md');
```

### Get all markdown files

When you do need to iterate, use the appropriate method:

```typescript
// All markdown files
const mdFiles = this.app.vault.getMarkdownFiles();

// All files (including non-markdown)
const allFiles = this.app.vault.getFiles();
```

## View access patterns

### Getting the active file

```typescript
const file = this.app.workspace.getActiveFile();
if (!file) {
  new Notice('No active file');
  return;
}
```

### Getting the active editor

```typescript
const editor = this.app.workspace.activeEditor?.editor;
if (!editor) {
  new Notice('No active editor');
  return;
}
```

### Getting leaves of a view type

```typescript
const leaves = this.app.workspace.getLeavesOfType('my-view-type');
if (leaves.length > 0) {
  this.app.workspace.revealLeaf(leaves[0]);
}
```

## Reading cached vs fresh content

```typescript
// Use cachedRead when you don't need the absolute latest version
// (faster, uses the in-memory cache)
const content = await this.app.vault.cachedRead(file);

// Use read when you need the latest from disk
const content = await this.app.vault.read(file);
```

## Creating files safely

```typescript
// Create a file, checking if it exists first
const path = normalizePath('folder/new-file.md');
const existing = this.app.vault.getAbstractFileByPath(path);

if (existing) {
  new Notice('File already exists');
  return;
}

// Ensure parent folder exists
const folderPath = normalizePath('folder');
const folder = this.app.vault.getAbstractFileByPath(folderPath);
if (!folder) {
  await this.app.vault.createFolder(folderPath);
}

await this.app.vault.create(path, 'Initial content');
```
