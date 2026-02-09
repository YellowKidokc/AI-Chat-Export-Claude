import {
	Editor,
	ItemView,
	Notice,
	Plugin,
	PluginSettingTab,
	Setting,
	TFile,
	WorkspaceLeaf,
	normalizePath,
	requestUrl,
	Platform,
	App,
} from "obsidian";

// ---------- Interfaces ----------

interface ChatMessage {
	role: "user" | "assistant";
	content: string;
	timestamp: number;
}

interface PromptTemplate {
	name: string;
	template: string;
	enabled: boolean;
	description: string;
}

interface AiChatExportSettings {
	apiProvider: string;
	apiKey: string;
	model: string;
	temperature: number;
	maxTokens: number;
	exportFolder: string;
	prompts: Record<string, PromptTemplate>;
}

const DEFAULT_SETTINGS: AiChatExportSettings = {
	apiProvider: "openai",
	apiKey: "",
	model: "gpt-4o-mini",
	temperature: 0.7,
	maxTokens: 2000,
	exportFolder: "AI Chat Exports",
	prompts: {
		clarify: {
			name: "Clarify",
			template:
				"Rewrite the following text for clarity and coherence without changing its meaning:\n\n{text}",
			enabled: true,
			description: "Makes text clearer and more coherent",
		},
		friendly: {
			name: "Make friendly",
			template:
				"Rewrite the following text to sound friendly and conversational:\n\n{text}",
			enabled: true,
			description: "Converts text to a friendly, conversational tone",
		},
		summarize: {
			name: "Summarize",
			template:
				"Summarize the following text clearly in 3 sentences:\n\n{text}",
			enabled: true,
			description: "Creates a concise 3-sentence summary",
		},
		professional: {
			name: "Professionalize",
			template:
				"Rewrite the following text to sound professional and polished:\n\n{text}",
			enabled: true,
			description: "Makes text sound professional and polished",
		},
		grammar: {
			name: "Fix grammar",
			template:
				"Fix any grammar, spelling, and punctuation errors in the following text:\n\n{text}",
			enabled: true,
			description: "Corrects grammar, spelling, and punctuation",
		},
		expand: {
			name: "Expand",
			template:
				"Expand on the following text with more detail and depth:\n\n{text}",
			enabled: false,
			description: "Adds more detail and depth to the text",
		},
		simplify: {
			name: "Simplify",
			template:
				"Rewrite the following text in simpler, easier-to-understand language:\n\n{text}",
			enabled: false,
			description: "Simplifies complex text",
		},
	},
};

const CHAT_VIEW_TYPE = "ai-chat-export-chat-view";

// ---------- Plugin ----------

export default class AiChatExportPlugin extends Plugin {
	settings: AiChatExportSettings = DEFAULT_SETTINGS;
	private chatHistory: ChatMessage[] = [];

	async onload(): Promise<void> {
		await this.loadSettings();

		this.registerView(
			CHAT_VIEW_TYPE,
			(leaf: WorkspaceLeaf) => new ChatView(leaf, this)
		);

		// Register commands for each enabled prompt (sentence case, no "command" prefix)
		for (const [id, prompt] of Object.entries(this.settings.prompts)) {
			if (prompt.enabled) {
				this.addCommand({
					id: id,
					name: prompt.name,
					editorCallback: (editor: Editor) => {
						this.runPromptOnSelection(editor, id);
					},
				});
			}
		}

		this.addCommand({
			id: "open-chat",
			name: "Open chat view",
			callback: () => {
				this.activateChatView();
			},
		});

		this.addCommand({
			id: "export-chat-history",
			name: "Export chat history to note",
			callback: () => {
				this.exportChatHistory();
			},
		});

		this.addSettingTab(new AiChatExportSettingTab(this.app, this));
	}

	async loadSettings(): Promise<void> {
		this.settings = Object.assign(
			{},
			DEFAULT_SETTINGS,
			await this.loadData()
		);
	}

	async saveSettings(): Promise<void> {
		await this.saveData(this.settings);
	}

	getChatHistory(): ChatMessage[] {
		return this.chatHistory;
	}

	clearChatHistory(): void {
		this.chatHistory = [];
	}

