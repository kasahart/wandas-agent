import * as vscode from 'vscode';
import { execFile } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';
import * as fs from 'fs';

const execFileAsync = promisify(execFile);

export interface WandasSchema {
    classes: Record<string, {
        methods: Record<string, {
            args: string[];
            doc?: string;
        }>;
        doc?: string;
    }>;
    functions?: Record<string, {
        args: string[];
        doc?: string;
    }>;
    version: string;
}

async function getPythonPath(): Promise<string> {
    // ワークスペースの .venv 内の Python を探す
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders) {
        const rootPath = workspaceFolders[0].uri.fsPath;
        const venvPythonPath = path.join(rootPath, '.venv', 'bin', 'python3');
        if (fs.existsSync(venvPythonPath)) {
            return venvPythonPath;
        }
        const venvPythonPathExe = path.join(rootPath, '.venv', 'bin', 'python');
        if (fs.existsSync(venvPythonPathExe)) {
            return venvPythonPathExe;
        }
    }
    return 'python3';
}

export async function getWandasSchemaFromPython(): Promise<WandasSchema> {
    const pythonPath = await getPythonPath();
    const script = `
import json
import sys
import inspect

try:
    import wandas
except ImportError:
    print(json.dumps({"error": "wandas library not found"}))
    sys.exit(0)

def get_class_info(cls):
    methods = {}

    # Public methods
    for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
        if name.startswith('_'):
            continue
        try:
            spec = inspect.getfullargspec(member)
            methods[name] = {
                "args": spec.args,
                "doc": inspect.getdoc(member)
            }
        except Exception:
            continue

    # Include constructor docs/signature hints
    try:
        init = getattr(cls, "__init__", None)
        if init is not None:
            spec = inspect.getfullargspec(init)
            methods["__init__"] = {
                "args": spec.args,
                "doc": inspect.getdoc(init)
            }
    except Exception:
        pass
    return {
        "methods": methods,
        "doc": inspect.getdoc(cls)
    }

schema = {
    "version": getattr(wandas, "__version__", "unknown"),
    "classes": {},
    "functions": {}
}

# Inspect main classes in wandas
for name, obj in inspect.getmembers(wandas, predicate=inspect.isclass):
    if not name.startswith('_'):
        schema["classes"][name] = get_class_info(obj)

# Inspect module-level functions (e.g., from_numpy)
for name, obj in inspect.getmembers(wandas, predicate=inspect.isfunction):
    if name.startswith('_'):
        continue
    try:
        spec = inspect.getfullargspec(obj)
        schema["functions"][name] = {
            "args": spec.args,
            "doc": inspect.getdoc(obj)
        }
    except Exception:
        continue

print(json.dumps(schema))
`;

    try {
        const { stdout } = await execFileAsync(pythonPath, ['-u', '-c', script], {
            timeout: 15000
        });
        const result = JSON.parse(stdout);
        if (result.error) {
            throw new Error(result.error);
        }
        return result;
    } catch (error) {
        throw error;
    }
}
