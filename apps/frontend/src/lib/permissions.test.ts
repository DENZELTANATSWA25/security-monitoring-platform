import { describe, expect, it } from "vitest";

import type { UserRole } from "@/types/user";

import {
  canViewUsers,
  canManageIncidents,
  canResolveAlerts,
  canManageRules,
  canViewTelemetryHealth,
  canManageTelemetrySources,
  canViewAuditLogs,
} from "./permissions";

type PermissionFunction = (role: UserRole | undefined) => boolean;

const permissions: {
  name: string;
  check: PermissionFunction;
  admin: boolean;
  analyst: boolean;
}[] = [
  {
    name: "view users",
    check: canViewUsers,
    admin: true,
    analyst: false,
  },
  {
    name: "manage incidents",
    check: canManageIncidents,
    admin: true,
    analyst: true,
  },
  {
    name: "resolve alerts",
    check: canResolveAlerts,
    admin: true,
    analyst: true,
  },
  {
    name: "manage detection rules",
    check: canManageRules,
    admin: true,
    analyst: false,
  },
  {
    name: "view telemetry health",
    check: canViewTelemetryHealth,
    admin: true,
    analyst: true,
  },
  {
    name: "manage telemetry sources",
    check: canManageTelemetrySources,
    admin: true,
    analyst: false,
  },
  {
    name: "view audit logs",
    check: canViewAuditLogs,
    admin: true,
    analyst: false,
  },
];

describe("Role-based access control", () => {
  for (const permission of permissions) {
    describe(permission.name, () => {
      it("applies administrator permissions correctly", () => {
        expect(permission.check("admin")).toBe(permission.admin);
      });

      it("applies analyst permissions correctly", () => {
        expect(permission.check("analyst")).toBe(permission.analyst);
      });

      it("denies unauthenticated users", () => {
        expect(permission.check(undefined)).toBe(false);
      });
    });
  }
});