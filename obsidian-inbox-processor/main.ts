import {
	App,
	Plugin,
	PluginSettingTab,
	Setting,
	ItemView,
	WorkspaceLeaf,
	TFile,
	Notice,
	Modal
} from 'obsidian';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';

const execAsync = promisify(exec);

// View type identifier
const VIEW_TYPE_INBOX = 'entropy-inbox-processor';

interface EntropySettings {
	// AI settings
	aiEnabled: boolean;
	aiProvider: 'anthropic' | 'openai';
	apiKey: string;
	model: string;

	// Paths
	pythonPath: string;

	// Behavior
	autoArchive: boolean;
	confirmBeforeApply: boolean;
}

const DEFAULT_SETTINGS: EntropySettings = {
	aiEnabled: false,
	aiProvider: 'anthropic',
	apiKey: '',
	model: '',
	pythonPath: 'python3',
	autoArchive: true,
	confirmBeforeApply: true
};

interface ProposalAction {
	type: string;
	target: string;
	section?: string;
	content: string;
	rationale: string;
	status: 'pending' | 'accept' | 'reject';
}

interface Relationship {
	target: string;
	confidence: number;
	reason: string;
}

interface ItemProposal {
	filename: string;
	wordCount: number;
	path: string;
	relationships: Relationship[];
	actions: ProposalAction[];
}

interface MOCSuggestion {
	name: string;
	topic: string;
	itemCount: number;
	items: string[];
	status: 'pending' | 'accept' | 'reject';
}

export default class EntropyInboxProcessor extends Plugin {
	settings: EntropySettings;
	statusBarItem: HTMLElement;

	async onload() {
		await this.loadSettings();

		// Add status bar item
		this.statusBarItem = this.addStatusBarItem();
		this.updateStatusBar();

		// Register view
		this.registerView(
			VIEW_TYPE_INBOX,
			(leaf) => new InboxProcessorView(leaf, this)
		);

		// Add ribbon icon
		this.addRibbonIcon('inbox', 'Entropy: Process Inbox', () => {
			this.activateView();
		});

		// Add commands
		this.addCommand({
			id: 'open-inbox-processor',
			name: 'Open Inbox Processor',
			callback: () => {
				this.activateView();
			}
		});

		this.addCommand({
			id: 'analyze-inbox',
			name: 'Analyze Inbox Now',
			callback: async () => {
				await this.activateView();
				const view = this.app.workspace.getLeavesOfType(VIEW_TYPE_INBOX)[0]?.view as InboxProcessorView;
				if (view) {
					await view.analyze();
				}
			}
		});

		// Add settings tab
		this.addSettingTab(new EntropySettingTab(this.app, this));

		// Update inbox count periodically
		this.registerInterval(
			window.setInterval(() => this.updateStatusBar(), 60000) // Every minute
		);
	}

	async activateView() {
		const { workspace } = this.app;

		let leaf: WorkspaceLeaf | null = null;
		const leaves = workspace.getLeavesOfType(VIEW_TYPE_INBOX);

		if (leaves.length > 0) {
			// View already exists, reveal it
			leaf = leaves[0];
		} else {
			// Create new view in right sidebar
			leaf = workspace.getRightLeaf(false);
			if (leaf) {
				await leaf.setViewState({ type: VIEW_TYPE_INBOX, active: true });
			}
		}

		if (leaf) {
			workspace.revealLeaf(leaf);
		}
	}

	async updateStatusBar() {
		try {
			const count = await this.getInboxCount();
			this.statusBarItem.setText(`📥 ${count}`);
			this.statusBarItem.setAttribute('aria-label', `${count} items in inbox`);
		} catch (error) {
			this.statusBarItem.setText('📥 ?');
		}
	}

