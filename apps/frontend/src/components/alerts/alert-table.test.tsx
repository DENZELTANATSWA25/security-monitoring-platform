import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";

import AlertTable from "./alert-table";

import {
  useAlerts,
  useResolveAlert,
} from "@/hooks/use-alerts";

import { useCurrentUser } from "@/hooks/use-users";

import type { Alert } from "@/types/alert";

vi.mock("@/hooks/use-alerts", () => ({
  useAlerts: vi.fn(),
  useResolveAlert: vi.fn(),
}));

vi.mock("@/hooks/use-users", () => ({
  useCurrentUser: vi.fn(),
}));

// Keep investigation dialog behaviour separate from table tests.
vi.mock("./alert-details", () => ({
  default: ({
    alertId,
    open,
  }: {
    alertId: number | null;
    open: boolean;
  }) =>
    open && alertId !== null ? (
      <div role="dialog" aria-label="Alert investigation">
        Investigating alert {alertId}
      </div>
    ) : null,
}));

const mockedUseAlerts = vi.mocked(useAlerts);
const mockedUseResolveAlert = vi.mocked(useResolveAlert);
const mockedUseCurrentUser = vi.mocked(useCurrentUser);

const refetch = vi.fn();
const mutateAsync = vi.fn();

const sampleAlert: Alert = {
  id: 101,
  alert_type: "BRUTE_FORCE",
  severity: "CRITICAL",
  message: "Repeated failed login attempts detected",
  resolved: false,
  created_at: "2026-10-01T12:00:00Z",
};

function mockAlerts(
  overrides: Record<string, unknown> = {}
) {
  mockedUseAlerts.mockReturnValue({
    data: [sampleAlert],
    isLoading: false,
    isError: false,
    isFetching: false,
    refetch,
    ...overrides,
  } as unknown as ReturnType<typeof useAlerts>);
}

function mockRole(
  role: "admin" | "analyst" | "viewer"
) {
  mockedUseCurrentUser.mockReturnValue({
    data: { role },
  } as ReturnType<typeof useCurrentUser>);
}

