import { describe, expect, it, vi } from "vitest";

vi.mock("./supabase", () => ({ supabase: {} }));
vi.stubEnv("VITE_API_BASE_URL", "http://api.test");

const { errorMessage } = await import("./api");

describe("errorMessage", () => {
  it("passes plain strings through", () => {
    expect(errorMessage("Quote not found", 404)).toBe("Quote not found");
  });

  it("reads message from object detail (ref conflict)", () => {
    expect(errorMessage({ message: "Ref no X already exists", suggested_ref: "Y" }, 409))
      .toBe("Ref no X already exists");
  });

  it("joins validation errors and strips pydantic prefix", () => {
    expect(errorMessage([{ msg: "Value error, Ref no is required" }, { msg: "Field required" }], 422))
      .toBe("Ref no is required; Field required");
  });

  it("explains network failure", () => {
    expect(errorMessage(null, 0)).toMatch(/reach the server/);
  });
});

describe("apiFetch", () => {
  it("sends JSON bodies as JSON but leaves file uploads to the browser", async () => {
    vi.doMock("./supabase", () => ({ supabase: { auth: { getSession: async () => ({ data: { session: null } }) } } }));
    vi.resetModules();
    const { apiFetch } = await import("./api");
    const calls: RequestInit[] = [];
    vi.stubGlobal("fetch", async (_url: string, init: RequestInit) => {
      calls.push(init);
      return new Response("{}", { status: 200 });
    });
    await apiFetch("/x", { method: "POST", body: JSON.stringify({ a: 1 }) });
    await apiFetch("/x", { method: "POST", body: new FormData() });
    const type = (i: RequestInit) => (i.headers as Record<string, string>)["Content-Type"];
    expect(type(calls[0])).toBe("application/json");
    expect(type(calls[1])).toBeUndefined();
    vi.unstubAllGlobals();
  });
});