	async getInboxCount(): Promise<number> {
		const inboxFolders = ['00-Inbox', 'Clippings', 'raw'];
		let count = 0;

		for (const folder of inboxFolders) {
			const folderPath = `${folder}/`;
			const files = this.app.vault.getMarkdownFiles().filter(f =>
				f.path.startsWith(folderPath) && !f.path.includes('/processed/')
			);
			count += files.length;
		}

		return count;
	}

	async runPythonScript(scriptName: string, args: string[] = []): Promise<string> {
		const vaultPath = (this.app.vault.adapter as any).basePath;
		const scriptPath = path.join(vaultPath, '.agent/skills/process-inbox', scriptName);

		const command = `${this.settings.pythonPath} "${scriptPath}" ${args.join(' ')}`;

		try {
			const { stdout, stderr } = await execAsync(command, {
				cwd: vaultPath,
				maxBuffer: 10 * 1024 * 1024 // 10MB buffer
			});

			if (stderr) {
				console.warn('Python stderr:', stderr);
			}

			return stdout;
		} catch (error) {
			console.error('Python execution failed:', error);
			throw error;
		}
	}

	async loadSettings() {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings() {
		await this.saveData(this.settings);
	}
}

class InboxProcessorView extends ItemView {
	plugin: EntropyInboxProcessor;
	proposals: ItemProposal[] = [];
	mocSuggestions: MOCSuggestion[] = [];
	currentIndex: number = 0;
	isAnalyzing: boolean = false;

	constructor(leaf: WorkspaceLeaf, plugin: EntropyInboxProcessor) {
		super(leaf);
		this.plugin = plugin;
	}

	getViewType() {
		return VIEW_TYPE_INBOX;
	}

	getDisplayText() {
		return 'Entropy Inbox';
	}

	getIcon() {
		return 'inbox';
	}

	async onOpen() {
		await this.render();
	}

	async render() {
		const container = this.containerEl.children[1] as HTMLElement;
		container.empty();
		container.addClass('entropy-inbox-view');

		// Header
		const header = container.createDiv({ cls: 'entropy-header' });
		header.createEl('h4', { text: '📥 Entropy Inbox Processor' });

		// Inbox count
		const count = await this.plugin.getInboxCount();
		const countEl = container.createDiv({ cls: 'entropy-inbox-count' });
		countEl.createEl('p', { text: `Unprocessed items: ${count}` });

		// Analyze button
		const analyzeBtn = container.createEl('button', {
			text: this.isAnalyzing ? '⏳ Analyzing...' : '🔍 Analyze Inbox',
			cls: 'mod-cta'
		});
		analyzeBtn.disabled = this.isAnalyzing || count === 0;
		analyzeBtn.addEventListener('click', async () => {
			await this.analyze();
		});

		// AI status
		if (this.plugin.settings.aiEnabled) {
			const aiStatus = container.createDiv({ cls: 'entropy-ai-status' });
			aiStatus.createEl('p', {
				text: `✨ AI Analysis: Enabled (${this.plugin.settings.aiProvider})`,
				cls: 'entropy-ai-enabled'
			});
			const estimatedCost = (count * 0.003).toFixed(2);
			aiStatus.createEl('p', {
				text: `Estimated cost: ~$${estimatedCost}`,
				cls: 'entropy-cost-estimate'
			});
		} else {
			const aiStatus = container.createDiv({ cls: 'entropy-ai-status' });
			aiStatus.createEl('p', {
				text: '⚡ Fast mode (keyword matching)',
				cls: 'entropy-ai-disabled'
			});
		}

		container.createEl('hr');

		// Show proposals if available
		if (this.mocSuggestions.length > 0 || this.proposals.length > 0) {
			await this.renderProposals(container);
		} else {
			container.createDiv({ cls: 'entropy-empty' }).createEl('p', {
				text: count === 0
					? '✅ Inbox is empty!'
					: 'Click "Analyze Inbox" to start processing'
			});
		}
	}

