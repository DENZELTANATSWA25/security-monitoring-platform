"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    CartesianGrid,
} from "recharts";

import { useAnalytics } from "@/hooks/use-analytics";

export default function EventChart() {

    const {

        data,

        isLoading,

    } = useAnalytics();

    if (isLoading)
        return <p>Loading chart...</p>;

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

                        <YAxis />

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