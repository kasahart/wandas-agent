import * as vscode from 'vscode';
import { getWandasSchemaFromPython } from './pythonIntrospection';
import { runPythonInActiveNotebook } from './notebookRunner';

// 拡張機能が有効化されたときに呼ばれる関数
export function activate(context: vscode.ExtensionContext) {

    // チャット参加者 (Chat Participant) を登録
    const handler: vscode.ChatRequestHandler = async (
        request: vscode.ChatRequest,
        context: vscode.ChatContext,
        stream: vscode.ChatResponseStream,
        token: vscode.CancellationToken
    ) => {
        let schema;
        try {
            schema = await getWandasSchemaFromPython();
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            stream.markdown(`Unable to inspect Wandas library: ${message}\n\n`);
            return;
        }

        const systemInstruction = `
# Role
You are Wandas, an expert AI assistant for signal processing using the 'wandas' Python library.

# Capabilities
- **Autonomous Tools**: You have access to tools.
- **Signal Analysis**: You can perform complex signal processing tasks using method chaining.
- **Dask support**: You understand lazy loading and large data handling.

# Rules
1. **Safety First**: Verify parameters against the provided schema.
2. **Method Chaining**: Prefer the fluent interface (e.g., \`signal.filter().plot()\`).
3. **Dask Awareness**: Remember that data is lazy-loaded. Warn users before calling \`.compute()\` on potentially large data.
4. **Transparency**: If asked about previous operations, refer to the \`operation_history\` attribute.
5. **Notebook Execution**: When you need to run code, call the tool. The code runs in the user's currently active Jupyter notebook kernel, so it can access existing Python variables.
6. **Outputs**: Prefer producing (a) a short text summary and (b) plots inline in the notebook.
7. **Tool Code Format**: When calling the tool, provide ONLY the Python code as it should appear in a notebook cell (no surrounding try/except wrapper, no leading indentation).
8. **Reproducibility**: If your analysis depends on variables (e.g., 'signal', 'cf', 'sr'), ensure they are (re)created in the notebook via setup code at least once.
   Prefer: first tool call = setup (imports + test signal creation), subsequent tool calls = analysis (describe/plot).
9. **Variable Discipline**: Do not reference variables that are not defined in your setup or already present in the notebook. Avoid introducing new names like 'loaded' unless you also define them in setup. Prefer using existing variables like 'signal'.

# Library Schema
Here is the strict definition of the available tools:
${JSON.stringify(schema, null, 2)}
`;

        stream.progress('Processing your request...');
        await handleGeneralChat(request, systemInstruction, stream, token);

        stream.button({
            command: 'wandas.showVersion',
            title: `Wandas v${schema.version}`
        });
    };

    const wandasParticipant = vscode.chat.createChatParticipant('wandas.hello', handler);

    // アイコンの設定 (任意)
    wandasParticipant.iconPath = vscode.Uri.joinPath(context.extensionUri, 'images', 'logo.png');

    // コマンドの登録
    const showVersionCommand = vscode.commands.registerCommand('wandas.showVersion', () => {
        vscode.window.showInformationMessage('Wandas Agent v0.0.1');
    });

    const createPythonFileCommand = vscode.commands.registerCommand('wandas.createPythonFile', async (code: string) => {
        const doc = await vscode.workspace.openTextDocument({
            content: code,
            language: 'python'
        });
        await vscode.window.showTextDocument(doc);
    });

    context.subscriptions.push(wandasParticipant, showVersionCommand, createPythonFileCommand);
}

