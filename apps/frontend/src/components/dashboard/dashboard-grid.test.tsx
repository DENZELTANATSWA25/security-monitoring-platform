import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";

import DashboardGrid from "./dashboard-grid";

import type { DashboardSummary } from "@/types/dashboard";

const dashboardData: DashboardSummary = {
  active_alerts: 12,
  critical_events: 4,
  total_events: 15240,
  resolved_alerts: 38,
  failed_logins_24h: 7,
  successful_logins_24h: 214,
};

describe("DashboardGrid", () => {
  it("renders the security overview heading", () => {
    render(<DashboardGrid data={dashboardData} />);

    expect(
      screen.getByRole("heading", {
        name: "Security Overview",
      })
    ).toBeInTheDocument();
  });

  it("displays all six security metrics", () => {
    render(<DashboardGrid data={dashboardData} />);

    expect(screen.getByText("Active Alerts")).toBeInTheDocument();
    expect(screen.getByText("Critical Events")).toBeInTheDocument();
    expect(screen.getByText("Total Events")).toBeInTheDocument();
    expect(screen.getByText("Resolved Alerts")).toBeInTheDocument();
    expect(screen.getByText("Failed Logins (24h)")).toBeInTheDocument();
    expect(screen.getByText("Successful Logins (24h)")).toBeInTheDocument();
  });

  it("displays the correct values for each metric", () => {
    render(<DashboardGrid data={dashboardData} />);

    const expectedMetrics = [
      ["Active Alerts", "12"],
      ["Critical Events", "4"],
      ["Total Events", "15,240"],
      ["Resolved Alerts", "38"],
      ["Failed Logins (24h)", "7"],
      ["Successful Logins (24h)", "214"],
    ];

    for (const [title, value] of expectedMetrics) {
      const metricLabel = screen.getByText(title);
      const card = metricLabel.closest("a");

      expect(card).not.toBeNull();
      expect(within(card!).getByText(value)).toBeInTheDocument();
    }
  });

  it("handles zero values correctly", () => {
    const emptyDashboard: DashboardSummary = {
      active_alerts: 0,
      critical_events: 0,
      total_events: 0,
      resolved_alerts: 0,
      failed_logins_24h: 0,
      successful_logins_24h: 0,
    };

    render(<DashboardGrid data={emptyDashboard} />);

    expect(screen.getAllByText("0")).toHaveLength(6);
  });

  it("provides links to relevant security pages", () => {
    render(<DashboardGrid data={dashboardData} />);

    const expectedLinks = [
      ["Active Alerts", "/alerts"],
      ["Critical Events", "/events"],
      ["Total Events", "/events"],
      ["Resolved Alerts", "/alerts"],
      ["Failed Logins (24h)", "/events"],
      ["Successful Logins (24h)", "/events"],
    ];

    for (const [title, href] of expectedLinks) {
      const label = screen.getByText(title);
      const link = label.closest("a");

      expect(link).not.toBeNull();
      expect(link).toHaveAttribute("href", href);
    }
  });
});