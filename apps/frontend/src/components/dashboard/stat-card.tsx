import { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";

interface StatCardProps {
    title: string;
    value: number | string;
    icon: ReactNode;
    description?: string;
}

export default function StatCard({
    title,
    value,
    icon,
    description,
}: StatCardProps) {
    return (
        <Card className="shadow-sm hover:shadow-md transition">
            <CardContent className="p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-muted-foreground">
                            {title}
                        </p>

                        <h2 className="text-3xl font-bold mt-2">
                            {value}
                        </h2>

                        {description && (
                            <p className="text-xs text-muted-foreground mt-3">
                                {description}
                            </p>
                        )}
                    </div>

                    <div className="text-muted-foreground">
                        {icon}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}