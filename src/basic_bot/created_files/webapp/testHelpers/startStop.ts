import { promisify } from "node:util";
import child_process from "node:child_process";
const execAsync = promisify(child_process.exec);

export async function startServices() {
    const threadId = process.env.VITEST_POOL_ID;
    const hubPort = 5150 + parseInt(threadId || "0");
    const envVars = [`BB_ENV=test`, `BB_HUB_PORT=${hubPort}`];

    // @ts-expect-error globalThis is a global object injected by vitest
    globalThis.hubPort = hubPort;

    // start all of the services used by the bot
    const cmd = `cd .. && ${envVars.join(" ")} bb_start`;
    console.log(
        `startStop.ts: starting services with command '${cmd}.  threadId: ${threadId}`
    );
    const { stdout, stderr } = await execAsync(cmd);
    console.log(`vitest.setup.ts beforeAll start.sh stdout: ${stdout}`);
    console.error(`vitest.setup.ts beforeAll start.sh stderr: ${stderr}`);
}

export async function stopServices() {
    const threadId = process.env.VITEST_POOL_ID;
    console.log("After all tests: stopping services", threadId);

    const { stderr, stdout } = await execAsync(`cd .. && BB_ENV=test bb_stop`);
    console.log(`vitest.setup.ts afterAll stdout: ${stdout}`);
    if (stderr) console.log(`vitest.setup.ts afterAll stderr: ${stderr}`);

    // @ts-expect-error globalThis is a global object injected by vitest
    delete globalThis.hubPort;
}
