"use client";

import { usePathname } from "next/navigation";

import Link from "next/link";

export default function Sidebar() {
    const pathname = usePathname();
    return (
        <aside className="w-64 min-h-screen border-r bg-slate-950 text-white">

            <div className="p-6 text-xl font-bold">
                Security SOC
            </div>

            <nav className="space-y-2 p-4">

                <Link
                href="/"
                className={`block rounded p-3 hover:bg-slate-800 ${
                pathname === "/"
                ? "bg-slate-800"
                : ""
                }`}
                 >
                    Dashboard
                </Link>

                <Link
                    href="/alerts"
                    className={`block rounded p-3 hover:bg-slate-800 ${
                    pathname === "/alerts"
                    ? "bg-slate-800"
                    : ""
                    }`}
                >
                    Alerts
                </Link>

                <Link
                    href="/incidents"
                    className="block rounded p-3 hover:bg-slate-800"
                >                
                    Incidents
                </Link>

                <Link
                    href="/events"
                    className={'block rounded p-3 hover:bg-slate-800 ${pathname === "/events" ? "bg-slate-800" : ""}'}
                >
                    Events
                </Link>

                <Link
                    href="/incidents"
                    className="block rounded p-3 hover:bg-slate-800"
                >
                    Incidents
                </Link>

                <Link
                    href="/users"
                    className={'block rounded p-3 hover:bg-slate-800 ${pathname === "/users" ? "bg-slate-800" : ""}'}
                >
                    Users
                </Link>

                <Link
                    href="/reports"
                    className={'block rounded p-3 hover:bg-slate-800 ${pathname === "/reports" ? "bg-slate-800" : ""}'}
                >
                    Reports
                </Link>

            </nav>

        </aside>
    );
}