	async activateChatView(): Promise<void> {
		const existing =
			this.app.workspace.getLeavesOfType(CHAT_VIEW_TYPE);
		if (existing.length > 0) {
			this.app.workspace.revealLeaf(existing[0]);
			return;
		}
		const leaf = this.app.workspace.getRightLeaf(false);
		if (leaf) {
			await leaf.setViewState({
				type: CHAT_VIEW_TYPE,
				active: true,
			});
			this.app.workspace.revealLeaf(leaf);
		}
	}

	async runPromptOnSelection(
		editor: Editor,
		promptId: string
	): Promise<void> {
		const selection = editor.getSelection();
		if (!selection) {
			new Notice("No text selected.");
			return;
		}

		const prompt = this.settings.prompts[promptId];
		if (!prompt) {
			new Notice("Prompt not found.");
			return;
		}

		const fullPrompt = prompt.template.replace("{text}", selection);
		new Notice(`Processing with "${prompt.name}"...`);

		try {
			const result = await this.callAiApi([
				{ role: "user", content: fullPrompt, timestamp: Date.now() },
			]);
			editor.replaceSelection(result);
			new Notice("Text replaced successfully.");
		} catch (error) {
			const message =
				error instanceof Error ? error.message : "Unknown error";
			new Notice(`AI request failed: ${message}`);
		}
	}

	async sendChatMessage(userMessage: string): Promise<string> {
		this.chatHistory.push({
			role: "user",
			content: userMessage,
			timestamp: Date.now(),
		});

		try {
			const result = await this.callAiApi(this.chatHistory);
			this.chatHistory.push({
				role: "assistant",
				content: result,
				timestamp: Date.now(),
			});
			return result;
		} catch (error) {
			const message =
				error instanceof Error ? error.message : "Unknown error";
			this.chatHistory.pop(); // Remove failed user message
			throw new Error(message);
		}
	}

	async callAiApi(messages: ChatMessage[]): Promise<string> {
		if (!this.settings.apiKey) {
			throw new Error(
				"API key not configured. Set it in plugin settings."
			);
		}

		const apiMessages = messages.map((m) => ({
			role: m.role,
			content: m.content,
		}));

		// Uses requestUrl() instead of fetch() per Obsidian guidelines
		const response = await requestUrl({
			url: "https://api.openai.com/v1/chat/completions",
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				Authorization: `Bearer ${this.settings.apiKey}`,
			},
			body: JSON.stringify({
				model: this.settings.model,
				messages: apiMessages,
				temperature: this.settings.temperature,
				max_tokens: this.settings.maxTokens,
			}),
		});

		if (response.status !== 200) {
			throw new Error(
				`API returned status ${response.status}: ${response.text}`
			);
		}

		const data = response.json;
		if (
			!data.choices ||
			!Array.isArray(data.choices) ||
			data.choices.length === 0
		) {
			throw new Error("No response from AI.");
		}

		return data.choices[0].message.content;
	}

	async exportChatHistory(): Promise<void> {
		if (this.chatHistory.length === 0) {
			new Notice("No chat history to export.");
			return;
		}

		const folderPath = normalizePath(this.settings.exportFolder);
		const folder = this.app.vault.getAbstractFileByPath(folderPath);
		if (!folder) {
			await this.app.vault.createFolder(folderPath);
		}

		const timestamp = new Date()
			.toISOString()
			.replace(/[:.]/g, "-")
			.slice(0, 19);
		const fileName = normalizePath(
			`${folderPath}/Chat export ${timestamp}.md`
		);

		let content = `# Chat export ${timestamp}\n\n`;
		for (const msg of this.chatHistory) {
			const time = new Date(msg.timestamp).toLocaleTimeString();
			const label = msg.role === "user" ? "You" : "AI";
			content += `### ${label} (${time})\n\n${msg.content}\n\n---\n\n`;
		}

		await this.app.vault.create(fileName, content);
		new Notice(`Chat exported to ${fileName}`);

		// Open the exported file
		const file = this.app.vault.getAbstractFileByPath(fileName);
		if (file instanceof TFile) {
			await this.app.workspace.getLeaf().openFile(file);
		}
	}
}

// ---------- Chat view ----------

class ChatView extends ItemView {
	private plugin: AiChatExportPlugin;
	private messagesContainer: HTMLElement | null = null;
	private inputEl: HTMLTextAreaElement | null = null;

