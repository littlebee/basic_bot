import { describe, it, beforeAll, afterAll } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { getHubPort } from "../testHelpers/globalContext";
import { startServices, stopServices } from "../testHelpers/startStop";

import App from "./App";

async function renderApp() {
    const hubPort = getHubPort();
    console.log("App.test.tsx", { hubPort });
    // autoReconnect is set to false to prevent the app from throwing an error on teardown
    render(<App hubPort={hubPort} autoReconnect={false} />);
    await waitFor(() => screen.getByText(/online/i));
}

describe("App", () => {
    beforeAll(async () => {
        await startServices();
    });

    afterAll(async () => {
        await stopServices();
    });

    it("renders the App component", async () => {
        await renderApp();
        screen.getAllByText("basic_bot");
    });

    // Add your tests here
});