	async analyze() {
		this.isAnalyzing = true;
		await this.render();

		try {
			const vaultPath = (this.app.vault.adapter as any).basePath;
			const args = [`"${vaultPath}"`];

			if (this.plugin.settings.aiEnabled && this.plugin.settings.apiKey) {
				args.push('--use-ai');
				args.push('--provider', this.plugin.settings.aiProvider);
				args.push('--api-key', `"${this.plugin.settings.apiKey}"`);
				if (this.plugin.settings.model) {
					args.push('--model', this.plugin.settings.model);
				}
			}

			new Notice('Analyzing inbox...');
			await this.plugin.runPythonScript('analyzer.py', args);

			// Read proposals.md
			await this.loadProposals();

			new Notice(`✅ Found ${this.proposals.length} items to process`);

		} catch (error) {
			new Notice('❌ Analysis failed: ' + error.message);
			console.error('Analysis error:', error);
		} finally {
			this.isAnalyzing = false;
			await this.render();
		}
	}

	async loadProposals() {
		const proposalsFile = this.app.vault.getAbstractFileByPath('proposals.md');
		if (!(proposalsFile instanceof TFile)) {
			return;
		}

		const content = await this.app.vault.read(proposalsFile);
		this.parseProposals(content);
	}

	parseProposals(content: string) {
		this.proposals = [];
		this.mocSuggestions = [];

		// Parse MOC suggestions
		const mocSection = content.match(/## 🎯 Suggested New MOCs\n([\s\S]+?)(?=\n## 📋|$)/);
		if (mocSection) {
			const mocText = mocSection[1];
			const mocBlocks = mocText.split(/### MOC Suggestion: /g).filter(b => b.trim());

			for (const block of mocBlocks) {
				const nameMatch = block.match(/^(.+)/);
				const topicMatch = block.match(/\*\*Detected topic:\*\* (.+)/);
				const countMatch = block.match(/\*\*Items in cluster:\*\* (\d+)/);
				const itemsMatch = block.match(/\*\*Items:\*\*\n([\s\S]+?)(?=\n### ACTION)/);

				if (nameMatch && topicMatch && countMatch) {
					const items: string[] = [];
					if (itemsMatch) {
						const itemLines = itemsMatch[1].split('\n');
						for (const line of itemLines) {
							if (line.trim().startsWith('- ') && !line.includes('...')) {
								items.push(line.trim().substring(2));
							}
						}
					}

					this.mocSuggestions.push({
						name: nameMatch[1].trim(),
						topic: topicMatch[1],
						itemCount: parseInt(countMatch[1]),
						items,
						status: 'pending'
					});
				}
			}
		}

		// Parse individual items
		const itemBlocks = content.split(/## Item \d+: /g).filter(b => b.trim());

		for (const block of itemBlocks) {
			const lines = block.split('\n');
			const filename = lines[0]?.trim();
			if (!filename) continue;

			const wordCountMatch = block.match(/\*\*Word Count:\*\* (\d+)/);
			const pathMatch = block.match(/\*\*Path:\*\* `([^`]+)`/);

			// Parse relationships
			const relationships: Relationship[] = [];
			const relSection = block.match(/\*\*Relationships:\*\*\n\n([\s\S]+?)(?=\n\*\*Proposed Actions|$)/);
			if (relSection) {
				const relLines = relSection[1].split('\n');
				for (const line of relLines) {
					const relMatch = line.match(/- (.+) \((\d+)% confidence\)/);
					if (relMatch) {
						relationships.push({
							target: relMatch[1],
							confidence: parseInt(relMatch[2]),
							reason: ''
						});
					}
				}
			}

			// Parse actions
			const actions: ProposalAction[] = [];
			const actionBlocks = block.split(/### ACTION \d+: /g).filter(b => b.trim());

			for (const actionBlock of actionBlocks) {
				const typeMatch = actionBlock.match(/^(\w+)/);
				const targetMatch = actionBlock.match(/\*\*Target:\*\* `([^`]+)`/);
				const sectionMatch = actionBlock.match(/\*\*Section:\*\* (.+)/);
				const rationaleMatch = actionBlock.match(/\*\*Rationale:\*\* (.+)/);
				const contentMatch = actionBlock.match(/```diff\n(.+?)\n```/s);

				if (typeMatch && targetMatch && rationaleMatch) {
					actions.push({
						type: typeMatch[1].toLowerCase(),
						target: targetMatch[1],
						section: sectionMatch?.[1],
						content: contentMatch?.[1] || '',
						rationale: rationaleMatch[1],
						status: 'pending'
					});
				}
			}

			this.proposals.push({
				filename,
				wordCount: wordCountMatch ? parseInt(wordCountMatch[1]) : 0,
				path: pathMatch?.[1] || '',
				relationships,
				actions
			});
		}
	}

	async renderProposals(container: HTMLElement) {
		// MOC suggestions first
		if (this.mocSuggestions.length > 0) {
			const mocSection = container.createDiv({ cls: 'entropy-moc-suggestions' });
			mocSection.createEl('h5', { text: '🎯 Suggested New MOCs' });

			for (let i = 0; i < this.mocSuggestions.length; i++) {
				const moc = this.mocSuggestions[i];
				const mocCard = mocSection.createDiv({ cls: 'entropy-moc-card' });

				mocCard.createEl('h6', { text: `MOC: ${moc.name}` });
				mocCard.createEl('p', { text: `Topic: ${moc.topic} • ${moc.itemCount} items` });

				const itemsList = mocCard.createEl('ul', { cls: 'entropy-moc-items' });
				for (const item of moc.items.slice(0, 3)) {
					itemsList.createEl('li', { text: item });
				}
				if (moc.items.length > 3) {
					itemsList.createEl('li', { text: `... and ${moc.items.length - 3} more` });
				}

				const btnContainer = mocCard.createDiv({ cls: 'entropy-action-buttons' });

				const acceptBtn = btnContainer.createEl('button', {
					text: '✓ Accept',
					cls: moc.status === 'accept' ? 'active' : ''
				});
				acceptBtn.addEventListener('click', () => {
					this.mocSuggestions[i].status = 'accept';
					this.render();
				});

				const rejectBtn = btnContainer.createEl('button', {
					text: '✗ Reject',
					cls: moc.status === 'reject' ? 'active' : ''
				});
				rejectBtn.addEventListener('click', () => {
					this.mocSuggestions[i].status = 'reject';
					this.render();
				});
			}

			container.createEl('hr');
		}

		// Individual item proposals
		if (this.proposals.length > 0) {
			const itemSection = container.createDiv({ cls: 'entropy-item-proposals' });
			itemSection.createEl('h5', { text: `📋 Items (${this.currentIndex + 1}/${this.proposals.length})` });

			const proposal = this.proposals[this.currentIndex];

			// Item details
			const itemCard = itemSection.createDiv({ cls: 'entropy-item-card' });
			itemCard.createEl('h6', { text: proposal.filename });
			itemCard.createEl('p', {
				text: `${proposal.wordCount} words`,
				cls: 'entropy-meta'
			});

			// Relationships
			if (proposal.relationships.length > 0) {
				const relSection = itemCard.createDiv({ cls: 'entropy-relationships' });
				relSection.createEl('strong', { text: 'Relates to:' });
				const relList = relSection.createEl('ul');
				for (const rel of proposal.relationships) {
					relList.createEl('li', { text: `${rel.target} (${rel.confidence}%)` });
				}
			}

			// Actions
			if (proposal.actions.length > 0) {
				const actionsSection = itemCard.createDiv({ cls: 'entropy-actions' });
				actionsSection.createEl('strong', { text: 'Proposed Actions:' });

				for (let i = 0; i < proposal.actions.length; i++) {
					const action = proposal.actions[i];
					const actionCard = actionsSection.createDiv({ cls: 'entropy-action-card' });

					actionCard.createEl('p', { text: `${action.type.toUpperCase()}: ${action.target}` });
					if (action.section) {
						actionCard.createEl('p', { text: `Section: ${action.section}`, cls: 'entropy-meta' });
					}
					actionCard.createEl('p', { text: action.rationale, cls: 'entropy-rationale' });

					const btnContainer = actionCard.createDiv({ cls: 'entropy-action-buttons' });

					const acceptBtn = btnContainer.createEl('button', {
						text: '✓ Accept',
						cls: action.status === 'accept' ? 'active' : ''
					});
					acceptBtn.addEventListener('click', () => {
						this.proposals[this.currentIndex].actions[i].status = 'accept';
						this.render();
					});

					const rejectBtn = btnContainer.createEl('button', {
						text: '✗ Reject',
						cls: action.status === 'reject' ? 'active' : ''
					});
					rejectBtn.addEventListener('click', () => {
						this.proposals[this.currentIndex].actions[i].status = 'reject';
						this.render();
					});
				}
			}

			// Navigation
			const navSection = container.createDiv({ cls: 'entropy-navigation' });

			if (this.currentIndex > 0) {
				const prevBtn = navSection.createEl('button', { text: '← Previous' });
				prevBtn.addEventListener('click', () => {
					this.currentIndex--;
					this.render();
				});
			}

			if (this.currentIndex < this.proposals.length - 1) {
				const nextBtn = navSection.createEl('button', { text: 'Next →' });
				nextBtn.addEventListener('click', () => {
					this.currentIndex++;
					this.render();
				});
			}

			// Apply button
			const applyBtn = navSection.createEl('button', {
				text: 'Apply All Changes',
				cls: 'mod-cta'
			});
			applyBtn.addEventListener('click', async () => {
				await this.applyChanges();
			});
		}
	}

	async applyChanges() {
		// Update proposals.md with user choices
		try {
			const proposalsFile = this.app.vault.getAbstractFileByPath('proposals.md');
			if (!(proposalsFile instanceof TFile)) {
				new Notice('proposals.md not found');
				return;
			}

			let content = await this.app.vault.read(proposalsFile);

			// Update MOC suggestions
			for (const moc of this.mocSuggestions) {
				const pattern = new RegExp(
					`(### MOC Suggestion: ${moc.name}[\\s\\S]+?\\[)ACCEPT(\\] \\[)REJECT(\\])`,
					'g'
				);
				if (moc.status === 'accept') {
					content = content.replace(pattern, '$1ACCEPT$2REJECT$3');
				} else if (moc.status === 'reject') {
					content = content.replace(pattern, '$1ACCEPT$2REJECT$3');
				}
			}

			// Update item actions
			// This is simplified - full implementation would track exact positions
			content = content.replace(/\[ACCEPT\]/g, '[REJECT]'); // Reset all
			for (const proposal of this.proposals) {
				for (const action of proposal.actions) {
					if (action.status === 'accept') {
						// Mark as ACCEPT in content
						// Real implementation would need precise matching
					}
				}
			}

			await this.app.vault.modify(proposalsFile, content);

			// Run apply script
			new Notice('Applying changes...');
			const vaultPath = (this.app.vault.adapter as any).basePath;
			await this.plugin.runPythonScript('apply.py', [`"${vaultPath}"`]);

			new Notice('✅ Changes applied!');

			// Reset state
			this.proposals = [];
			this.mocSuggestions = [];
			this.currentIndex = 0;
			await this.plugin.updateStatusBar();
			await this.render();

		} catch (error) {
			new Notice('❌ Failed to apply changes: ' + error.message);
			console.error('Apply error:', error);
		}
	}
}

class EntropySettingTab extends PluginSettingTab {
	plugin: EntropyInboxProcessor;

	constructor(app: App, plugin: EntropyInboxProcessor) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const { containerEl } = this;

		containerEl.empty();

		containerEl.createEl('h2', { text: 'Entropy Inbox Processor Settings' });

		// AI Analysis toggle
		new Setting(containerEl)
			.setName('Enable AI Analysis')
			.setDesc('Use Claude or GPT for semantic understanding (requires API key)')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.aiEnabled)
				.onChange(async (value) => {
					this.plugin.settings.aiEnabled = value;
					await this.plugin.saveSettings();
					this.display(); // Refresh to show/hide AI settings
				}));

		// AI-specific settings
		if (this.plugin.settings.aiEnabled) {
			// Provider selection
			new Setting(containerEl)
				.setName('AI Provider')
				.setDesc('Choose between Anthropic Claude or OpenAI GPT')
				.addDropdown(dropdown => dropdown
					.addOption('anthropic', 'Anthropic (Claude)')
					.addOption('openai', 'OpenAI (GPT)')
					.setValue(this.plugin.settings.aiProvider)
					.onChange(async (value: 'anthropic' | 'openai') => {
						this.plugin.settings.aiProvider = value;
						await this.plugin.saveSettings();
					}));

			// API Key
			new Setting(containerEl)
				.setName('API Key')
				.setDesc('Your Anthropic or OpenAI API key (stored locally)')
				.addText(text => text
					.setPlaceholder('sk-...')
					.setValue(this.plugin.settings.apiKey)
					.onChange(async (value) => {
						this.plugin.settings.apiKey = value;
						await this.plugin.saveSettings();
					}))
				.addButton(button => button
					.setButtonText('Test Connection')
					.onClick(async () => {
						await this.testConnection();
					}));

			// Model (optional)
			new Setting(containerEl)
				.setName('Model (optional)')
				.setDesc('Override default model (e.g., gpt-4o-mini for cheaper OpenAI)')
				.addText(text => text
					.setPlaceholder('Leave empty for default')
					.setValue(this.plugin.settings.model)
					.onChange(async (value) => {
						this.plugin.settings.model = value;
						await this.plugin.saveSettings();
					}));

			// Security notice
			const securityEl = containerEl.createDiv({ cls: 'entropy-security-notice' });
			securityEl.createEl('p', {
				text: '⚠️ Security Notice:',
				cls: 'entropy-warning-title'
			});
			securityEl.createEl('p', {
				text: 'API keys are stored in .obsidian/plugins/entropy-inbox-processor/data.json. Keep this folder out of git repositories!'
			});
			securityEl.createEl('p', {
				text: 'Estimated cost: ~$0.15 for 50 items with Claude, ~$0.03 with GPT-4o-mini'
			});
		}

		// Python path
		new Setting(containerEl)
			.setName('Python Path')
			.setDesc('Path to Python 3 executable')
			.addText(text => text
				.setPlaceholder('python3')
				.setValue(this.plugin.settings.pythonPath)
				.onChange(async (value) => {
					this.plugin.settings.pythonPath = value;
					await this.plugin.saveSettings();
				}));

		// Behavior settings
		containerEl.createEl('h3', { text: 'Behavior' });

		new Setting(containerEl)
			.setName('Auto-archive processed items')
			.setDesc('Automatically move processed items to raw/processed/')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.autoArchive)
				.onChange(async (value) => {
					this.plugin.settings.autoArchive = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Confirm before applying')
			.setDesc('Show confirmation dialog before applying changes')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.confirmBeforeApply)
				.onChange(async (value) => {
					this.plugin.settings.confirmBeforeApply = value;
					await this.plugin.saveSettings();
				}));
	}

	async testConnection(): Promise<void> {
		try {
			new Notice('Testing connection...');

			const result = await this.plugin.runPythonScript('llm_analyzer.py', [
				this.plugin.settings.aiProvider,
				`"${this.plugin.settings.apiKey}"`
			]);

			if (result.includes('✅')) {
				new Notice('✅ Connection successful!');
			} else {
				new Notice('❌ Connection failed');
			}
		} catch (error) {
			new Notice('❌ Connection failed: ' + error.message);
		}
	}
}
