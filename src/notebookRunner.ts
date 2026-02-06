import * as vscode from 'vscode';

const AGENT_CELL_METADATA_KEY = 'wandasAgent';
const RESULT_SENTINEL = '__WANDAS_AGENT_RESULT__';
const BACKUPS_METADATA_KEY = 'wandasAgentBackups';

export interface NotebookPythonRunResult {
	ok: boolean;
	success?: boolean;
	text: string;
	textOutputs: string[];
	imagesPngCount: number;
	writtenCode: string;
	parsedResult?: unknown;
	error?: string;
	traceback?: string;
	notebookError?: {
		name?: string;
		message?: string;
		stack?: string;
		raw?: unknown;
	};
}

function truncate(text: string, maxChars: number): string {
	if (text.length <= maxChars) {
		return text;
	}
	return `${text.slice(0, Math.max(0, maxChars - 20))}\n…(truncated ${text.length - maxChars} chars)`;
}

function decodeUtf8(data: Uint8Array): string {
	return new TextDecoder('utf-8').decode(data);
}

function readCellText(cell: vscode.NotebookCell): string {
	return cell.document.getText();
}

function getActiveNotebookEditor(): vscode.NotebookEditor {
	const editor = vscode.window.activeNotebookEditor;
	if (!editor) {
		throw new Error('アクティブなノートブックが見つかりません。.ipynb を開いてから再実行してください。');
	}
	return editor;
}

async function ensureAgentCell(editor: vscode.NotebookEditor): Promise<vscode.NotebookCell> {
	const existing = editor.notebook
		.getCells()
		.find(cell => Boolean((cell.metadata as Record<string, unknown> | undefined)?.[AGENT_CELL_METADATA_KEY]));
	if (existing) {
		return existing;
	}

	const cellData = new vscode.NotebookCellData(
		vscode.NotebookCellKind.Code,
		'# wandas-agent cell (auto-generated)\n',
		'python'
	);
	cellData.metadata = { [AGENT_CELL_METADATA_KEY]: true };

	const insertIndex = editor.notebook.cellCount;
	const edit = new vscode.WorkspaceEdit();
	edit.set(editor.notebook.uri, [vscode.NotebookEdit.insertCells(insertIndex, [cellData])]);
	const ok = await vscode.workspace.applyEdit(edit);
	if (!ok) {
		throw new Error('ノートブックに wandas-agent 用セルを追加できませんでした。');
	}

	// Re-fetch after edit
	const created = editor.notebook
		.getCells()
		.find(cell => Boolean((cell.metadata as Record<string, unknown> | undefined)?.[AGENT_CELL_METADATA_KEY]));
	if (!created) {
		throw new Error('wandas-agent 用セルの作成に失敗しました。');
	}
	return created;
}

async function overwriteCellText(cell: vscode.NotebookCell, newText: string): Promise<void> {
	const doc = cell.document;
	const lastLine = doc.lineAt(Math.max(0, doc.lineCount - 1));
	const fullRange = new vscode.Range(0, 0, Math.max(0, doc.lineCount - 1), lastLine.text.length);

	const edit = new vscode.WorkspaceEdit();
	edit.replace(doc.uri, fullRange, newText);
	const ok = await vscode.workspace.applyEdit(edit);
	if (!ok) {
		throw new Error('セルの内容を更新できませんでした。');
	}
}

async function executeCell(editor: vscode.NotebookEditor, cellIndex: number): Promise<void> {
	// Run by explicit document URI + ranges, so it works even when focus is on chat.
	const notebookUri = editor.notebook.uri;
	const range = new vscode.NotebookRange(cellIndex, cellIndex + 1);
	const rangesObj = [{ start: cellIndex, end: cellIndex + 1 }];

	// Best-effort: clear outputs so we can detect a new run.
	try {
		await vscode.commands.executeCommand('notebook.cell.clearOutputs', { document: notebookUri, ranges: rangesObj } as any);
	} catch {
		// ignore
	}

	const candidateArgs: any[] = [
		{ document: notebookUri, ranges: rangesObj },
		{ document: notebookUri, ranges: [range] },
		{ document: notebookUri, range },
		{ uri: notebookUri, ranges: rangesObj },
		{ uri: notebookUri, ranges: [range] }
	];

	for (const arg of candidateArgs) {
		try {
			await vscode.commands.executeCommand('notebook.cell.execute', arg);
			return;
		} catch {
			// try next
		}
	}

	// Last resort: set selection and run (may depend on focus)
	editor.selections = [range];
	try {
		editor.revealRange(range);
	} catch {
		// optional
	}
	await vscode.commands.executeCommand('notebook.cell.execute');
}

function outputSignature(cell: vscode.NotebookCell): string {
	return cell.outputs
		.map(o => o.items.map(i => `${i.mime}:${i.data.byteLength}`).join(','))
		.join('|');
}

