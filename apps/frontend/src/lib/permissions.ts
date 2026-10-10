import type { UserRole } from "@/types/user";

export function canViewUsers(
    role: UserRole | undefined
) {
    return role === "admin";
}

export function canManageIncidents(
    role: UserRole | undefined
) {
    return role === "admin" || role === "analyst";
}

export function canResolveAlerts(
    role: UserRole | undefined
) {
    return role === "admin" || role === "analyst";
}

export function canManageRules(
    role: UserRole | undefined
) {
    return role === "admin";
}

export function canViewTelemetryHealth(
    role: UserRole | undefined
) {
    return role === "admin" || role === "analyst";
}

export function canManageTelemetrySources(
    role: UserRole | undefined
) {
    return role === "admin";
}

export function canViewAuditLogs(
    role: UserRole | undefined
) {
    return role === "admin";
}