	constructor(leaf: WorkspaceLeaf, plugin: AiChatExportPlugin) {
		super(leaf);
		this.plugin = plugin;
	}

	getViewType(): string {
		return CHAT_VIEW_TYPE;
	}

	getDisplayText(): string {
		return "AI chat";
	}

	getIcon(): string {
		return "message-square";
	}

	async onOpen(): Promise<void> {
		const container = this.containerEl.children[1];
		container.empty();

		const wrapper = container.createDiv({
			cls: "ai-chat-export-chat-wrapper",
		});

		// Header with actions
		const header = wrapper.createDiv({
			cls: "ai-chat-export-chat-header",
		});
		header.createEl("span", {
			text: "AI chat",
			cls: "ai-chat-export-chat-title",
		});

		const headerActions = header.createDiv({
			cls: "ai-chat-export-header-actions",
		});

		const exportBtn = headerActions.createEl("button", {
			cls: "ai-chat-export-header-btn",
			attr: {
				"aria-label": "Export chat history",
				"data-tooltip-position": "top",
			},
		});
		exportBtn.setText("Export");
		exportBtn.addEventListener("click", () => {
			this.plugin.exportChatHistory();
		});

		const clearBtn = headerActions.createEl("button", {
			cls: "ai-chat-export-header-btn",
			attr: {
				"aria-label": "Clear chat history",
				"data-tooltip-position": "top",
			},
		});
		clearBtn.setText("Clear");
		clearBtn.addEventListener("click", () => {
			this.plugin.clearChatHistory();
			this.renderMessages();
			new Notice("Chat history cleared.");
		});

		// Messages area
		this.messagesContainer = wrapper.createDiv({
			cls: "ai-chat-export-messages",
			attr: {
				role: "log",
				"aria-label": "Chat messages",
				"aria-live": "polite",
			},
		});

		this.renderMessages();

		// Input area
		const inputArea = wrapper.createDiv({
			cls: "ai-chat-export-input-area",
		});

		this.inputEl = inputArea.createEl("textarea", {
			cls: "ai-chat-export-input",
			attr: {
				placeholder: "Type a message...",
				"aria-label": "Chat message input",
				rows: "3",
			},
		});

		this.inputEl.addEventListener("keydown", (e: KeyboardEvent) => {
			if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
				e.preventDefault();
				this.sendMessage();
			}
		});

		const sendBtn = inputArea.createEl("button", {
			cls: "ai-chat-export-send-btn",
			attr: {
				"aria-label": "Send message",
				"data-tooltip-position": "top",
			},
		});
		sendBtn.setText("Send");
		sendBtn.addEventListener("click", () => {
			this.sendMessage();
		});

		const hint = inputArea.createDiv({
			cls: "ai-chat-export-input-hint",
		});
		const shortcut = Platform.isMacOS ? "Cmd+Enter" : "Ctrl+Enter";
		hint.setText(`Press ${shortcut} to send`);
	}

	private renderMessages(): void {
		if (!this.messagesContainer) return;
		this.messagesContainer.empty();

		const history = this.plugin.getChatHistory();
		if (history.length === 0) {
			const empty = this.messagesContainer.createDiv({
				cls: "ai-chat-export-empty",
			});
			empty.setText("No messages yet. Start a conversation.");
			return;
		}

		for (const msg of history) {
			const msgDiv = this.messagesContainer.createDiv({
				cls: `ai-chat-export-message ai-chat-export-message-${msg.role}`,
			});

			const labelDiv = msgDiv.createDiv({
				cls: "ai-chat-export-message-label",
			});
			labelDiv.setText(msg.role === "user" ? "You" : "AI");

			const contentDiv = msgDiv.createDiv({
				cls: "ai-chat-export-message-content",
			});
			contentDiv.setText(msg.content);

			const timeDiv = msgDiv.createDiv({
				cls: "ai-chat-export-message-time",
			});
			timeDiv.setText(
				new Date(msg.timestamp).toLocaleTimeString()
			);
		}

		this.messagesContainer.scrollTop =
			this.messagesContainer.scrollHeight;
	}

	private async sendMessage(): Promise<void> {
		if (!this.inputEl) return;

		const text = this.inputEl.value.trim();
		if (!text) return;

		this.inputEl.value = "";
		this.renderMessages();

		// Add temporary user message for immediate feedback
		this.plugin.getChatHistory().push({
			role: "user",
			content: text,
			timestamp: Date.now(),
		});
		this.renderMessages();

		// Remove the manually added message (sendChatMessage will add it)
		this.plugin.getChatHistory().pop();

		try {
			await this.plugin.sendChatMessage(text);
			this.renderMessages();
		} catch (error) {
			const message =
				error instanceof Error ? error.message : "Unknown error";
			new Notice(`Chat error: ${message}`);
			this.renderMessages();
		}
	}

	async onClose(): Promise<void> {
		this.messagesContainer = null;
		this.inputEl = null;
	}
}

