import { promisify } from "node:util";
import child_process from "node:child_process";
const execAsync = promisify(child_process.exec);

export async function startServices() {
    const threadId = process.env.VITEST_POOL_ID;

    // @ts-expect-error globalThis is a global object injected by vitest
    globalThis.hubPort = 5150;

    // start all of the services used by the bot
    const cmd = `cd .. && BB_ENV=test BB_FILE_APPEND=${threadId} bb_start`;
    console.log(`startStop.ts: starting services with command '${cmd}'`);
    const { stdout, stderr } = await execAsync(cmd);
    console.log(`vitest.setup.ts beforeAll start.sh stdout: ${stdout}`);
    console.error(`vitest.setup.ts beforeAll start.sh stderr: ${stderr}`);
}

export async function stopServices() {
    console.log("After all tests: stopping services");
    const threadId = process.env.VITEST_POOL_ID;
    const { stderr, stdout } = await execAsync(
        `cd .. && BB_ENV=test BB_FILE_APPEND=${threadId} bb_stop`
    );
    console.log(`vitest.setup.ts afterAll stdout: ${stdout}`);
    if (stderr) console.log(`vitest.setup.ts afterAll stderr: ${stderr}`);

    // @ts-expect-error globalThis is a global object injected by vitest
    delete globalThis.hubPort;
}
