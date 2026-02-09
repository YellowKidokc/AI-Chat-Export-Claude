# Type Safety

TypeScript's type system helps catch bugs at compile time. Obsidian plugins should use proper type narrowing and avoid unsafe patterns.

## Use instanceof instead of type casting

Obsidian's vault methods return abstract types. Use `instanceof` to narrow them safely rather than casting, which bypasses type checking entirely.

```typescript
// CORRECT - safe type narrowing
const file = this.app.vault.getAbstractFileByPath(path);
if (file instanceof TFile) {
  // TypeScript knows this is a TFile
  const content = await this.app.vault.read(file);
}

if (file instanceof TFolder) {
  // TypeScript knows this is a TFolder
  for (const child of file.children) {
    // ...
  }
}

// WRONG - unsafe cast, no runtime check
const file = this.app.vault.getAbstractFileByPath(path) as TFile;
// If this is actually a TFolder, you get runtime errors
const content = await this.app.vault.read(file);
```

### Why this matters

- `getAbstractFileByPath()` returns `TAbstractFile | null`
- The result could be a `TFile`, a `TFolder`, or `null`
- Casting with `as TFile` tells TypeScript to trust you, but provides zero runtime protection
- `instanceof` checks the actual type at runtime and narrows the TypeScript type simultaneously

## Avoid the any type

Using `any` disables TypeScript's type checking for that value. Use specific types or `unknown` instead.

```typescript
// WRONG
function processData(data: any) {
  return data.name.toUpperCase();
}

// CORRECT - use a specific type
interface PluginData {
  name: string;
  count: number;
}

function processData(data: PluginData) {
  return data.name.toUpperCase();
}

// CORRECT - use unknown with type guards when the type is truly unknown
function processData(data: unknown) {
  if (typeof data === 'object' && data !== null && 'name' in data) {
    const typed = data as { name: string };
    return typed.name.toUpperCase();
  }
  throw new Error('Invalid data format');
}
```

### When any is unavoidable

Sometimes external APIs or Obsidian's own types require `any`. In those cases, narrow the type as close to the boundary as possible:

```typescript
// Obsidian's loadData() returns Promise<any>
async loadSettings(): Promise<MySettings> {
  const data: unknown = await this.loadData();
  return Object.assign({}, DEFAULT_SETTINGS, data);
}
```

## Use const and let, not var

`var` has function-scoped hoisting that leads to subtle bugs. `const` and `let` are block-scoped and easier to reason about.

```typescript
// WRONG
var count = 0;
for (var i = 0; i < items.length; i++) {
  var item = items[i];
  // 'item' is accessible outside this block
}

// CORRECT
let count = 0;
for (let i = 0; i < items.length; i++) {
  const item = items[i];
  // 'item' is scoped to this block
}

// Prefer const when the value won't be reassigned
const settings = await this.loadSettings();
const file = this.app.vault.getAbstractFileByPath(path);
```

## Type narrowing patterns

### Null checks

```typescript
const file = this.app.workspace.getActiveFile();
if (!file) {
  new Notice('No active file');
  return;
}
// TypeScript knows file is TFile here
```

### Array element checks

```typescript
const leaves = this.app.workspace.getLeavesOfType(VIEW_TYPE);
if (leaves.length === 0) {
  return;
}
const leaf = leaves[0];
// leaf is guaranteed to exist
```

### String union discrimination

```typescript
function handleEvent(type: 'create' | 'modify' | 'delete', file: TFile) {
  switch (type) {
    case 'create':
      // handle creation
      break;
    case 'modify':
      // handle modification
      break;
    case 'delete':
      // handle deletion
      break;
  }
}
```

## Settings type safety

Define a complete settings interface with defaults:

```typescript
interface MyPluginSettings {
  dateFormat: string;
  showNotifications: boolean;
  maxResults: number;
}

const DEFAULT_SETTINGS: MyPluginSettings = {
  dateFormat: 'YYYY-MM-DD',
  showNotifications: true,
  maxResults: 10,
};
```

Use `Object.assign` with the defaults to ensure all fields are present even if the saved data is partial:

```typescript
async loadSettings(): Promise<MyPluginSettings> {
  return Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
}
```