async function handleGeneralChat(request: vscode.ChatRequest, systemInstruction: string, stream: vscode.ChatResponseStream, token: vscode.CancellationToken) {
    const messages = [
        vscode.LanguageModelChatMessage.User(systemInstruction),
        vscode.LanguageModelChatMessage.User(request.prompt)
    ];

    const tools: vscode.LanguageModelChatTool[] = [
        {
            name: 'wandas_runNotebookCell',
            description: 'Execute Python code in the currently active Jupyter notebook (same kernel / same variables) and return the outputs.',
            inputSchema: {
                type: 'object',
                properties: {
                    code: {
                        type: 'string',
                        description: 'Python code to execute as a notebook cell. Do NOT include try/except wrappers; do NOT indent the whole snippet.'
                    }
                },
                required: ['code']
            }
        }
    ];

    try {
        const [model] = await vscode.lm.selectChatModels({ vendor: 'copilot' });
        if (!model) {
            stream.markdown('No suitable chat model found.');
            return;
        }

        const maxToolIterations = 8;
		let lastFailureSignature: string | undefined;
		let repeatedFailures = 0;
        for (let iteration = 0; iteration < maxToolIterations; iteration++) {
            const assistantParts: Array<vscode.LanguageModelTextPart | vscode.LanguageModelToolCallPart | vscode.LanguageModelDataPart> = [];
            const toolCalls: vscode.LanguageModelToolCallPart[] = [];

            const chatResponse = await model.sendRequest(messages, { tools }, token);
            for await (const part of chatResponse.stream) {
                if (part instanceof vscode.LanguageModelTextPart) {
                    stream.markdown(part.value);
                    assistantParts.push(part);
                } else if (part instanceof vscode.LanguageModelToolCallPart) {
                    toolCalls.push(part);
                    assistantParts.push(part);
                    stream.markdown(`\n\n> **Wandas Agent**: ツール \`${part.name}\` を実行中...\n\n`);
                }
            }

            // No tool call => done
            if (toolCalls.length === 0) {
                return;
            }

            // Provide the tool-call message back to the model, then provide the tool results as a User message.
            messages.push(vscode.LanguageModelChatMessage.Assistant(assistantParts));

            const toolResultParts: Array<vscode.LanguageModelToolResultPart | vscode.LanguageModelTextPart | vscode.LanguageModelDataPart> = [];
            for (const call of toolCalls) {
                if (call.name !== 'wandas_runNotebookCell') {
                    toolResultParts.push(
                        new vscode.LanguageModelToolResultPart(call.callId, [
                            new vscode.LanguageModelTextPart(JSON.stringify({ ok: false, error: `Unknown tool: ${call.name}` }))
                        ])
                    );
                    continue;
                }

                const { code } = call.input as { code: string };
                try {
                    const runResult = await runPythonInActiveNotebook(code, token, { timeoutMs: 90_000, maxResultChars: 12_000 });
                    stream.markdown(`\n\n> **Wandas Agent**: 実行結果: success=${String(runResult.success)} / images=${runResult.imagesPngCount}\n\n`);
					if (runResult.notebookError?.name || runResult.notebookError?.message) {
						const errLine = `${runResult.notebookError.name ?? 'Error'}: ${runResult.notebookError.message ?? ''}`.trim();
						stream.markdown(`\n\n> **Wandas Agent**: ノートブックエラー: ${errLine}\n\n`);
					}

					const failureSig = runResult.notebookError?.name || runResult.notebookError?.message
						? JSON.stringify({ name: runResult.notebookError?.name, message: runResult.notebookError?.message })
						: (runResult.success === false ? 'execution_failed' : undefined);
					if (failureSig && failureSig === lastFailureSignature) {
						repeatedFailures += 1;
					} else if (failureSig) {
						lastFailureSignature = failureSig;
						repeatedFailures = 1;
					} else {
						lastFailureSignature = undefined;
						repeatedFailures = 0;
					}
					if (repeatedFailures >= 3) {
						stream.markdown('\n\n⚠️ 同じ失敗が繰り返されたため停止しました。setup/analysis の変数名（例: signal/loaded）を揃えるよう指示してください。\n');
						return;
					}

                    toolResultParts.push(
                        new vscode.LanguageModelToolResultPart(call.callId, [
                            new vscode.LanguageModelTextPart(
                                JSON.stringify({
                                    ok: runResult.ok,
                                    success: runResult.success,
                                    imagesPngCount: runResult.imagesPngCount,
                                    parsedResult: runResult.parsedResult,
                                    error: runResult.error,
                                    traceback: runResult.traceback,
                                    notebookError: runResult.notebookError,
                                    writtenCode: runResult.writtenCode,
                                    text: runResult.text
                                })
                            )
                        ])
                    );
                } catch (error) {
                    const message = error instanceof Error ? error.message : String(error);
                    stream.markdown(`\n\n> **Wandas Agent**: 実行失敗: ${message}\n\n`);
                    toolResultParts.push(
                        new vscode.LanguageModelToolResultPart(call.callId, [
                            new vscode.LanguageModelTextPart(JSON.stringify({ ok: false, error: message }))
                        ])
                    );
                }
            }

            messages.push(vscode.LanguageModelChatMessage.User(toolResultParts));
        }

        stream.markdown('\n\n⚠️ ツール実行の反復回数上限に達したため停止しました。必要なら指示を具体化して再実行してください。\n');
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        stream.markdown(`LLM request failed: ${message}\n`);
    }
}

export function deactivate() { }