"use client";

import {
    BarChart,
    Bar,
    CartesianGrid,
    LineChart,
    Line,
    PieChart,
    Pie,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import {
    Activity,
    AlertTriangle,
    CheckCircle,
    Lock,
    RefreshCw,
    Shield,
    UserCheck,
} from "lucide-react";

import { useSecurityReport } from "@/hooks/use-reports";
import { useAnalytics } from "@/hooks/use-analytics";

import StatCard from "@/components/dashboard/stat-card";

import { Button } from "@/components/ui/button";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";


function EmptyChart({
    message,
}: {
    message: string;
}) {
    return (
        <div className="flex h-80 items-center justify-center">
            <p className="text-sm text-muted-foreground">
                {message}
            </p>
        </div>
    );
}


function ErrorMessage({
    message,
    onRetry,
}: {
    message: string;
    onRetry: () => void;
}) {
    return (
        <div
            role="alert"
            className="space-y-3 rounded-md border border-red-200 bg-red-50 p-5"
        >
            <p className="font-medium text-red-700">
                {message}
            </p>

            <Button
                variant="outline"
                onClick={onRetry}
            >
                Try Again
            </Button>
        </div>
    );
}


export default function ReportsPage() {
    const {
        data: report,
        isLoading: isLoadingReport,
        isFetching: isFetchingReport,
        error: reportError,
        refetch: refetchReport,
    } = useSecurityReport();

    const {
        data: eventTrend = [],
        isLoading: isLoadingAnalytics,
        isFetching: isFetchingAnalytics,
        error: analyticsError,
        refetch: refetchAnalytics,
    } = useAnalytics();

    const isRefreshing =
        isFetchingReport || isFetchingAnalytics;


    async function refreshAll() {
        await Promise.all([
            refetchReport(),
            refetchAnalytics(),
        ]);
    }


    return (
        <div className="space-y-8">
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold">
                        Security Reports
                    </h1>

                    <p className="mt-1 text-muted-foreground">
                        Review security metrics, event activity,
                        alert distributions, and authentication trends.
                    </p>
                </div>

                <Button
                    variant="outline"
                    disabled={isRefreshing}
                    onClick={() => void refreshAll()}
                >
                    <RefreshCw
                        className={`mr-2 h-4 w-4 ${
                            isRefreshing ? "animate-spin" : ""
                        }`}
                    />

                    {isRefreshing ? "Refreshing..." : "Refresh"}
                </Button>
            </div>


            {/* Security summary */}

            {isLoadingReport ? (
                <Card>
                    <CardContent className="py-10">
                        <p className="text-muted-foreground">
                            Loading security report...
                        </p>
                    </CardContent>
                </Card>
            ) : reportError || !report ? (
                <ErrorMessage
                    message="Failed to load security report."
                    onRetry={() => void refetchReport()}
                />
            ) : (
                <>
                    <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
                        <StatCard
                            title="Total Events"
                            value={report.total_events}
                            icon={<Activity className="h-8 w-8" />}
                        />

                        <StatCard
                            title="Critical Events"
                            value={report.critical_events}
                            icon={<AlertTriangle className="h-8 w-8" />}
                        />

                        <StatCard
                            title="Active Alerts"
                            value={report.active_alerts}
                            icon={<Shield className="h-8 w-8" />}
                        />

                        <StatCard
                            title="Resolved Alerts"
                            value={report.resolved_alerts}
                            icon={<CheckCircle className="h-8 w-8" />}
                        />

                        <StatCard
                            title="Failed Logins (24h)"
                            value={report.failed_logins_24h}
                            icon={<Lock className="h-8 w-8" />}
                        />

                        <StatCard
                            title="Successful Logins (24h)"
                            value={report.successful_logins_24h}
                            icon={<UserCheck className="h-8 w-8" />}
                        />
                    </div>


                    <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
                        {/* Event severity */}

                        <Card>
                            <CardHeader>
                                <CardTitle>
                                    Event Severity Distribution
                                </CardTitle>
                            </CardHeader>

                            <CardContent>
                                {report.severity_distribution.length === 0 ? (
                                    <EmptyChart message="No event severity data available." />
                                ) : (
                                    <div className="h-80 w-full">
                                        <ResponsiveContainer
                                            width="100%"
                                            height="100%"
                                        >
                                            <BarChart
                                                data={report.severity_distribution}
                                            >
                                                <CartesianGrid strokeDasharray="3 3" />

                                                <XAxis dataKey="name" />

                                                <YAxis allowDecimals={false} />

                                                <Tooltip />

                                                <Bar
                                                    dataKey="count"
                                                    fill="#2563eb"
                                                />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
                            </CardContent>
                        </Card>


                        {/* Alert severity */}

                        <Card>
                            <CardHeader>
                                <CardTitle>
                                    Alert Severity Distribution
                                </CardTitle>
                            </CardHeader>

                            <CardContent>
                                {report.alert_severity_distribution.length === 0 ? (
                                    <EmptyChart message="No alert severity data available." />
                                ) : (
                                    <div className="h-80 w-full">
                                        <ResponsiveContainer
                                            width="100%"
                                            height="100%"
                                        >
                                            <PieChart>
                                                <Pie
                                                    data={report.alert_severity_distribution}
                                                    dataKey="count"
                                                    nameKey="name"
                                                    outerRadius={110}
                                                    fill="#2563eb"
                                                    label
                                                />

                                                <Tooltip />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </div>
                                )}
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
                            {report.event_type_distribution.length === 0 ? (
                                <p className="py-6 text-sm text-muted-foreground">
                                    No event type data available.
                                </p>
                            ) : (
                                <div className="space-y-3">
                                    {report.event_type_distribution.map(
                                        (item) => (
                                            <div
                                                key={item.name}
                                                className="flex items-center justify-between border-b pb-3"
                                            >
                                                <span className="font-medium">
                                                    {item.name}
                                                </span>

                                                <span className="text-sm font-semibold">
                                                    {item.count}
                                                </span>
                                            </div>
                                        )
                                    )}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </>
            )}


            {/* Event trend analytics */}

            <Card>
                <CardHeader>
                    <CardTitle>
                        Event Activity Over Time
                    </CardTitle>
                </CardHeader>

                <CardContent>
                    {isLoadingAnalytics ? (
                        <EmptyChart message="Loading event analytics..." />
                    ) : analyticsError ? (
                        <ErrorMessage
                            message="Failed to load event analytics."
                            onRetry={() => void refetchAnalytics()}
                        />
                    ) : eventTrend.length === 0 ? (
                        <EmptyChart message="No event activity data available." />
                    ) : (
                        <div className="h-80 w-full">
                            <ResponsiveContainer
                                width="100%"
                                height="100%"
                            >
                                <LineChart data={eventTrend}>
                                    <CartesianGrid strokeDasharray="3 3" />

                                    <XAxis dataKey="date" />

                                    <YAxis allowDecimals={false} />

                                    <Tooltip />

                                    <Line
                                        type="monotone"
                                        dataKey="count"
                                        stroke="#2563eb"
                                        strokeWidth={2}
                                        dot={false}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}