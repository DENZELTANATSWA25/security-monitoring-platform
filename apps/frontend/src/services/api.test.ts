import {
  AxiosError,
  type AxiosAdapter,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";

import {
  beforeEach,
  describe,
  expect,
  it,
} from "vitest";

import { api } from "./api";

import {
  getAccessToken,
  setAccessToken,
} from "@/lib/auth";

type TestResponse = {
  status: number;
  data?: unknown;
};

function createMockAdapter({
  status,
  data = {},
}: TestResponse): AxiosAdapter {
  return async (config: InternalAxiosRequestConfig) => {
    if (status >= 400) {
      throw new AxiosError(
        `Request failed with status code ${status}`,
        AxiosError.ERR_BAD_RESPONSE,
        config,
        undefined,
        {
          data,
          status,
          statusText: "Error",
          headers: {},
          config,
        }
      );
    }

    return {
      data,
      status,
      statusText: "OK",
      headers: {},
      config,
    };
  };
}

async function makeRequest(
  adapter: AxiosAdapter,
  config: AxiosRequestConfig = {}
) {
  return api.get("/test-endpoint", {
    ...config,
    adapter,
  });
}

describe("API authentication interceptors", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("attaches the current bearer token to authenticated requests", async () => {
    setAccessToken("test-token");

    let authorizationHeader: string | undefined;

    const adapter: AxiosAdapter = async (config) => {
      authorizationHeader =
        config.headers.get("Authorization")?.toString();

      return {
        data: {},
        status: 200,
        statusText: "OK",
        headers: {},
        config,
      };
    };

    await makeRequest(adapter);

    expect(authorizationHeader).toBe("Bearer test-token");
  });

  it("does not attach a bearer token when unauthenticated", async () => {
    let authorizationHeader: string | undefined;

    const adapter: AxiosAdapter = async (config) => {
      authorizationHeader =
        config.headers.get("Authorization")?.toString();

      return {
        data: {},
        status: 200,
        statusText: "OK",
        headers: {},
        config,
      };
    };

    await makeRequest(adapter);

    expect(authorizationHeader).toBeUndefined();
  });

  it("removes the current token when the backend returns 401", async () => {
    setAccessToken("expired-token");

    await expect(
      makeRequest(createMockAdapter({ status: 401 }))
    ).rejects.toBeInstanceOf(AxiosError);

    expect(getAccessToken()).toBeNull();
  });

  it("preserves a newer session when an older request returns 401", async () => {
    setAccessToken("old-token");

    const adapter: AxiosAdapter = async (config) => {
      setAccessToken("new-token");

      throw new AxiosError(
        "Unauthorized",
        AxiosError.ERR_BAD_RESPONSE,
        config,
        undefined,
        {
          data: {},
          status: 401,
          statusText: "Unauthorized",
          headers: {},
          config,
        }
      );
    };

    await expect(
      makeRequest(adapter)
    ).rejects.toBeInstanceOf(AxiosError);

    expect(getAccessToken()).toBe("new-token");
  });

  it.each([403, 500])(
    "preserves authentication when the backend returns %i",
    async (status) => {
      setAccessToken("valid-token");

      await expect(
        makeRequest(createMockAdapter({ status }))
      ).rejects.toBeInstanceOf(AxiosError);

      expect(getAccessToken()).toBe("valid-token");
    }
  );
});