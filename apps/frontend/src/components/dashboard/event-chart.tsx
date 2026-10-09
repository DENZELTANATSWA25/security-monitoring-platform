"use client";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import { useAnalytics } from "@/hooks/use-analytics";

export default function EventChart() {
    const {
        data,
        isLoading,
        isError,
    } = useAnalytics();

    if (isLoading) {
        return (
            <Card>
                <CardContent className="p-6">
                    Loading event trend...
                </CardContent>
            </Card>
        );
    }

    if (isError) {
        return (
            <Card>
                <CardContent className="p-6 text-red-600">
                    Failed to load event trend.
                </CardContent>
            </Card>
        );
    }

    if (!data?.length) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Event Trend</CardTitle>
                </CardHeader>

                <CardContent className="p-6 text-muted-foreground">
                    No event trend data is available yet.
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>
                    Event Trend
                </CardTitle>
            </CardHeader>

            <CardContent>
                <ResponsiveContainer
                    width="100%"
                    height={300}
                >
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />

                        <XAxis dataKey="date" />

                        <YAxis allowDecimals={false} />

                        <Tooltip />

                        <Line
                            type="monotone"
                            dataKey="count"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
}