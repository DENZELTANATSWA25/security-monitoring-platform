import type { ReactNode } from "react";

import Link from "next/link";

import {
  Card,
  CardContent,
} from "@/components/ui/card";

type StatCardProps = {
  title: string;
  value: number | string;
  subtitle?: string;
  icon?: ReactNode;
  description?: string;
  href?: string;
  priority?: "default" | "critical" | "warning" | "success";
};

export default function StatCard({
  title,
  value,
  subtitle,
  icon,
  description,
  href,
  priority = "default",
}: StatCardProps) {
  const priorityStyles = {
    default: {
      icon: "text-primary bg-primary/10",
      accent: "bg-primary",
    },
    critical: {
      icon: "text-destructive bg-destructive/10",
      accent: "bg-destructive",
    },
    warning: {
      icon: "text-status-warning bg-status-warning/10",
      accent: "bg-status-warning",
    },
    success: {
      icon: "text-status-success bg-status-success/10",
      accent: "bg-status-success",
    },
  };

  const styles = priorityStyles[priority];

  const content = (
    <Card
      className={`
        group relative h-full overflow-hidden
        border-border bg-card
        transition-all duration-200
        ${href ? "hover:border-primary/40 hover:shadow-md" : ""}
      `}
    >
      <span
        aria-hidden="true"
        className={`
          absolute inset-x-0 top-0 h-[2px]
          ${styles.accent}
        `}
      />

      <CardContent className="p-5 sm:p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-sm font-medium text-muted-foreground">
              {title}
            </p>

            <p className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              {typeof value === "number"
                ? value.toLocaleString()
                : value}
            </p>

            {(subtitle || description) && (
              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                {subtitle || description}
              </p>
            )}
          </div>

          {icon && (
            <div
              aria-hidden="true"
              className={`
                flex size-11 shrink-0 items-center justify-center
                rounded-xl
                ${styles.icon}
              `}
            >
              {icon}
            </div>
          )}
        </div>

        {href && (
          <p className="mt-5 text-xs font-medium text-primary">
            View details →
          </p>
        )}
      </CardContent>
    </Card>
  );

  if (!href) {
    return content;
  }

  return (
    <Link
      href={href}
      className="
        block h-full rounded-xl
        focus-visible:outline-2
        focus-visible:outline-offset-2
        focus-visible:outline-ring
      "
    >
      {content}
    </Link>
  );
}