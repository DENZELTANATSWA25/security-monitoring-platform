"use client";

import { useId } from "react";

import {
    Activity,
    AlertCircle,
    BarChart3,
    RefreshCw,
} from "lucide-react";

import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

import { Button } from "@/components/ui/button";
import { useAnalytics } from "@/hooks/use-analytics";

function formatDate(value: string): string {
    const parts = value.split("-");

    if (parts.length === 3) {
        const month = Number(parts[1]);
        const day = Number(parts[2]);

        if (
            Number.isInteger(month) &&
            Number.isInteger(day) &&
            month >= 1 &&
            month <= 12 &&
            day >= 1 &&
            day <= 31
        ) {
            return new Intl.DateTimeFormat("en-GB", {
                month: "short",
                day: "numeric",
            }).format(
                new Date(
                    Date.UTC(
                        Number(parts[0]),
                        month - 1,
                        day
                    )
                )
            );
        }
    }

    return value;
}

export default function EventChart() {
    const chartId = useId();

    const {
        data,
        isLoading,
        isError,
        isFetching,
        refetch,
    } = useAnalytics();

    const totalEvents =
        data?.reduce(
            (total, point) => total + point.count,
            0
        ) ?? 0;

    const peakEvents =
        data?.reduce(
            (highest, point) =>
                Math.max(highest, point.count),
            0
        ) ?? 0;

    const hasData = Boolean(data?.length);

    return (
        <Card className="overflow-hidden border-border/70 bg-card shadow-sm">
            <CardHeader className="gap-4 border-b border-border/60 pb-5 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-2">
                    <div className="flex items-center gap-2">
                        <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                            <Activity
                                className="size-4"
                                aria-hidden="true"
                            />
                        </div>

                        <div>
                            <CardTitle className="text-base font-semibold tracking-tight">
                                Security Event Trend
                            </CardTitle>

                            <p className="mt-1 text-xs text-muted-foreground">
                                Recorded security events over time
                            </p>
                        </div>
                    </div>
                </div>

                <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => void refetch()}
                    disabled={isFetching}
                    className="w-fit gap-2"
                    aria-label="Refresh security event trend"
                >
                    <RefreshCw
                        className={`size-3.5 ${
                            isFetching ? "animate-spin" : ""
                        }`}
                        aria-hidden="true"
                    />

                    Refresh
                </Button>
            </CardHeader>

            <CardContent className="space-y-6 pt-6">
                {isLoading ? (
                    <div
                        className="space-y-4"
                        role="status"
                        aria-live="polite"
                    >
                        <div className="flex gap-3">
                            <div className="h-14 w-32 animate-pulse rounded-lg bg-muted" />
                            <div className="h-14 w-32 animate-pulse rounded-lg bg-muted" />
                        </div>

                        <div className="h-[300px] animate-pulse rounded-xl bg-muted/50" />

                        <span className="sr-only">
                            Loading security event trend
                        </span>
                    </div>
                ) : isError ? (
                    <div
                        role="alert"
                        className="flex min-h-[280px] flex-col items-center justify-center gap-3 rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-center"
                    >
                        <AlertCircle
                            className="size-7 text-destructive"
                            aria-hidden="true"
                        />

                        <h3 className="font-semibold">
                            Unable to load event trend
                        </h3>

                        <p className="max-w-sm text-sm text-muted-foreground">
                            Security event analytics could not be retrieved.
                            Try refreshing the chart.
                        </p>

                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => void refetch()}
                        >
                            Try again
                        </Button>
                    </div>
                ) : !hasData ? (
                    <div className="flex min-h-[280px] flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border p-6 text-center">
                        <BarChart3
                            className="size-8 text-muted-foreground"
                            aria-hidden="true"
                        />

                        <h3 className="font-semibold">
                            No event activity available
                        </h3>

                        <p className="max-w-sm text-sm text-muted-foreground">
                            Event trends will appear when security telemetry
                            has been recorded.
                        </p>
                    </div>
                ) : (
                    <>
                        <div className="flex flex-wrap gap-3">
                            <div className="min-w-36 rounded-lg border border-border/70 bg-muted/30 px-4 py-3">
                                <p className="text-xs text-muted-foreground">
                                    Events in displayed period
                                </p>

                                <p className="mt-1 text-2xl font-semibold tracking-tight tabular-nums">
                                    {totalEvents.toLocaleString()}
                                </p>
                            </div>

                            <div className="min-w-36 rounded-lg border border-border/70 bg-muted/30 px-4 py-3">
                                <p className="text-xs text-muted-foreground">
                                    Peak daily events
                                </p>

                                <p className="mt-1 text-2xl font-semibold tracking-tight tabular-nums">
                                    {peakEvents.toLocaleString()}
                                </p>
                            </div>
                        </div>

                        <div
                            role="img"
                            aria-label={`Security event trend with ${totalEvents} events across ${data?.length ?? 0} recorded dates. Highest daily count: ${peakEvents}.`}
                            className="h-[260px] w-full sm:h-[320px]"
                        >
                            <ResponsiveContainer
                                width="100%"
                                height="100%"
                            >
                                <LineChart
                                    data={data}
                                    margin={{
                                        top: 12,
                                        right: 16,
                                        left: -12,
                                        bottom: 8,
                                    }}
                                >
                                    <defs>
                                        <linearGradient
                                            id={`${chartId}-line`}
                                            x1="0"
                                            y1="0"
                                            x2="1"
                                            y2="0"
                                        >
                                            <stop
                                                offset="0%"
                                                stopColor="var(--chart-2)"
                                            />

                                            <stop
                                                offset="100%"
                                                stopColor="var(--chart-1)"
                                            />
                                        </linearGradient>
                                    </defs>

                                    <CartesianGrid
                                        vertical={false}
                                        stroke="var(--border)"
                                        strokeOpacity={0.65}
                                        strokeDasharray="3 5"
                                    />

                                    <XAxis
                                        dataKey="date"
                                        tickFormatter={formatDate}
                                        tick={{
                                            fill: "var(--muted-foreground)",
                                            fontSize: 11,
                                        }}
                                        tickLine={false}
                                        axisLine={false}
                                        minTickGap={24}
                                        dy={12}
                                    />

                                    <YAxis
                                        allowDecimals={false}
                                        tick={{
                                            fill: "var(--muted-foreground)",
                                            fontSize: 11,
                                        }}
                                        tickLine={false}
                                        axisLine={false}
                                        width={36}
                                    />

                                    <Tooltip
                                        cursor={{
                                            stroke: "var(--muted-foreground)",
                                            strokeOpacity: 0.35,
                                            strokeDasharray: "4 4",
                                        }}
                                        contentStyle={{
                                            backgroundColor: "var(--popover)",
                                            color: "var(--popover-foreground)",
                                            border: "1px solid var(--border)",
                                            borderRadius: "10px",
                                            boxShadow:
                                                "0 12px 30px rgba(0,0,0,0.12)",
                                            fontSize: "12px",
                                        }}
                                        labelStyle={{
                                            color: "var(--popover-foreground)",
                                            fontWeight: 600,
                                            marginBottom: "6px",
                                        }}
                                        itemStyle={{
                                            color: "var(--popover-foreground)",
                                        }}
                                        labelFormatter={(label) =>
                                            formatDate(String(label))
                                        }
                                        formatter={(value) => [
                                            Number(value).toLocaleString(),
                                            "Security events",
                                        ]}
                                    />

                                    <Line
                                        type="monotone"
                                        dataKey="count"
                                        name="Security events"
                                        stroke={`url(#${chartId}-line)`}
                                        strokeWidth={2.5}
                                        dot={{
                                            r: 3,
                                            fill: "var(--background)",
                                            stroke: "var(--chart-1)",
                                            strokeWidth: 2,
                                        }}
                                        activeDot={{
                                            r: 6,
                                            fill: "var(--chart-1)",
                                            stroke: "var(--background)",
                                            strokeWidth: 2,
                                        }}
                                        isAnimationActive={false}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>

                        <p className="text-xs text-muted-foreground">
                            Showing {data?.length ?? 0} recorded dates.
                            Analytics refresh automatically every 30 seconds.
                        </p>
                    </>
                )}
            </CardContent>
        </Card>
    );
}