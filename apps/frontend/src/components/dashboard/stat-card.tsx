import { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon?: ReactNode;
  description?: string;
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon,
  description,
}: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-gray-500">{title}</p>

            <h2 className="mt-2 text-4xl font-bold">{value}</h2>

            {subtitle && (
              <p className="mt-2 text-sm text-gray-400">{subtitle}</p>
            )}

            {description && (
              <p className="mt-2 text-sm text-muted-foreground">
                {description}
              </p>
            )}
          </div>

          {icon && <div className="text-blue-600">{icon}</div>}
        </div>
      </CardContent>
    </Card>
  );
}
