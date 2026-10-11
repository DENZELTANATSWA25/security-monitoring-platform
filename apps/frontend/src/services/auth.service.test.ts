import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import { api } from "./api";

import { login, logout } from "./auth.service";

import {
  getAccessToken,
  setAccessToken,
} from "@/lib/auth";

describe("Authentication service", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("sends credentials to the correct login endpoint", async () => {
    const credentials = {
      email: "test@example.test",
      password: "dummy-password",
    };

    const postSpy = vi.spyOn(api, "post").mockResolvedValue({
      data: {
        access_token: "dummy-access-token",
        token_type: "bearer",
      },
    });

    await login(credentials);

    expect(postSpy).toHaveBeenCalledWith(
      "/auth/login",
      credentials
    );
  });

  it("stores the access token after successful login", async () => {
    vi.spyOn(api, "post").mockResolvedValue({
      data: {
        access_token: "new-access-token",
        token_type: "bearer",
      },
    });

    await login({
      email: "test@example.test",
      password: "dummy-password",
    });

    expect(getAccessToken()).toBe("new-access-token");
  });

  it("does not replace the current token when login fails", async () => {
    setAccessToken("existing-token");

    vi.spyOn(api, "post").mockRejectedValue(
      new Error("Invalid credentials")
    );

    await expect(
      login({
        email: "test@example.test",
        password: "wrong-password",
      })
    ).rejects.toThrow("Invalid credentials");

    expect(getAccessToken()).toBe("existing-token");
  });

  it("removes the access token on logout", () => {
    setAccessToken("existing-token");

    logout();

    expect(getAccessToken()).toBeNull();
  });
});