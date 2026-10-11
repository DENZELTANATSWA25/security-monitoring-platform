import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  getAccessToken,
  getAuthSnapshot,
  removeAccessToken,
  setAccessToken,
  subscribeToAuth,
} from "./auth";

describe("Authentication token utilities", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("returns null when no token exists", () => {
    expect(getAccessToken()).toBeNull();
  });

  it("stores and retrieves an access token", () => {
    setAccessToken("test-token");

    expect(getAccessToken()).toBe("test-token");
    expect(getAuthSnapshot()).toBe(true);
  });

  it("removes the access token", () => {
    setAccessToken("test-token");

    removeAccessToken();

    expect(getAccessToken()).toBeNull();
    expect(getAuthSnapshot()).toBe(false);
  });

  it("notifies subscribers when authentication changes", () => {
    const callback = vi.fn();

    const unsubscribe = subscribeToAuth(callback);

    setAccessToken("test-token");

    expect(callback).toHaveBeenCalledTimes(1);

    removeAccessToken();

    expect(callback).toHaveBeenCalledTimes(2);

    unsubscribe();

    setAccessToken("another-token");

    expect(callback).toHaveBeenCalledTimes(2);
  });
});