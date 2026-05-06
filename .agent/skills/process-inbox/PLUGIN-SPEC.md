## Obsidian Inbox Processor Plugin - Complete Specification

**Status:** Python backend ✅ complete | Plugin UI ⏳ to be built

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   OBSIDIAN PLUGIN (TypeScript)           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Settings Tab → Stores API key in data.json             │
│  Sidebar View → Shows proposals with buttons            │
│  Commands     → "Process Inbox", "Apply Changes"        │
│                                                          │
│  ┌────────────────────────────────────────────┐         │
│  │  When user clicks "Process Inbox":         │         │
│  │                                             │         │
│  │  await exec(`python3 analyzer.py           │         │
│  │    --vault "${vaultPath}"                  │         │
│  │    ${ai ? '--use-ai' : ''}                 │         │
│  │    --provider ${provider}                  │         │
│  │    --api-key ${apiKey}`)                   │         │
│  │                                             │         │
│  │  Then: Parse proposals.md → Show in UI     │         │
│  └────────────────────────────────────────────┘         │
│                                                          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ↓ Calls Python scripts
┌─────────────────────────────────────────────────────────┐
│              PYTHON BACKEND (analyzer.py)                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Mode A: Keyword matching (free, fast)                  │
│  ├─ Scan inbox folders                                  │
│  ├─ Extract concepts via regex                          │
│  └─ Match against existing MOCs/frameworks              │
│                                                          │
│  Mode B: LLM analysis (smart, costs ~$)                 │
│  ├─ Scan inbox folders                                  │
│  ├─ Call Claude/GPT API for each item                   │
│  ├─ Get semantic analysis + relationships               │
│  └─ Detect topic clusters for MOC suggestions           │
│                                                          │
│  Output: proposals.md with actionable suggestions       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## User Workflows

### Workflow 1: Without AI (Free, Fast)

```
1. User drops 10 articles in Clippings/

2. User opens Obsidian sidebar
   ┌─────────────────────────────────┐
   │ 📥 Inbox Processing             │
   ├─────────────────────────────────┤
   │ Unprocessed items: 10           │
   │                                 │
   │ [🔍 Analyze Inbox]              │
   │                                 │
   │ AI Analysis: ❌ Disabled        │
   │ (Free keyword matching)         │
   └─────────────────────────────────┘

3. Clicks "Analyze Inbox"
   → Plugin calls: python3 analyzer.py ~/vault
   → Takes 1-2 seconds

4. Plugin shows results:
   ┌─────────────────────────────────────────┐
   │ 📋 Proposals (10 items)                 │
   ├─────────────────────────────────────────┤
   │ 1/10 Microsoft Agent Stack.md           │
   │                                         │
   │ Relates to: AI Federation MOC (85%)    │
   │                                         │
   │ Actions:                                │
   │ ├─ Add wikilink to MOC                 │
   │ │  [✓ Accept] [✗ Reject]               │
   │ └─ Update framework                     │
   │    [✓ Accept] [✗ Reject]               │
   │                                         │
   │ ← Previous | Next → | [Apply All]      │
   └─────────────────────────────────────────┘

5. User reviews, clicks Accept/Reject for each action

6. User clicks "Apply All"
   → Plugin calls: python3 apply.py ~/vault
   → Files updated, items archived
   → Shows summary
```

### Workflow 2: With AI (Smart, Paid)

```
1. User configures AI in settings:
   ┌──────────────────────────────────┐
   │ Inbox Processing Settings        │
   ├──────────────────────────────────┤
   │ ☑ Enable AI Analysis             │
   │                                  │
   │ Provider: ⚫ Anthropic           │
   │                                  │
   │ API Key: sk-ant-***              │
   │ [Test Connection] ✅             │
   │                                  │
   │ Cost estimate: ~$0.15/50 items   │
   │                                  │
   │ [Save Settings]                  │
   └──────────────────────────────────┘

2. User drops 10 articles

3. Clicks "Analyze Inbox"
   ┌─────────────────────────────────┐
   │ 🤖 AI Analysis in progress...   │
   │                                 │
   │ ████████░░ 8/10 items           │
   │                                 │
   │ Estimated cost: $0.024          │
   └─────────────────────────────────┘

4. Plugin shows results:
   ┌─────────────────────────────────────────┐
   │ 📋 Proposals (10 items)                 │
   ├─────────────────────────────────────────┤
   │ 🎯 Suggested MOC: RAG Architecture      │
   │    5 items detected                     │
   │    [✓ Accept] [✗ Reject]                │
   │                                         │
   │ ─────────────────────────────────────   │
   │                                         │
   │ 1/10 Microsoft Agent Stack.md           │
   │                                         │
   │ 🤖 AI Analysis:                         │
   │ "Article discusses centralized vs       │
   │  federated agent architectures..."      │
   │                                         │
   │ Relates to:                             │
   │ - AI Federation MOC (95%) ✨            │
   │ - Multi-Agent Framework (87%)           │
   │                                         │
   │ Key insight: "Microsoft's unified       │
   │ approach misses the personal layer"     │
   │                                         │
   │ Actions:                                │
   │ ├─ Add to AI Federation MOC             │
   │ │  [✓ Accept] [✗ Reject]               │
   │ └─ Update Multi-Agent Framework         │
   │    [✓ Accept] [✗ Reject]               │
   │                                         │
   │ ← Previous | Next → | [Apply All]      │
   └─────────────────────────────────────────┘

5. User reviews AI suggestions

6. Clicks "Apply All" → Changes applied
```

