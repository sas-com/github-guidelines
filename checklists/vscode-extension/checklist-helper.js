/**
 * VS Code Extension Helper for PR Review Checklist
 * エス・エー・エス株式会社
 * 
 * このスクリプトは、VS Code拡張機能として、PRレビューチェックリストを
 * エディタ内で簡単に利用できるようにするヘルパー機能を提供します。
 */

// チェックリスト構造の読み込み
const checklistStructure = require('../pr-checklist-structure.json');

/**
 * チェックリストアイテムクラス
 */
class ChecklistItem {
    constructor(id, label, description, priority, autoCheckable = false, tools = []) {
        this.id = id;
        this.label = label;
        this.description = description;
        this.priority = priority;
        this.autoCheckable = autoCheckable;
        this.tools = tools;
        this.checked = false;
        this.notes = '';
    }

    /**
     * チェック状態を切り替え
     */
    toggle() {
        this.checked = !this.checked;
        return this.checked;
    }

    /**
     * Markdown形式で出力
     */
    toMarkdown() {
        const checkbox = this.checked ? '[x]' : '[ ]';
        const autoLabel = this.autoCheckable ? ' 🤖' : '';
        const priorityEmoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }[this.priority] || '';
        
        let markdown = `- ${checkbox} ${priorityEmoji} **${this.label}**${autoLabel}\n`;
        markdown += `  - ${this.description}\n`;
        
        if (this.tools.length > 0) {
            markdown += `  - Tools: ${this.tools.join(', ')}\n`;
        }
        
        if (this.notes) {
            markdown += `  - Notes: ${this.notes}\n`;
        }
        
        return markdown;
    }
}

/**
 * チェックリストマネージャークラス
 */
class ChecklistManager {
    constructor() {
        this.checklists = checklistStructure.checklists;
        this.currentChecklist = [];
        this.prType = null;
        this.reviewerLevel = null;
    }

    /**
     * PR種別に応じたチェックリストを生成
     */
    generateChecklistForPRType(prType) {
        this.prType = prType;
        this.currentChecklist = [];

        const prTypeConfig = this.checklists.pr_types[prType];
        if (!prTypeConfig) {
            throw new Error(`Unknown PR type: ${prType}`);
        }

        // 基本チェックリストを追加
        this.addBasicChecklist();

        // PR種別固有のチェック項目を追加
        if (prTypeConfig.priorityChecks) {
            this.addPRTypeSpecificChecks(prTypeConfig.priorityChecks);
        }

        return this.currentChecklist;
    }

    /**
     * レビュアーレベルに応じたチェックリストを生成
     */
    generateChecklistForReviewerLevel(level) {
        this.reviewerLevel = level;
        this.currentChecklist = [];

        const levelConfig = this.checklists.levels[level];
        if (!levelConfig) {
            throw new Error(`Unknown reviewer level: ${level}`);
        }

        // 必須カテゴリーのチェック項目を追加
        if (levelConfig.requiredCategories.includes('all')) {
            this.addAllChecks();
        } else {
            levelConfig.requiredCategories.forEach(category => {
                this.addCategoryChecks(category);
            });
        }

        // レベル固有のチェックポイントを追加
        if (levelConfig.checkpoints) {
            this.addSpecificCheckpoints(levelConfig.checkpoints);
        }

        return this.currentChecklist;
    }

    /**
     * 基本チェックリストを追加
     */
    addBasicChecklist() {
        const basicCategories = ['code_quality', 'security', 'testing'];
        basicCategories.forEach(categoryName => {
            const category = this.findCategory(categoryName);
            if (category) {
                category.items.forEach(item => {
                    this.currentChecklist.push(new ChecklistItem(
                        item.id,
                        item.label,
                        item.description,
                        item.priority,
                        item.autoCheckable,
                        item.tools || []
                    ));
                });
            }
        });
    }

    /**
     * カテゴリー内のチェック項目を追加
     */
    addCategoryChecks(categoryName) {
        const category = this.findCategory(categoryName);
        if (category) {
            category.items.forEach(item => {
                this.currentChecklist.push(new ChecklistItem(
                    item.id,
                    item.label,
                    item.description,
                    item.priority,
                    item.autoCheckable,
                    item.tools || []
                ));
            });
        }
    }

    /**
     * カテゴリーを検索
     */
    findCategory(categoryName) {
        for (const checklistType of Object.values(this.checklists)) {
            if (checklistType.categories) {
                const category = checklistType.categories.find(cat => cat.name === categoryName);
                if (category) {
                    return category;
                }
            }
        }
        return null;
    }

    /**
     * チェックリストをMarkdown形式で出力
     */
    exportToMarkdown() {
        let markdown = '# PR Review Checklist\n\n';
        
        if (this.prType) {
            markdown += `## PR Type: ${this.prType}\n\n`;
        }
        
        if (this.reviewerLevel) {
            markdown += `## Reviewer Level: ${this.reviewerLevel}\n\n`;
        }
        
        // プライオリティ別にグループ化
        const grouped = this.groupByPriority();
        
        ['critical', 'high', 'medium', 'low'].forEach(priority => {
            if (grouped[priority] && grouped[priority].length > 0) {
                markdown += `### ${priority.charAt(0).toUpperCase() + priority.slice(1)} Priority\n\n`;
                grouped[priority].forEach(item => {
                    markdown += item.toMarkdown() + '\n';
                });
            }
        });
        
        // 完了率を計算
        const totalItems = this.currentChecklist.length;
        const checkedItems = this.currentChecklist.filter(item => item.checked).length;
        const completionRate = totalItems > 0 ? Math.round((checkedItems / totalItems) * 100) : 0;
        
        markdown += `\n## 📊 Completion Status\n\n`;
        markdown += `- Total items: ${totalItems}\n`;
        markdown += `- Completed: ${checkedItems}\n`;
        markdown += `- Completion rate: ${completionRate}%\n`;
        markdown += `- Progress: ${'█'.repeat(Math.floor(completionRate / 10))}${'░'.repeat(10 - Math.floor(completionRate / 10))} ${completionRate}%\n`;
        
        return markdown;
    }