// ---------- Settings tab ----------

class AiChatExportSettingTab extends PluginSettingTab {
	plugin: AiChatExportPlugin;

	constructor(app: App, plugin: AiChatExportPlugin) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const { containerEl } = this;
		containerEl.empty();

		// API configuration section - uses .setHeading() per guidelines
		new Setting(containerEl).setName("API configuration").setHeading();

		new Setting(containerEl)
			.setName("API provider")
			.setDesc("Select the AI API provider to use.")
			.addDropdown((dropdown) => {
				dropdown
					.addOption("openai", "OpenAI")
					.setValue(this.plugin.settings.apiProvider)
					.onChange(async (value) => {
						this.plugin.settings.apiProvider = value;
						await this.plugin.saveSettings();
					});
			});

		new Setting(containerEl)
			.setName("API key")
			.setDesc("Your API key for the selected provider.")
			.addText((text) => {
				text.inputEl.type = "password";
				text.inputEl.setAttribute(
					"aria-label",
					"API key input"
				);
				text.setPlaceholder("Enter your API key")
					.setValue(this.plugin.settings.apiKey)
					.onChange(async (value) => {
						this.plugin.settings.apiKey = value;
						await this.plugin.saveSettings();
					});
			});

		new Setting(containerEl)
			.setName("Model")
			.setDesc("The AI model to use for processing.")
			.addText((text) => {
				text.setPlaceholder("gpt-4o-mini")
					.setValue(this.plugin.settings.model)
					.onChange(async (value) => {
						this.plugin.settings.model = value;
						await this.plugin.saveSettings();
					});
			});

		new Setting(containerEl)
			.setName("Temperature")
			.setDesc(
				"Controls randomness in responses (0.0 = deterministic, 1.0 = creative)."
			)
			.addSlider((slider) => {
				slider
					.setLimits(0, 1, 0.1)
					.setValue(this.plugin.settings.temperature)
					.setDynamicTooltip()
					.onChange(async (value) => {
						this.plugin.settings.temperature = value;
						await this.plugin.saveSettings();
					});
			});

		new Setting(containerEl)
			.setName("Max tokens")
			.setDesc("Maximum number of tokens in AI responses.")
			.addText((text) => {
				text.setPlaceholder("2000")
					.setValue(
						String(this.plugin.settings.maxTokens)
					)
					.onChange(async (value) => {
						const parsed = parseInt(value, 10);
						if (!isNaN(parsed) && parsed > 0) {
							this.plugin.settings.maxTokens = parsed;
							await this.plugin.saveSettings();
						}
					});
			});

		// Export section
		new Setting(containerEl).setName("Export").setHeading();

		new Setting(containerEl)
			.setName("Export folder")
			.setDesc(
				"Folder where chat exports are saved."
			)
			.addText((text) => {
				text.setPlaceholder("AI Chat Exports")
					.setValue(this.plugin.settings.exportFolder)
					.onChange(async (value) => {
						this.plugin.settings.exportFolder = value;
						await this.plugin.saveSettings();
					});
			});

		// Prompts section
		new Setting(containerEl).setName("Prompts").setHeading();

		for (const [id, prompt] of Object.entries(
			this.plugin.settings.prompts
		)) {
			new Setting(containerEl)
				.setName(prompt.name)
				.setDesc(prompt.description)
				.addToggle((toggle) => {
					toggle
						.setValue(prompt.enabled)
						.onChange(async (value) => {
							this.plugin.settings.prompts[id].enabled =
								value;
							await this.plugin.saveSettings();
							new Notice(
								`Prompt "${prompt.name}" ${value ? "enabled" : "disabled"}. Restart to update commands.`
							);
						});
				});
		}
	}
}
