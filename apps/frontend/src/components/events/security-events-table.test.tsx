import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";

import SecurityEventsTable from "./security-events-table";

import { useEvents } from "@/hooks/use-events";

import type { SecurityEvent } from "@/types/event";

vi.mock("@/hooks/use-events", () => ({
  useEvents: vi.fn(),
}));

// Isolate the table tests from the investigation dialog implementation.
vi.mock("@/components/dashboard/event-details", () => ({
  default: ({
    event,
    open,
  }: {
    event: SecurityEvent | null;
    open: boolean;
  }) =>
    open && event ? (
      <div role="dialog" aria-label="Event investigation">
        <p>Investigating event {event.id}</p>
      </div>
    ) : null,
}));

const mockedUseEvents = vi.mocked(useEvents);

const refetch = vi.fn();

const sampleEvent: SecurityEvent = {
  id: 101,
  event_type: "SQL_INJECTION",
  severity: "CRITICAL",
  source: "web_application",
  message: "Suspicious SQL injection attempt detected",
  created_at: "2026-10-01T12:00:00Z",
};

function mockEvents(
  overrides: Record<string, unknown> = {}
) {
  mockedUseEvents.mockReturnValue({
    data: [sampleEvent],
    isLoading: false,
    isError: false,
    isFetching: false,
    refetch,
    ...overrides,
  } as unknown as ReturnType<typeof useEvents>);
}

describe("SecurityEventsTable", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockEvents();
  });

  it("requests the first page using lookahead pagination", () => {
    render(<SecurityEventsTable />);

    expect(mockedUseEvents).toHaveBeenCalledWith(
      expect.objectContaining({
        limit: 21,
        offset: 0,
        sort_order: "desc",
      }),
      { enabled: true }
    );
  });

  it("applies a severity filter", () => {
    render(<SecurityEventsTable />);

    fireEvent.change(screen.getByLabelText("Severity"), {
      target: { value: "CRITICAL" },
    });

    expect(mockedUseEvents).toHaveBeenLastCalledWith(
      expect.objectContaining({
        severity: "CRITICAL",
        offset: 0,
      }),
      { enabled: true }
    );
  });

  it("applies a search term only after submission", () => {
    render(<SecurityEventsTable />);

    const input = screen.getByPlaceholderText(
      "Search security events..."
    );

    fireEvent.change(input, {
      target: { value: "  injection  " },
    });

    expect(mockedUseEvents).toHaveBeenLastCalledWith(
      expect.not.objectContaining({
        search: expect.anything(),
      }),
      { enabled: true }
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Search" })
    );

    expect(mockedUseEvents).toHaveBeenLastCalledWith(
      expect.objectContaining({
        search: "injection",
      }),
      { enabled: true }
    );
  });

  it("resets filters and sorting", () => {
    render(<SecurityEventsTable />);

    fireEvent.change(screen.getByLabelText("Severity"), {
      target: { value: "ERROR" },
    });

    fireEvent.change(screen.getByLabelText("Sort"), {
      target: { value: "asc" },
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Reset" })
    );

    expect(mockedUseEvents).toHaveBeenLastCalledWith(
      {
        limit: 21,
        offset: 0,
        sort_order: "desc",
      },
      { enabled: true }
    );
  });

  it("displays an empty state when no events are returned", () => {
    mockEvents({ data: [] });

    render(<SecurityEventsTable />);

    expect(
      screen.getByText("No security events found")
    ).toBeInTheDocument();
  });

  it("displays an error and supports retrying", () => {
    mockEvents({
      data: undefined,
      isError: true,
    });

    render(<SecurityEventsTable />);

    expect(
      screen.getByText("Failed to load security events.")
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Retry" })
    );

    expect(refetch).toHaveBeenCalledOnce();
  });

  it("opens investigation details for the selected event", () => {
    render(<SecurityEventsTable />);

    const eventRow = screen.getByText("101").closest("tr");

    expect(eventRow).not.toBeNull();

    fireEvent.click(eventRow!);

    const dialog = screen.getByRole("dialog", {
      name: "Event investigation",
    });

    expect(
      within(dialog).getByText("Investigating event 101")
    ).toBeInTheDocument();
  });

  it("advances pagination by 20 records", () => {
    const events: SecurityEvent[] = Array.from(
      { length: 21 },
      (_, index) => ({
        ...sampleEvent,
        id: index + 1,
      })
    );

    mockEvents({ data: events });

    render(<SecurityEventsTable />);

    expect(
      screen.getByText("Page 1")
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Next" })
    );

    expect(
      screen.getByText("Page 2")
    ).toBeInTheDocument();

    expect(mockedUseEvents).toHaveBeenLastCalledWith(
      expect.objectContaining({
        limit: 21,
        offset: 20,
      }),
      { enabled: true }
    );
  });

  it("prevents fetching when the date range is invalid", () => {
    render(<SecurityEventsTable />);

    fireEvent.change(screen.getByLabelText("Start Date"), {
      target: { value: "2026-10-10T12:00" },
    });

    fireEvent.change(screen.getByLabelText("End Date"), {
      target: { value: "2026-10-09T12:00" },
    });

    expect(
      screen.getByRole("alert")
    ).toHaveTextContent(
      "Start date must be earlier than or equal to end date."
    );

    expect(mockedUseEvents).toHaveBeenLastCalledWith(
      expect.any(Object),
      { enabled: false }
    );
  });

  it("shows a loading state while fetching events", () => {
    mockEvents({
      data: undefined,
      isLoading: true,
    });

    render(<SecurityEventsTable />);

    expect(
      screen.getByText("Loading security events...")
    ).toBeInTheDocument();
  });
});