    /**
     * プライオリティ別にグループ化
     */
    groupByPriority() {
        const grouped = {
            critical: [],
            high: [],
            medium: [],
            low: []
        };
        
        this.currentChecklist.forEach(item => {
            if (grouped[item.priority]) {
                grouped[item.priority].push(item);
            }
        });
        
        return grouped;
    }

    /**
     * 自動チェック可能な項目を取得
     */
    getAutoCheckableItems() {
        return this.currentChecklist.filter(item => item.autoCheckable);
    }

    /**
     * チェックリストの進捗状況を取得
     */
    getProgress() {
        const total = this.currentChecklist.length;
        const checked = this.currentChecklist.filter(item => item.checked).length;
        const autoCheckable = this.getAutoCheckableItems().length;
        
        return {
            total,
            checked,
            remaining: total - checked,
            autoCheckable,
            completionRate: total > 0 ? (checked / total) * 100 : 0
        };
    }

    /**
     * チェックリストをリセット
     */
    reset() {
        this.currentChecklist = [];
        this.prType = null;
        this.reviewerLevel = null;
    }
}

/**
 * VS Code Command: チェックリストを生成
 */
function generateChecklist(prType, reviewerLevel) {
    const manager = new ChecklistManager();
    
    if (prType) {
        manager.generateChecklistForPRType(prType);
    }
    
    if (reviewerLevel) {
        manager.generateChecklistForReviewerLevel(reviewerLevel);
    }
    
    return manager;
}

/**
 * VS Code Command: クイックピック用のアイテムを生成
 */
function getQuickPickItems() {
    return {
        prTypes: [
            { label: '🚀 Feature', value: 'feature', description: 'New feature implementation' },
            { label: '🐛 Bugfix', value: 'bugfix', description: 'Bug fix' },
            { label: '🔥 Hotfix', value: 'hotfix', description: 'Emergency fix' },
            { label: '♻️ Refactoring', value: 'refactoring', description: 'Code improvement' }
        ],
        reviewerLevels: [
            { label: '🟢 Junior', value: 'junior', description: 'Junior reviewer checklist' },
            { label: '🔵 Senior', value: 'senior', description: 'Senior reviewer checklist' },
            { label: '🟣 Architect', value: 'architect', description: 'Tech lead/Architect checklist' }
        ]
    };
}

/**
 * VS Code Command: 自動チェックを実行
 */
async function runAutoChecks(manager) {
    const autoCheckableItems = manager.getAutoCheckableItems();
    const results = [];
    
    for (const item of autoCheckableItems) {
        // ここで実際のツールを呼び出す
        // 例: ESLint, SonarQube, etc.
        const result = await runToolCheck(item);
        results.push({
            item: item.id,
            passed: result.passed,
            message: result.message
        });
        
        if (result.passed) {
            item.checked = true;
        }
    }
    
    return results;
}

/**
 * ツールチェックを実行（モック実装）
 */
async function runToolCheck(item) {
    // 実際の実装では、各ツールのAPIを呼び出す
    return {
        passed: Math.random() > 0.3, // 70%の確率で成功
        message: `Check ${item.id} completed`
    };
}

// エクスポート
module.exports = {
    ChecklistItem,
    ChecklistManager,
    generateChecklist,
    getQuickPickItems,
    runAutoChecks
};

// VS Code拡張機能として使用する場合のサンプル
if (typeof vscode !== 'undefined') {
    const vscode = require('vscode');
    
    // コマンド: チェックリストを生成
    vscode.commands.registerCommand('prReview.generateChecklist', async () => {
        const quickPickItems = getQuickPickItems();
        
        // PR種別を選択
        const prType = await vscode.window.showQuickPick(
            quickPickItems.prTypes,
            { placeHolder: 'Select PR type' }
        );
        
        if (!prType) return;
        
        // レビュアーレベルを選択
        const level = await vscode.window.showQuickPick(
            quickPickItems.reviewerLevels,
            { placeHolder: 'Select reviewer level' }
        );
        
        if (!level) return;
        
        // チェックリストを生成
        const manager = generateChecklist(prType.value, level.value);
        
        // 新しいドキュメントを作成
        const doc = await vscode.workspace.openTextDocument({
            content: manager.exportToMarkdown(),
            language: 'markdown'
        });
        
        await vscode.window.showTextDocument(doc);
    });
    
    // コマンド: 自動チェックを実行
    vscode.commands.registerCommand('prReview.runAutoChecks', async () => {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Running automated checks...',
            cancellable: false
        }, async (progress) => {
            // 現在のチェックリストマネージャーを取得（実装省略）
            const manager = getCurrentManager();
            
            if (!manager) {
                vscode.window.showErrorMessage('No checklist generated');
                return;
            }
            
            const results = await runAutoChecks(manager);
            
            // 結果を表示
            const passed = results.filter(r => r.passed).length;
            const total = results.length;
            
            vscode.window.showInformationMessage(
                `Automated checks completed: ${passed}/${total} passed`
            );
            
            // チェックリストを更新
            updateChecklistDocument(manager);
        });
    });
}