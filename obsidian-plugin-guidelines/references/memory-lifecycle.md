# Memory Management and Lifecycle

Proper resource management is critical in Obsidian plugins. Failing to clean up event listeners, intervals, and DOM references causes memory leaks that degrade performance over time.

## Core principle

Obsidian's `Plugin` class provides lifecycle-aware registration methods. When you use these methods, cleanup happens automatically when the plugin is disabled or unloaded.

## registerEvent()

Always use `this.registerEvent()` to subscribe to Obsidian events. This ensures the listener is removed when the plugin unloads.

```typescript
// CORRECT
export default class MyPlugin extends Plugin {
  async onload() {
    this.registerEvent(
      this.app.vault.on('create', (file) => {
        console.log('File created:', file.path);
      })
    );

    this.registerEvent(
      this.app.workspace.on('file-open', (file) => {
        if (file) {
          this.handleFileOpen(file);
        }
      })
    );
  }
}

// WRONG - event listener is never removed
export default class MyPlugin extends Plugin {
  async onload() {
    this.app.vault.on('create', (file) => {
      console.log('File created:', file.path);
    });
  }
}
```

## addCommand()

Use `this.addCommand()` to register commands. Obsidian automatically removes them on unload.

```typescript
// CORRECT
this.addCommand({
  id: 'insert-timestamp',
  name: 'Insert timestamp',
  editorCallback: (editor: Editor) => {
    editor.replaceSelection(new Date().toISOString());
  }
});
```

## registerDomEvent()

Use `this.registerDomEvent()` for DOM event listeners. This ensures proper cleanup.

```typescript
// CORRECT
this.registerDomEvent(document, 'click', (evt: MouseEvent) => {
  // Handle click
});

// WRONG - manual listener without cleanup
document.addEventListener('click', this.handleClick);
```

## registerInterval()

Use `this.registerInterval()` for recurring timers.

```typescript
// CORRECT
this.registerInterval(
  window.setInterval(() => this.checkForUpdates(), 5 * 60 * 1000)
);

// WRONG - interval is never cleared
setInterval(() => this.checkForUpdates(), 5 * 60 * 1000);
```

**Important**: Use `window.setInterval` (returns `number`) not `setInterval` (returns `NodeJS.Timeout` in TypeScript). The `registerInterval()` method expects a `number` parameter.

## Don't store view references

Storing view references in plugin properties causes memory leaks because views can be destroyed and recreated by Obsidian at any time. The stored reference prevents garbage collection of the old view.

```typescript
// WRONG - stores view reference
export default class MyPlugin extends Plugin {
  private myView: MyView;

  async onload() {
    this.registerView(VIEW_TYPE, (leaf) => {
      this.myView = new MyView(leaf);
      return this.myView;
    });
  }

  doSomething() {
    // This reference may be stale
    this.myView.refresh();
  }
}

// CORRECT - look up the view when needed
export default class MyPlugin extends Plugin {
  async onload() {
    this.registerView(VIEW_TYPE, (leaf) => new MyView(leaf));
  }

  getView(): MyView | null {
    const leaves = this.app.workspace.getLeavesOfType(VIEW_TYPE);
    if (leaves.length > 0) {
      return leaves[0].view as MyView;
    }
    return null;
  }

  doSomething() {
    const view = this.getView();
    if (view) {
      view.refresh();
    }
  }
}
```

## Don't pass plugin as component to MarkdownRenderer

Passing the plugin instance as the `component` parameter to `MarkdownRenderer.render()` attaches cleanup responsibilities to the plugin's entire lifecycle. Instead, create a dedicated `Component` instance or use the view/container as the component.

```typescript
// WRONG
MarkdownRenderer.render(this.app, markdown, el, sourcePath, this);

// CORRECT - use a dedicated component
const component = new Component();
component.load();
MarkdownRenderer.render(this.app, markdown, el, sourcePath, component);
// Later: component.unload() when done

// CORRECT - use the view as component
MarkdownRenderer.render(this.app, markdown, el, sourcePath, this.view);
```

## Don't detach leaves in onunload()

When a plugin is disabled, Obsidian handles cleaning up the plugin's views. Manually detaching leaves in `onunload()` causes issues because the views may already be in the process of being cleaned up.

```typescript
// WRONG
async onunload() {
  this.app.workspace.detachLeavesOfType(VIEW_TYPE);
}

// CORRECT - let Obsidian handle leaf cleanup
async onunload() {
  // Obsidian automatically cleans up registered views
}
```

## Lifecycle summary

| Method | What it registers | Auto-cleanup? |
|--------|-------------------|---------------|
| `registerEvent()` | Obsidian event listeners | Yes |
| `addCommand()` | Commands | Yes |
| `registerDomEvent()` | DOM event listeners | Yes |
| `registerInterval()` | `setInterval` timers | Yes |
| `registerView()` | Custom views | Yes |
| `addSettingTab()` | Settings tabs | Yes |
| `addRibbonIcon()` | Ribbon icons | Yes |
| `addStatusBarItem()` | Status bar items | Yes |

All of these are automatically cleaned up when the plugin is disabled. Do not manually clean them up in `onunload()` unless you have a specific reason.
