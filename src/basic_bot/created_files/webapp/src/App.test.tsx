import { describe, it, beforeAll, afterAll } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { CentralHubTestClient } from "../testHelpers/centralHub";

import App from "./App";

/*

There are a couple of strategies to test the webapp.  From a high level, you can test
the integration of the webapp with the central hub.  Or from individual react components,
you can design the components so that they accept data from hubstate as props but know
little or nothing about the central hub.  This way you can test the components in isolation
from the central hub.

This test demonstrates the first strategy.  It tests the integration of the webapp with the
central hub.  It uses the CentralHubTestClient to start a central hub process and then
the App component connects to that server.  None of the other backend services are started.
The test itself could, for example, test that the App component renders correctly given a
certain hub state or change to hubstate that the test inself triggers using the
CentralHubTestClient sendHubStateUpdate method.

See also https://github.com/littlebee/daphbot-due/blob/main/webapp/src/App.test.tsx for
a more extensive exameple of testing the webapp integration testing.

*/

describe("App", () => {
    let hubClient: CentralHubTestClient;

    beforeAll(async () => {
        hubClient = new CentralHubTestClient("App.test.tsx");
        await hubClient.startTestHub();
    });

    afterAll(async () => {
        await hubClient.stopTestHub();
    });

    async function renderApp() {
        const hubPort = hubClient.getHubPort();
        console.log("App.test.tsx", { hubPort });
        // autoReconnect is set to false to prevent the app from throwing an error on teardown
        render(<App hubPort={hubPort} autoReconnect={false} />);

        // Wait for the app to connect to the hub and render the "online" status
        await waitFor(() => screen.getByText(/online/i));
    }

    it("renders the App component", async () => {
        await renderApp();
        screen.getAllByText("basic_bot");
    });

    // Add your tests here
});