async function waitForCellExecutionToEndPolling(
	editor: vscode.NotebookEditor,
	cellIndex: number,
	token: vscode.CancellationToken,
	timeoutMs: number,
	before: { executionOrder?: number; endTime?: number; outputsSig: string }
): Promise<{ success?: boolean }> {
	const start = Date.now();
	while (Date.now() - start < timeoutMs) {
		if (token.isCancellationRequested) {
			throw new Error('キャンセルされました。');
		}
		const cell = editor.notebook.getCells()[cellIndex];
		const summary = cell.executionSummary;
		const endTime = summary?.timing?.endTime;
		const outputsSig = outputSignature(cell);
		const executionOrder = summary?.executionOrder;

		// Consider finished when:
		// - there is a new endTime, or
		// - outputs changed and we have a defined success flag
		if (typeof endTime === 'number' && endTime !== before.endTime) {
			return { success: summary?.success };
		}
		if (outputsSig !== before.outputsSig && typeof summary?.success === 'boolean') {
			return { success: summary?.success };
		}
		if (typeof executionOrder === 'number' && executionOrder !== before.executionOrder && typeof endTime === 'number') {
			return { success: summary?.success };
		}

		await new Promise(r => setTimeout(r, 200));
	}
	throw new Error(`セル実行がタイムアウトしました（${timeoutMs}ms）。`);
}

function extractOutputs(cell: vscode.NotebookCell): { textOutputs: string[]; imagesPngCount: number } {
	const textOutputs: string[] = [];
	let imagesPngCount = 0;

	for (const out of cell.outputs) {
		for (const item of out.items) {
			if (item.mime === 'text/plain' || item.mime === 'text/markdown') {
				textOutputs.push(decodeUtf8(item.data));
			} else if (item.mime === 'image/png') {
				imagesPngCount += 1;
			}
		}
	}
	return { textOutputs, imagesPngCount };
}

function extractNotebookError(cell: vscode.NotebookCell): NotebookPythonRunResult['notebookError'] | undefined {
	for (const out of cell.outputs) {
		for (const item of out.items) {
			if (item.mime !== 'application/vnd.code.notebook.error') {
				continue;
			}
			const rawText = decodeUtf8(item.data);
			try {
				const parsed = JSON.parse(rawText) as any;
				return {
					name: typeof parsed?.name === 'string' ? parsed.name : undefined,
					message: typeof parsed?.message === 'string' ? parsed.message : undefined,
					stack: typeof parsed?.stack === 'string' ? parsed.stack : undefined,
					raw: parsed
				};
			} catch {
				return { raw: rawText };
			}
		}
	}
	return undefined;
}

function parseSentinel(textOutputs: string[]): { parsed?: unknown; error?: string; traceback?: string; ok?: boolean } {
	for (const t of textOutputs) {
		const idx = t.indexOf(RESULT_SENTINEL);
		if (idx === -1) {
			continue;
		}
		const jsonPart = t.slice(idx + RESULT_SENTINEL.length).trim();
		try {
			const parsed = JSON.parse(jsonPart) as any;
			return {
				parsed,
				ok: typeof parsed?.ok === 'boolean' ? parsed.ok : undefined,
				error: typeof parsed?.error === 'string' ? parsed.error : undefined,
				traceback: typeof parsed?.traceback === 'string' ? parsed.traceback : undefined
			};
		} catch {
			return { parsed: jsonPart };
		}
	}
	return {};
}

function normalizeUserCode(code: string): string {
	// Make notebook cells readable: remove a common leading indentation.
	const lines = code.replace(/\r\n/g, '\n').split('\n');
	// Trim leading/trailing blank lines
	while (lines.length > 0 && lines[0].trim() === '') {
		lines.shift();
	}
	while (lines.length > 0 && lines[lines.length - 1].trim() === '') {
		lines.pop();
	}

	let minIndent: number | undefined;
	for (const line of lines) {
		if (line.trim() === '') {
			continue;
		}
		const m = line.match(/^[\t ]+/);
		const indent = m ? m[0].length : 0;
		minIndent = minIndent === undefined ? indent : Math.min(minIndent, indent);
	}
	const cut = minIndent ?? 0;
	const normalized = lines.map(l => (cut > 0 ? l.slice(cut) : l)).join('\n');
	return normalized.endsWith('\n') ? normalized : `${normalized}\n`;
}

const SETUP_START = '# --- wandas-agent: setup ---';
const ANALYSIS_START = '# --- wandas-agent: analysis ---';

function splitSections(text: string): { setup: string; analysis: string } {
	const normalized = text.replace(/\r\n/g, '\n');
	const setupIdx = normalized.indexOf(SETUP_START);
	const analysisIdx = normalized.indexOf(ANALYSIS_START);
	if (setupIdx === -1 || analysisIdx === -1 || analysisIdx < setupIdx) {
		// No markers: treat all existing text as setup so rerun keeps prior definitions.
		return { setup: normalized.trim() ? `${normalized.trimEnd()}\n` : '', analysis: '' };
	}
	const afterSetupMarker = setupIdx + SETUP_START.length;
	const afterAnalysisMarker = analysisIdx + ANALYSIS_START.length;
	const setup = normalized.slice(afterSetupMarker, analysisIdx).trim();
	const analysis = normalized.slice(afterAnalysisMarker).trim();
	return {
		setup: setup ? `${setup}\n` : '',
		analysis: analysis ? `${analysis}\n` : ''
	};
}

