import * as path from 'path';
import Mocha = require('mocha');
import { glob } from 'glob';

export async function run(): Promise<void> {
    const mocha = new Mocha({
        ui: 'tdd',
        color: true
    });

    // out/test/suite/index.js から見た out/test 配下を探索
    const testsRoot = path.resolve(__dirname, '..');
    const files = await glob('**/*.test.js', { cwd: testsRoot });
    for (const f of files) {
        mocha.addFile(path.resolve(testsRoot, f));
    }

    await new Promise<void>((resolve, reject) => {
        try {
            mocha.run((failures: number) => {
                if (failures > 0) {
                    reject(new Error(`${failures} tests failed.`));
                } else {
                    resolve();
                }
            });
        } catch (err) {
            reject(err);
        }
    });
}
