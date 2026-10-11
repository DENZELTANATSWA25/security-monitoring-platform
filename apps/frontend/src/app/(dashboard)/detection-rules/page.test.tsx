import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  render,
  screen,
} from "@testing-library/react";

import DetectionRulesPage from "./page";

import { useCurrentUser } from "@/hooks/use-users";

vi.mock("@/hooks/use-users", () => ({
  useCurrentUser: vi.fn(),
}));

vi.mock(
  "@/components/detection-rules/detection-rules-manager",
  () => ({
    default: () => (
      <div data-testid="detection-rules-manager">
        Detection Rules Manager
      </div>
    ),
  }),
);

const mockedUseCurrentUser = vi.mocked(useCurrentUser);

function mockCurrentUser(
  role: "admin" | "analyst" | "viewer",
) {
  mockedUseCurrentUser.mockReturnValue({
    data: {
      id: 1,
      username: "testuser",
      role,
    },
    isLoading: false,
    isPending: false,
    error: null,
  } as ReturnType<typeof useCurrentUser>);
}

describe("DetectionRulesPage authorization", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCurrentUser("admin");
  });

  it("allows administrators to access detection rules", () => {
    render(<DetectionRulesPage />);

    expect(
      screen.getByTestId("detection-rules-manager"),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: "Detection Rules",
      }),
    ).toBeInTheDocument();
  });

  it("denies analysts access", () => {
    mockCurrentUser("analyst");

    render(<DetectionRulesPage />);

    expect(
      screen.getByText("Access Denied"),
    ).toBeInTheDocument();

    expect(
      screen.queryByTestId("detection-rules-manager"),
    ).not.toBeInTheDocument();
  });

  it("denies viewers access", () => {
    mockCurrentUser("viewer");

    render(<DetectionRulesPage />);

    expect(
      screen.getByText("Access Denied"),
    ).toBeInTheDocument();

    expect(
      screen.queryByTestId("detection-rules-manager"),
    ).not.toBeInTheDocument();
  });

  it("waits for permissions to load", () => {
    mockedUseCurrentUser.mockReturnValue({
      data: undefined,
      isLoading: true,
      isPending: true,
      error: null,
    } as ReturnType<typeof useCurrentUser>);

    render(<DetectionRulesPage />);

    expect(
      screen.getByText("Loading account permissions..."),
    ).toBeInTheDocument();

    expect(
      screen.queryByTestId("detection-rules-manager"),
    ).not.toBeInTheDocument();
  });

  it("handles permission verification failures", () => {
    mockedUseCurrentUser.mockReturnValue({
      data: undefined,
      isLoading: false,
      isPending: false,
      error: new Error("Unable to retrieve user"),
    } as ReturnType<typeof useCurrentUser>);

    render(<DetectionRulesPage />);

    expect(
      screen.getByText("Unable to verify permissions"),
    ).toBeInTheDocument();

    expect(
      screen.queryByTestId("detection-rules-manager"),
    ).not.toBeInTheDocument();
  });
});