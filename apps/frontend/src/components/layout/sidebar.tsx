"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useCurrentUser } from "@/hooks/use-users";
import {
    canViewUsers,
    canManageRules,
} from "@/lib/permissions";


export default function Sidebar() {
    const pathname = usePathname();

    const {
        data: currentUser,
    } = useCurrentUser();


    /**
     * Determines whether a navigation item represents the current route.
     *
     * Dashboard must match "/" exactly, while application sections should
     * remain active on nested routes such as /incidents/2.
     */
    function isActiveRoute(href: string) {
        if (href === "/") {
            return pathname === "/";
        }

        return (
            pathname === href
            || pathname.startsWith(`${href}/`)
        );
    }


    function navigationClassName(href: string) {
        return [
            "block rounded p-3 transition-colors",
            "hover:bg-slate-800",
            isActiveRoute(href)
                ? "bg-slate-800"
                : "",
        ]
            .filter(Boolean)
            .join(" ");
    }


    return (
        <aside className="min-h-screen w-64 border-r bg-slate-950 text-white">
            <div className="p-6 text-xl font-bold">
                Security SOC
            </div>

            <nav className="space-y-2 p-4">
                <Link
                    href="/"
                    className={navigationClassName("/")}
                >
                    Dashboard
                </Link>

                <Link
                    href="/alerts"
                    className={navigationClassName("/alerts")}
                >
                    Alerts
                </Link>

                <Link
                    href="/incidents"
                    className={navigationClassName("/incidents")}
                >
                    Incidents
                </Link>

                <Link
                    href="/events"
                    className={navigationClassName("/events")}
                >
                    Events
                </Link>

                {canManageRules(currentUser?.role) && (
                    <Link
                        href="/detection-rules"
                        className={navigationClassName("/detection-rules")}
                    >
                        Detection Rules
                    </Link>
                )}

                {canViewUsers(currentUser?.role) && (
                    <Link
                        href="/users"
                        className={navigationClassName("/users")}
                    >
                        Users
                    </Link>
                )}

                <Link
                    href="/reports"
                    className={navigationClassName("/reports")}
                >
                    Reports
                </Link>
            </nav>
        </aside>
    );
}