---

## Plugin Components

### 1. Settings Tab

```typescript
interface InboxProcessorSettings {
  // AI settings
  aiEnabled: boolean;
  aiProvider: 'anthropic' | 'openai';
  apiKey: string;
  model?: string;

  // Paths
  pythonPath: string;

  // Behavior
  autoArchive: boolean;
  confirmBeforeApply: boolean;
}

class InboxProcessorSettingTab extends PluginSettingTab {
  display(): void {
    // AI Enable toggle
    new Setting(containerEl)
      .setName('Enable AI Analysis')
      .addToggle(toggle => {
        toggle.setValue(this.plugin.settings.aiEnabled)
          .onChange(async (value) => {
            this.plugin.settings.aiEnabled = value;
            await this.plugin.saveSettings();
            this.display(); // Refresh to show/hide API settings
          });
      });

    // Provider selection (only if AI enabled)
    if (this.plugin.settings.aiEnabled) {
      new Setting(containerEl)
        .setName('AI Provider')
        .addDropdown(dropdown => {
          dropdown
            .addOption('anthropic', 'Anthropic (Claude)')
            .addOption('openai', 'OpenAI (GPT)')
            .setValue(this.plugin.settings.aiProvider)
            .onChange(async (value) => {
              this.plugin.settings.aiProvider = value;
              await this.plugin.saveSettings();
            });
        });

      // API Key input
      new Setting(containerEl)
        .setName('API Key')
        .addText(text => {
          text
            .setPlaceholder('sk-...')
            .setValue(this.plugin.settings.apiKey)
            .onChange(async (value) => {
              this.plugin.settings.apiKey = value;
              await this.plugin.saveSettings();
            });
        })
        .addButton(button => {
          button
            .setButtonText('Test Connection')
            .onClick(async () => {
              await this.testConnection();
            });
        });
    }
  }

  async testConnection(): Promise<void> {
    // Call llm_analyzer.py test function
    const result = await this.plugin.runPython(
      'llm_analyzer.py',
      [this.plugin.settings.aiProvider, this.plugin.settings.apiKey]
    );

    if (result.success) {
      new Notice('✅ Connection successful!');
    } else {
      new Notice('❌ Connection failed: ' + result.message);
    }
  }
}
```

### 2. Sidebar View

