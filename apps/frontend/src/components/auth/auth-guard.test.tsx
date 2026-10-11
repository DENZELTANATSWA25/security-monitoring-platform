import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";

import AuthGuard from "./auth-guard";
import { removeAccessToken, setAccessToken } from "@/lib/auth";
import { useCurrentUser } from "@/hooks/use-users";

const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
  }),
}));

vi.mock("@/hooks/use-users", () => ({
  useCurrentUser: vi.fn(),
}));

vi.mock("@/lib/auth-config", () => ({
  DEV_AUTH_BYPASS: false,
}));

const mockedUseCurrentUser = vi.mocked(useCurrentUser);

function renderProtectedContent() {
  return render(
    <AuthGuard>
      <div>Protected dashboard content</div>
    </AuthGuard>
  );
}

describe("AuthGuard", () => {
  beforeEach(() => {
    localStorage.clear();
    mockReplace.mockReset();

    mockedUseCurrentUser.mockReturnValue({
      data: undefined,
      isPending: true,
      isError: false,
    } as ReturnType<typeof useCurrentUser>);
  });

  it("redirects unauthenticated users to login", async () => {
    renderProtectedContent();

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/login");
    });

    expect(
      screen.queryByText("Protected dashboard content")
    ).not.toBeInTheDocument();
  });

  it("renders protected content for an authenticated user", () => {
    setAccessToken("dummy-test-token");

    mockedUseCurrentUser.mockReturnValue({
      data: {
        id: 1,
        email: "admin@example.test",
        username: "test-admin",
        full_name: "Test Administrator",
        role: "admin",
        is_active: true,
        is_verified: true,
        last_login: null,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
      isPending: false,
      isError: false,
    } as ReturnType<typeof useCurrentUser>);

    renderProtectedContent();

    expect(
      screen.getByText("Protected dashboard content")
    ).toBeInTheDocument();

    expect(mockReplace).not.toHaveBeenCalled();
  });

  it("shows a loading state while verifying authentication", () => {
    setAccessToken("dummy-test-token");

    renderProtectedContent();

    expect(
      screen.getByText("Checking authentication...")
    ).toBeInTheDocument();

    expect(
      screen.queryByText("Protected dashboard content")
    ).not.toBeInTheDocument();
  });

  it("redirects when current-user verification fails", async () => {
    setAccessToken("dummy-test-token");

    mockedUseCurrentUser.mockReturnValue({
      data: undefined,
      isPending: false,
      isError: true,
    } as ReturnType<typeof useCurrentUser>);

    renderProtectedContent();

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/login");
    });

    expect(
      screen.queryByText("Protected dashboard content")
    ).not.toBeInTheDocument();
  });

  it("stops displaying protected content after logout", async () => {
    setAccessToken("dummy-test-token");

    mockedUseCurrentUser.mockReturnValue({
      data: {
        id: 1,
        email: "admin@example.test",
        username: "test-admin",
        full_name: "Test Administrator",
        role: "admin",
        is_active: true,
        is_verified: true,
        last_login: null,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
      isPending: false,
      isError: false,
    } as ReturnType<typeof useCurrentUser>);

    renderProtectedContent();

    expect(
      screen.getByText("Protected dashboard content")
    ).toBeInTheDocument();

    act(() => {
      removeAccessToken();
    });

    await waitFor(() => {
      expect(
        screen.queryByText("Protected dashboard content")
      ).not.toBeInTheDocument();
    });

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/login");
    });
  });
});