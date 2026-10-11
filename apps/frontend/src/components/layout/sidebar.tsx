"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BellRing,
  ChartNoAxesCombined,
  ChevronRight,
  DatabaseZap,
  LayoutDashboard,
  LockKeyhole,
  Radar,
  ScrollText,
  ShieldCheck,
  UsersRound,
  type LucideIcon,
} from "lucide-react";

import { useCurrentUser } from "@/hooks/use-users";
import {
  canViewUsers,
  canManageRules,
  canViewTelemetryHealth,
  canViewAuditLogs,
} from "@/lib/permissions";

type NavigationItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  visible?: boolean;
};

type NavigationGroup = {
  label: string;
  items: NavigationItem[];
};

type SidebarProps = {
  collapsed?: boolean;
  onNavigate?: () => void;
};

export default function Sidebar({
  collapsed = false,
  onNavigate,
}: SidebarProps) {
  const pathname = usePathname();
  const { data: currentUser } = useCurrentUser();

  const navigationGroups: NavigationGroup[] = [
    {
      label: "OVERVIEW",
      items: [
        {
          label: "Dashboard",
          href: "/",
          icon: LayoutDashboard,
        },
        {
          label: "Reports",
          href: "/reports",
          icon: ChartNoAxesCombined,
        },
      ],
    },
    {
      label: "SECURITY OPERATIONS",
      items: [
        {
          label: "Alerts",
          href: "/alerts",
          icon: BellRing,
        },
        {
          label: "Incidents",
          href: "/incidents",
          icon: ShieldCheck,
        },
        {
          label: "Security Events",
          href: "/events",
          icon: Activity,
        },
      ],
    },
    {
      label: "DETECTION & SOURCES",
      items: [
        {
          label: "Detection Rules",
          href: "/detection-rules",
          icon: Radar,
          visible: canManageRules(currentUser?.role),
        },
        {
          label: "Telemetry Sources",
          href: "/telemetry-sources",
          icon: DatabaseZap,
          visible: canViewTelemetryHealth(currentUser?.role),
        },
      ],
    },
    {
      label: "ADMINISTRATION",
      items: [
        {
          label: "Users",
          href: "/users",
          icon: UsersRound,
          visible: canViewUsers(currentUser?.role),
        },
        {
          label: "Audit Logs",
          href: "/audit-logs",
          icon: ScrollText,
          visible: canViewAuditLogs(currentUser?.role),
        },
      ],
    },
  ];

  function isActiveRoute(href: string) {
    if (href === "/") {
      return pathname === "/";
    }

    return pathname === href || pathname.startsWith(`${href}/`);
  }

  return (
    <aside
      className={`
        flex h-full flex-col
        border-r border-sidebar-border
        bg-sidebar text-sidebar-foreground
        transition-[width] duration-200
        ${collapsed ? "w-[76px]" : "w-[260px]"}
      `}
    >
      {/* Brand */}
      <div
        className={`
          flex h-[72px] shrink-0 items-center
          border-b border-sidebar-border
          ${collapsed ? "justify-center px-3" : "gap-3 px-5"}
        `}
      >
        <div
          className="
            flex size-10 shrink-0 items-center justify-center
            rounded-xl border border-primary/25
            bg-primary/10 text-primary
          "
        >
          <ShieldCheck className="size-5" aria-hidden="true" />
        </div>

        {!collapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold tracking-tight">
              Security SOC
            </p>

            <p className="truncate text-[11px] text-muted-foreground">
              Threat Monitoring Platform
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav
        aria-label="Main navigation"
        className="flex-1 space-y-6 overflow-y-auto px-3 py-5"
      >
        {navigationGroups.map((group) => {
          const visibleItems = group.items.filter(
            (item) => item.visible !== false
          );

          if (visibleItems.length === 0) {
            return null;
          }

          return (
            <div key={group.label}>
              {!collapsed && (
                <p
                  className="
                    mb-2 px-3 text-[10px] font-semibold
                    tracking-[0.14em] text-muted-foreground
                  "
                >
                  {group.label}
                </p>
              )}

              <div className="space-y-1">
                {visibleItems.map((item) => {
                  const Icon = item.icon;
                  const active = isActiveRoute(item.href);

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onNavigate}
                      aria-current={active ? "page" : undefined}
                      title={collapsed ? item.label : undefined}
                      className={`
                        group relative flex min-h-10 items-center
                        rounded-lg px-3 text-sm
                        transition-colors duration-150
                        focus-visible:outline-2
                        focus-visible:outline-offset-[-2px]
                        focus-visible:outline-ring
                        ${
                          collapsed
                            ? "justify-center"
                            : "gap-3"
                        }
                        ${
                          active
                            ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                            : "text-sidebar-foreground/75 hover:bg-sidebar-accent/65 hover:text-sidebar-accent-foreground"
                        }
                      `}
                    >
                      {active && (
                        <span
                          aria-hidden="true"
                          className="
                            absolute inset-y-2 left-0 w-[3px]
                            rounded-r-full bg-sidebar-primary
                          "
                        />
                      )}

                      <Icon
                        aria-hidden="true"
                        className={`
                          size-[18px] shrink-0
                          ${active ? "text-sidebar-primary" : ""}
                        `}
                      />

                      {!collapsed && (
                        <>
                          <span className="min-w-0 flex-1 truncate">
                            {item.label}
                          </span>

                          {active && (
                            <ChevronRight
                              aria-hidden="true"
                              className="size-3.5 text-sidebar-primary"
                            />
                          )}
                        </>
                      )}

                      {collapsed && (
                        <span className="sr-only">{item.label}</span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })}
      </nav>

      {/* Sidebar footer */}
      <div className="shrink-0 border-t border-sidebar-border p-3">
        <div
          className={`
            flex items-center rounded-lg
            bg-sidebar-accent/50 p-3
            ${collapsed ? "justify-center" : "gap-3"}
          `}
        >
          <div className="relative shrink-0">
            <div
              className="
                flex size-8 items-center justify-center
                rounded-lg bg-primary/10 text-primary
              "
            >
              <LockKeyhole className="size-4" aria-hidden="true" />
            </div>
            <span
              aria-hidden="true"
              className="
                absolute -bottom-0.5 -right-0.5 size-2.5
                rounded-full border-2 border-sidebar
                bg-status-success
              "
            />
          </div>

          {!collapsed && (
            <div className="min-w-0">
              <p className="text-xs font-medium">
                Secure Workspace
              </p>
              <p className="text-[11px] text-muted-foreground">
                Role-based access enabled
              </p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}