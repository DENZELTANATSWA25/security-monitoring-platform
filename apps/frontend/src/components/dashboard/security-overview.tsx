"use client";

import {
    Activity,
    AlertTriangle,
    ShieldCheck,
    LogIn,
    XCircle
} from "lucide-react";

import StatCard  from "./stat-card";
import { useDashboard } from "@/hooks/use-dashboard";

export default function SecurityOverview() {

    const {
        data,
        isLoading
    } = useDashboard();

    if(isLoading){
        return (

            <div>
                Loading metrics...
            </div>
        )   
    }

    return (

        <div className="
        grid
        grid-cols-1
        md:grid-cols-2
        lg:grid-cols-5
        gap-5
        "
        >

            <StatCard
            title="Total Events"
            value={data?.total_events ?? 0}
            icon={<Activity/>}
            description="Security events records"
            />

            <StatCard
            title="Critical Events"
            value={data?.critical_events ?? 0}
            icon={<AlertTriangle/>}
            description="High priority threats"
            />

            <StatCard
            title="Active Alerts"
            value={data?.active_alerts ?? 0}
            icon={<ShieldCheck/>}
            description="Unresolved alerts"
            />

            <StatCard
            title="Failed Logins"
            value={data?.failed_logins_24h ?? 0}
            icon={<XCircle/>}
            description="Last 24 hours"
            />

            <StatCard
            title="Successful Logins"
            value={data?.successful_logins_24h ?? 0}
            icon={<LogIn/>}
            description="Last 24 hours"
            />

        </div>
    )
}