function looksLikeSetupCode(code: string): boolean {
	// Heuristic: if code imports or constructs frames / uses from_numpy etc, treat as setup.
	const c = code;
	if (/^\s*(import|from)\s+/m.test(c)) {
		return true;
	}
	if (/\bwd\.(from_\w+|ChannelFrame|\w*Frame)\b/.test(c)) {
		return true;
	}
	// Creating base signals often assigns arrays
	if (/^\s*\w+\s*=\s*.+/m.test(c) && /\b(np\.|numpy\.)/.test(c)) {
		return true;
	}
	return false;
}

function composeCell(setup: string, analysis: string): string {
	const s = setup.trimEnd();
	const a = analysis.trimEnd();
	let out = `${SETUP_START}\n`;
	if (s) {
		out += `${s}\n`;
	}
	out += `\n${ANALYSIS_START}\n`;
	if (a) {
		out += `${a}\n`;
	}
	return out.endsWith('\n') ? out : `${out}\n`;
}

function mergeForReproducibility(existingText: string, newSnippet: string): string {
	const existing = splitSections(existingText);
	const snippet = normalizeUserCode(newSnippet);

	// Keep the cell compact: replace only the relevant section.
	// - setup snippet => replace setup, keep analysis
	// - otherwise => keep setup, replace analysis
	if (looksLikeSetupCode(snippet)) {
		return composeCell(snippet, existing.analysis || '');
	}
	return composeCell(existing.setup || '', snippet);
}

function truncateForBackup(text: string, maxChars: number): string {
	if (text.length <= maxChars) {
		return text;
	}
	return `${text.slice(0, maxChars)}\n…(truncated)`;
}

async function pushCellBackup(editor: vscode.NotebookEditor, cellIndex: number, previousText: string): Promise<void> {
	const cell = editor.notebook.getCells()[cellIndex];
	const meta = (cell.metadata ?? {}) as Record<string, unknown>;
	const existing = Array.isArray(meta[BACKUPS_METADATA_KEY]) ? (meta[BACKUPS_METADATA_KEY] as unknown[]) : [];
	const backups = existing
		.map(v => (typeof v === 'string' ? v : ''))
		.filter(Boolean);

	const entry = truncateForBackup(previousText, 20_000);
	if (backups.length > 0 && backups[backups.length - 1] === entry) {
		return;
	}
	backups.push(entry);
	while (backups.length > 3) {
		backups.shift();
	}

	const newMeta = { ...meta, [BACKUPS_METADATA_KEY]: backups };
	const edit = new vscode.WorkspaceEdit();
	edit.set(editor.notebook.uri, [vscode.NotebookEdit.updateCellMetadata(cellIndex, newMeta)]);
	await vscode.workspace.applyEdit(edit);
}

export async function runPythonInActiveNotebook(
	code: string,
	token: vscode.CancellationToken,
	options?: { timeoutMs?: number; maxResultChars?: number }
): Promise<NotebookPythonRunResult> {
	const editor = getActiveNotebookEditor();
	const cell = await ensureAgentCell(editor);

	const notebookUri = editor.notebook.uri;
	const cellDocUri = cell.document.uri;
	const cellIndex = editor.notebook.getCells().findIndex(c => c.document.uri.toString() === cellDocUri.toString());
	if (cellIndex < 0) {
		throw new Error('wandas-agent 用セルのインデックス解決に失敗しました。');
	}

	const existingText = readCellText(cell);
	const mergedText = mergeForReproducibility(existingText, code);
	if (existingText.trim() && existingText !== mergedText) {
		await pushCellBackup(editor, cellIndex, existingText);
	}
	await overwriteCellText(cell, mergedText);

	const beforeSummary = editor.notebook.getCells()[cellIndex].executionSummary;
	const before = {
		executionOrder: beforeSummary?.executionOrder,
		endTime: beforeSummary?.timing?.endTime,
		outputsSig: outputSignature(editor.notebook.getCells()[cellIndex])
	};

	await executeCell(editor, cellIndex);
	const { success } = await waitForCellExecutionToEndPolling(
		editor,
		cellIndex,
		token,
		options?.timeoutMs ?? 60_000,
		before
	);

	// Re-fetch cell to read latest outputs
	const latestCell = editor.notebook.getCells()[cellIndex];
	const { textOutputs, imagesPngCount } = extractOutputs(latestCell);
	const notebookError = extractNotebookError(latestCell);
	const parsed = parseSentinel(textOutputs);

	const combinedText = truncate(textOutputs.join('\n\n'), options?.maxResultChars ?? 8000);

	return {
		ok: parsed.ok ?? (success !== false),
		success,
		text: combinedText,
		textOutputs,
		imagesPngCount,
		writtenCode: mergedText,
		parsedResult: parsed.parsed,
		error: parsed.error,
		traceback: parsed.traceback,
		notebookError
	};
}