describe("AlertTable", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockAlerts();
    mockRole("analyst");

    mutateAsync.mockResolvedValue({
      ...sampleAlert,
      resolved: true,
    });

    mockedUseResolveAlert.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useResolveAlert>);
  });

  it("requests the first page using lookahead pagination", () => {
    render(<AlertTable />);

    expect(mockedUseAlerts).toHaveBeenCalledWith(
      {
        limit: 21,
        offset: 0,
        sort_order: "desc",
      },
      { enabled: true }
    );
  });

  it("filters open alerts correctly", () => {
    render(<AlertTable />);

    fireEvent.change(screen.getByLabelText("Status"), {
      target: { value: "open" },
    });

    expect(mockedUseAlerts).toHaveBeenLastCalledWith(
      expect.objectContaining({
        resolved: false,
        offset: 0,
      }),
      { enabled: true }
    );
  });

  it("filters alerts by severity", () => {
    render(<AlertTable />);

    fireEvent.change(screen.getByLabelText("Severity"), {
      target: { value: "CRITICAL" },
    });

    expect(mockedUseAlerts).toHaveBeenLastCalledWith(
      expect.objectContaining({
        severity: "CRITICAL",
      }),
      { enabled: true }
    );
  });

  it("submits trimmed search terms", () => {
    render(<AlertTable />);

    fireEvent.change(
      screen.getByPlaceholderText("Search alerts..."),
      {
        target: { value: "  brute force  " },
      }
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Search" })
    );

    expect(mockedUseAlerts).toHaveBeenLastCalledWith(
      expect.objectContaining({
        search: "brute force",
      }),
      { enabled: true }
    );
  });

  it("resets filters and sorting", () => {
    render(<AlertTable />);

    fireEvent.change(screen.getByLabelText("Status"), {
      target: { value: "resolved" },
    });

    fireEvent.change(screen.getByLabelText("Sort"), {
      target: { value: "asc" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Reset" })
    );

    expect(mockedUseAlerts).toHaveBeenLastCalledWith(
      {
        limit: 21,
        offset: 0,
        sort_order: "desc",
      },
      { enabled: true }
    );
  });

  it("opens investigation details for the selected alert", () => {
    render(<AlertTable />);

    const row = screen.getByText("101").closest("tr");

    expect(row).not.toBeNull();

    fireEvent.click(row!);

    expect(
      screen.getByRole("dialog", {
        name: "Alert investigation",
      })
    ).toHaveTextContent("Investigating alert 101");
  });

  it.each(["admin", "analyst"] as const)(
    "allows %s users to resolve alerts",
    async (role) => {
      mockRole(role);

      render(<AlertTable />);

      fireEvent.click(
        screen.getByRole("button", { name: "Resolve" })
      );

      await waitFor(() => {
        expect(mutateAsync).toHaveBeenCalledWith(101);
      });
    }
  );

  it("does not expose resolution actions to viewers", () => {
    mockRole("viewer");

    render(<AlertTable />);

    expect(
      screen.queryByRole("button", { name: "Resolve" })
    ).not.toBeInTheDocument();
  });

  it("does not offer resolution for already resolved alerts", () => {
    mockAlerts({
      data: [{ ...sampleAlert, resolved: true }],
    });

    render(<AlertTable />);

    expect(
      screen.queryByRole("button", { name: "Resolve" })
    ).not.toBeInTheDocument();
  });

  it("shows an error when alert resolution fails", async () => {
    mutateAsync.mockRejectedValue(
      new Error("Resolution failed")
    );

    render(<AlertTable />);

    fireEvent.click(
      screen.getByRole("button", { name: "Resolve" })
    );

    expect(
      await screen.findByRole("alert")
    ).toHaveTextContent(
      "Failed to resolve alert #101. Please retry."
    );
  });

  it("shows an empty state when no alerts match", () => {
    mockAlerts({ data: [] });

    render(<AlertTable />);

    expect(
      screen.getByText("No matching alerts")
    ).toBeInTheDocument();
  });

  it("displays an API error and supports retry", () => {
    mockAlerts({
      data: undefined,
      isError: true,
    });

    render(<AlertTable />);

    expect(
      screen.getByText("Failed to load alerts.")
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Retry" })
    );

    expect(refetch).toHaveBeenCalledOnce();
  });

  it("prevents fetching when the date range is invalid", () => {
    render(<AlertTable />);

    fireEvent.change(
      screen.getByLabelText("Start Date"),
      {
        target: { value: "2026-10-10T12:00" },
      }
    );

    fireEvent.change(
      screen.getByLabelText("End Date"),
      {
        target: { value: "2026-10-09T12:00" },
      }
    );

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Start date must be earlier than or equal to end date."
    );

    expect(mockedUseAlerts).toHaveBeenLastCalledWith(
      expect.any(Object),
      { enabled: false }
    );
  });

  it("advances pagination by 20 records", () => {
    const alerts: Alert[] = Array.from(
      { length: 21 },
      (_, index) => ({
        ...sampleAlert,
        id: index + 1,
      })
    );

    mockAlerts({ data: alerts });

    render(<AlertTable />);

    fireEvent.click(
      screen.getByRole("button", { name: "Next" })
    );

    expect(
      screen.getByText("Page 2")
    ).toBeInTheDocument();

    expect(mockedUseAlerts).toHaveBeenLastCalledWith(
      expect.objectContaining({
        limit: 21,
        offset: 20,
      }),
      { enabled: true }
    );
  });

  it("shows a loading state", () => {
    mockAlerts({
      data: undefined,
      isLoading: true,
    });

    render(<AlertTable />);

    expect(
      screen.getByText("Loading alerts...")
    ).toBeInTheDocument();
  });
});