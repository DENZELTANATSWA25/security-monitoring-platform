"use client";


import StatCard from "./stat-card";
import {DashboardSummary} from "@/types/dashboard";
import {
    Shield,
    AlertTriangle,
    Activity,
    CheckCircle,
    Lock,
    UserCheck
} from "lucide-react";


interface Props {
data:DashboardSummary
}



export default function DashboardGrid({
data
}:Props){


return (

<div className="grid grid-cols-1 md:grid-cols-3 gap-6">


<StatCard
title="Total Events"
value={data.total_events}
icon={<Activity className="h-8 w-8" />}
/>


<StatCard
title="Critical Events"
value={data.critical_events}
icon={<AlertTriangle className="h-8 w-8" />}
/>


<StatCard
title="Active Alerts"
value={data.active_alerts}
icon={<Shield className="h-8 w-8" />}
/>


<StatCard
title="Resolved Alerts"
value={data.resolved_alerts}
icon={<CheckCircle className="h-8 w-8" />}
/>


<StatCard
title="Failed Logins (24h)"
value={data.failed_logins_24h}
icon={<Lock className="h-8 w-8" />}
/>


<StatCard
title="Successful Logins (24h)"
value={data.successful_logins_24h}
icon={<UserCheck className="h-8 w-8" />}
/>


</div>


)

}