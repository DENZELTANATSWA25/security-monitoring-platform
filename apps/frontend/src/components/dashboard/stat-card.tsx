import { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";

interface StatCardProps {
    title: string;
    value: number | string;
    subtitle?: string;
    icon?: ReactNode;
}

export default function StatCard({
    title,
    value,
    subtitle,
    icon,
}: StatCardProps) {
    return (
        <Card>
            <CardContent className="p-6">

                <div className="flex justify-between items-start">

                    <div>

                        <p className="text-sm text-gray-500">
                            {title}
                        </p>

                        <h2 className="mt-2 text-4xl font-bold">
                            {value}
                        </h2>

                        {subtitle && (
                            <p className="mt-2 text-sm text-gray-400">
                                {subtitle}
                            </p>
                        )}

                    </div>

                    {icon && (
                        <div className="text-blue-600">
                            {icon}
                        </div>
                    )}

                </div>

            </CardContent>
        </Card>
    );
}