"use client";

import {
    BarChart,
    Bar,
    CartesianGrid,
    PieChart,
    Pie,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import { useSecurityReport } from "@/hooks/use-reports";

import StatCard from "@/components/dashboard/stat-card";

import {
    Activity,
    AlertTriangle,
    CheckCircle,
    Lock,
    Shield,
    UserCheck,
} from "lucide-react";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";


export default function ReportsPage() {

    const {
        data,
        isLoading,
        error,
    } = useSecurityReport();


    if (isLoading) {
        return (
            <div className="p-6">
                Loading security report...
            </div>
        );
    }


    if (error || !data) {
        return (
            <div className="p-6">

                <p className="font-semibold text-red-600">
                    Failed to load security report.
                </p>

                <p className="text-sm text-muted-foreground mt-1">
                    Verify that the backend reports API is running.
                </p>

            </div>
        );
    }


    return (

        <div className="space-y-8">

            <div>

                <h1 className="text-3xl font-bold">
                    Security Reports
                </h1>

                <p className="text-muted-foreground mt-1">
                    Review security activity, alerts, authentication activity,
                    and event distributions.
                </p>

            </div>


            {/* Summary statistics */}

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">

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


            {/* Charts */}

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">

                <Card>

                    <CardHeader>

                        <CardTitle>
                            Event Severity Distribution
                        </CardTitle>

                    </CardHeader>

                    <CardContent>

                        <ResponsiveContainer
                            width="100%"
                            height={320}
                        >

                            <BarChart
                                data={data.severity_distribution}
                            >

                                <CartesianGrid
                                    strokeDasharray="3 3"
                                />

                                <XAxis
                                    dataKey="name"
                                />

                                <YAxis
                                    allowDecimals={false}
                                />

                                <Tooltip />

                                <Bar
                                    dataKey="count"
                                />

                            </BarChart>

                        </ResponsiveContainer>

                    </CardContent>

                </Card>


                <Card>

                    <CardHeader>

                        <CardTitle>
                            Alert Severity Distribution
                        </CardTitle>

                    </CardHeader>

                    <CardContent>

                        <ResponsiveContainer
                            width="100%"
                            height={320}
                        >

                            <PieChart>

                                <Pie
                                    data={data.alert_severity_distribution}
                                    dataKey="count"
                                    nameKey="name"
                                    outerRadius={110}
                                    label
                                />

                                <Tooltip />

                            </PieChart>

                        </ResponsiveContainer>

                    </CardContent>

                </Card>

            </div>


            {/* Event types */}

            <Card>

                <CardHeader>

                    <CardTitle>
                        Events by Type
                    </CardTitle>

                </CardHeader>

                <CardContent>

                    {data.event_type_distribution.length === 0 ? (

                        <p className="text-muted-foreground">
                            No event data available.
                        </p>

                    ) : (

                        <div className="space-y-3">

                            {data.event_type_distribution.map(
                                (item) => (

                                    <div
                                        key={item.name}
                                        className="
                                            flex
                                            items-center
                                            justify-between
                                            border-b
                                            pb-3
                                        "
                                    >

                                        <span className="font-medium">
                                            {item.name}
                                        </span>

                                        <span className="
                                            text-sm
                                            font-semibold
                                        ">
                                            {item.count}
                                        </span>

                                    </div>

                                )
                            )}

                        </div>

                    )}

                </CardContent>

            </Card>

        </div>
    );
}