```typescript
class InboxSidebarView extends ItemView {
  proposals: Proposal[] = [];
  currentIndex: number = 0;

  async onOpen() {
    const container = this.containerEl.children[1];
    container.empty();

    // Show inbox count
    const count = await this.getInboxCount();
    container.createEl('h4', { text: `📥 Inbox (${count})` });

    // Analyze button
    const analyzeBtn = container.createEl('button', {
      text: '🔍 Analyze Inbox'
    });
    analyzeBtn.addEventListener('click', async () => {
      await this.analyze();
    });

    // Show proposals if available
    if (this.proposals.length > 0) {
      this.renderProposals(container);
    }
  }

  async analyze(): Promise<void> {
    // Show progress
    this.showProgress('Analyzing...');

    // Call Python analyzer
    const args = ['--vault', this.app.vault.adapter.basePath];

    if (this.plugin.settings.aiEnabled) {
      args.push('--use-ai');
      args.push('--provider', this.plugin.settings.aiProvider);
      args.push('--api-key', this.plugin.settings.apiKey);
    }

    await this.plugin.runPython('analyzer.py', args);

    // Read proposals.md
    const proposalsFile = this.app.vault.getAbstractFileByPath('proposals.md');
    if (proposalsFile instanceof TFile) {
      const content = await this.app.vault.read(proposalsFile);
      this.proposals = this.parseProposals(content);
      this.onOpen(); // Refresh view
    }
  }

  renderProposals(container: HTMLElement): void {
    const proposal = this.proposals[this.currentIndex];

    // MOC suggestions (if any)
    if (proposal.mocSuggestion) {
      this.renderMocSuggestion(container, proposal.mocSuggestion);
    }

    // Item details
    container.createEl('h5', {
      text: `${this.currentIndex + 1}/${this.proposals.length} ${proposal.filename}`
    });

    // Relationships
    if (proposal.relationships) {
      proposal.relationships.forEach(rel => {
        const relEl = container.createDiv({ cls: 'relationship' });
        relEl.createEl('span', {
          text: `Relates to: ${rel.target} (${rel.confidence}%)`
        });
      });
    }

    // Actions
    proposal.actions.forEach((action, idx) => {
      const actionEl = container.createDiv({ cls: 'action' });
      actionEl.createEl('p', { text: action.description });

      // Accept/Reject buttons
      const btnContainer = actionEl.createDiv({ cls: 'action-buttons' });

      btnContainer.createEl('button', {
        text: '✓ Accept',
        cls: action.status === 'accept' ? 'active' : ''
      }).addEventListener('click', () => {
        proposal.actions[idx].status = 'accept';
        this.onOpen(); // Refresh
      });

      btnContainer.createEl('button', {
        text: '✗ Reject',
        cls: action.status === 'reject' ? 'active' : ''
      }).addEventListener('click', () => {
        proposal.actions[idx].status = 'reject';
        this.onOpen(); // Refresh
      });
    });

    // Navigation
    const navContainer = container.createDiv({ cls: 'navigation' });

    if (this.currentIndex > 0) {
      navContainer.createEl('button', { text: '← Previous' })
        .addEventListener('click', () => {
          this.currentIndex--;
          this.onOpen();
        });
    }

    if (this.currentIndex < this.proposals.length - 1) {
      navContainer.createEl('button', { text: 'Next →' })
        .addEventListener('click', () => {
          this.currentIndex++;
          this.onOpen();
        });
    }

    // Apply button
    navContainer.createEl('button', {
      text: 'Apply All',
      cls: 'mod-cta'
    }).addEventListener('click', async () => {
      await this.applyChanges();
    });
  }

  async applyChanges(): Promise<void> {
    // Write updated proposals back to proposals.md
    const updatedContent = this.serializeProposals(this.proposals);
    await this.app.vault.adapter.write('proposals.md', updatedContent);

    // Call apply.py
    await this.plugin.runPython('apply.py', [
      '--vault', this.app.vault.adapter.basePath
    ]);

    new Notice('✅ Changes applied!');

    // Refresh
    this.proposals = [];
    this.currentIndex = 0;
    this.onOpen();
  }
}
```

### 3. Main Plugin Class

```typescript
export default class InboxProcessorPlugin extends Plugin {
  settings: InboxProcessorSettings;

  async onload() {
    await this.loadSettings();

    // Add settings tab
    this.addSettingTab(new InboxProcessorSettingTab(this.app, this));

    // Register sidebar view
    this.registerView(
      'inbox-processor-sidebar',
      (leaf) => new InboxSidebarView(leaf, this)
    );

    // Add ribbon icon
    this.addRibbonIcon('inbox', 'Process Inbox', () => {
      this.activateView();
    });

    // Add commands
    this.addCommand({
      id: 'process-inbox',
      name: 'Process Inbox',
      callback: () => {
        this.activateView();
      }
    });
  }

  async runPython(script: string, args: string[] = []): Promise<any> {
    const { exec } = require('child_process');
    const scriptPath = path.join(
      this.app.vault.adapter.basePath,
      '.agent/skills/process-inbox',
      script
    );

    const command = `${this.settings.pythonPath} ${scriptPath} ${args.join(' ')}`;

    return new Promise((resolve, reject) => {
      exec(command, (error, stdout, stderr) => {
        if (error) {
          reject(error);
        } else {
          try {
            resolve(JSON.parse(stdout));
          } catch {
            resolve(stdout);
          }
        }
      });
    });
  }

  async activateView() {
    this.app.workspace.detachLeavesOfType('inbox-processor-sidebar');

    await this.app.workspace.getRightLeaf(false).setViewState({
      type: 'inbox-processor-sidebar',
      active: true,
    });

    this.app.workspace.revealLeaf(
      this.app.workspace.getLeavesOfType('inbox-processor-sidebar')[0]
    );
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
}
```

---

## Summary

**What we built:**
✅ Python backend with keyword + LLM analysis
✅ Automatic MOC detection
✅ BrainLift processing
✅ Complete CLI tools

**What's next:**
⏳ Obsidian plugin UI wrapper
⏳ Sidebar view with actionable buttons
⏳ Settings panel for API keys

**The plugin is just UI** - all the intelligence is in Python scripts. This makes it easy to:
- Test/iterate on analysis logic
- Use from command line OR plugin
- Support multiple editors (could wrap with VSCode extension too)

**User experience:**
1. Install plugin
2. (Optional) Enter API key in settings
3. Drop files in inbox
4. Click "Analyze" button
5. Review with Accept/Reject buttons
6. Click "Apply" → Done!
