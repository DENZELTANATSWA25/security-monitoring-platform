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
  within,
} from "@testing-library/react";

import IncidentsPage from "./page";

import { useIncidents } from "@/hooks/use-incidents";

import type { Incident } from "@/types/incident";

vi.mock("@/hooks/use-incidents", () => ({
  useIncidents: vi.fn(),
}));

const mockedUseIncidents = vi.mocked(useIncidents);
const refetch = vi.fn();

const sampleIncident: Incident = {
  id: 101,
  title: "Suspicious authentication activity",
  description: "Repeated failed authentication attempts",
  severity: "HIGH",
  status: "OPEN",
  assigned_to: null,
  assigned_user_id: null,
  event_id: 501,
  created_at: "2026-10-01T12:00:00Z",
  updated_at: "2026-10-01T12:00:00Z",
};

function mockIncidents(
  overrides: Record<string, unknown> = {},
) {
  mockedUseIncidents.mockReturnValue({
    data: [sampleIncident],
    isLoading: false,
    isFetching: false,
    error: null,
    refetch,
    ...overrides,
  } as unknown as ReturnType<typeof useIncidents>);
}

describe("IncidentsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIncidents();
  });

  it("requests the first page using lookahead pagination", () => {
    render(<IncidentsPage />);

    expect(mockedUseIncidents).toHaveBeenCalledWith({
      limit: 11,
      offset: 0,
      sort_order: "desc",
    });
  });

  it("displays incident information and investigation link", () => {
    render(<IncidentsPage />);

    const link = screen.getByRole("link", {
      name: /Suspicious authentication activity/,
    });

    expect(link).toHaveAttribute(
      "href",
      "/incidents/101",
    );

    expect(
      within(link).getByText("HIGH"),
    ).toBeInTheDocument();

    expect(
      within(link).getByText("Unassigned"),
    ).toBeInTheDocument();

    expect(
      within(link).getByText("Event #501"),
    ).toBeInTheDocument();
  });

  it("submits a trimmed search term", () => {
    render(<IncidentsPage />);

    fireEvent.change(
      screen.getByPlaceholderText("Search incidents..."),
      {
        target: { value: "  authentication  " },
      },
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Search" }),
    );

    expect(mockedUseIncidents).toHaveBeenLastCalledWith(
      expect.objectContaining({
        search: "authentication",
        offset: 0,
      }),
    );
  });

  it("filters incidents by status", () => {
    render(<IncidentsPage />);

    fireEvent.change(screen.getByLabelText("Status"), {
      target: { value: "IN_PROGRESS" },
    });

    expect(mockedUseIncidents).toHaveBeenLastCalledWith(
      expect.objectContaining({
        status: "IN_PROGRESS",
      }),
    );
  });

  it("filters incidents by severity", () => {
    render(<IncidentsPage />);

    fireEvent.change(screen.getByLabelText("Severity"), {
      target: { value: "CRITICAL" },
    });

    expect(mockedUseIncidents).toHaveBeenLastCalledWith(
      expect.objectContaining({
        severity: "CRITICAL",
      }),
    );
  });

  it("filters incidents assigned to a specific user", () => {
    render(<IncidentsPage />);

    fireEvent.change(screen.getByLabelText("Assignment"), {
      target: { value: "assigned" },
    });

    fireEvent.change(
      screen.getByLabelText("Assigned user ID"),
      {
        target: { value: "42" },
      },
    );

    expect(mockedUseIncidents).toHaveBeenLastCalledWith(
      expect.objectContaining({
        assigned_user_id: 42,
      }),
    );
  });

  it("uses the unassigned API filter", () => {
    render(<IncidentsPage />);

    fireEvent.change(screen.getByLabelText("Assignment"), {
      target: { value: "unassigned" },
    });

    expect(mockedUseIncidents).toHaveBeenLastCalledWith(
      expect.objectContaining({
        unassigned: true,
      }),
    );

    const lastCall = mockedUseIncidents.mock.lastCall;

    expect(lastCall).toBeDefined();

    expect(lastCall?.[0]).not.toHaveProperty(
      "assigned_user_id",
    );
  });

  it("rejects invalid assigned user IDs", () => {
    render(<IncidentsPage />);

    fireEvent.change(screen.getByLabelText("Assignment"), {
      target: { value: "assigned" },
    });

    expect(
      screen.getByText(
        "Enter a valid positive user ID to filter incidents.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        "Suspicious authentication activity",
      ),
    ).not.toBeInTheDocument();
  });

  it("resets filters and sorting", () => {
    render(<IncidentsPage />);

    fireEvent.change(screen.getByLabelText("Status"), {
      target: { value: "RESOLVED" },
    });

    fireEvent.change(screen.getByLabelText("Sort"), {
      target: { value: "asc" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Reset" }),
    );

    expect(mockedUseIncidents).toHaveBeenLastCalledWith({
      limit: 11,
      offset: 0,
      sort_order: "desc",
    });
  });

  it("advances pagination by 10 records", () => {
    const incidents: Incident[] = Array.from(
      { length: 11 },
      (_, index) => ({
        ...sampleIncident,
        id: index + 1,
        title: `Incident ${index + 1}`,
      }),
    );

    mockIncidents({ data: incidents });

    render(<IncidentsPage />);

    fireEvent.click(
      screen.getByRole("button", { name: "Next" }),
    );

    expect(
      screen.getByText("Page 2"),
    ).toBeInTheDocument();

    expect(mockedUseIncidents).toHaveBeenLastCalledWith(
      expect.objectContaining({
        limit: 11,
        offset: 10,
      }),
    );
  });

  it("displays an empty state", () => {
    mockIncidents({ data: [] });

    render(<IncidentsPage />);

    expect(
      screen.getByText("No matching incidents found."),
    ).toBeInTheDocument();
  });

  it("displays a loading state", () => {
    mockIncidents({
      data: undefined,
      isLoading: true,
    });

    render(<IncidentsPage />);

    expect(
      screen.getByText("Loading incidents..."),
    ).toBeInTheDocument();
  });

  it("displays an API error", () => {
    mockIncidents({
      data: undefined,
      error: new Error("Network failure"),
    });

    render(<IncidentsPage />);

    expect(
      screen.getByText("Failed to load incidents."),
    ).toBeInTheDocument();
  });

  it("allows users to refresh the incident list", () => {
    render(<IncidentsPage />);

    fireEvent.click(
      screen.getByRole("button", { name: "Refresh" }),
    );

    expect(refetch).toHaveBeenCalledOnce();
  });
});