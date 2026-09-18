"use client";

import {
    Activity,
    BellRing,
    CirclePlus,
    FileText,
    Link2,
    RefreshCcw,
    UserRoundCheck,
} from "lucide-react";

import {
    useIncidentActivities,
} from "@/hooks/use-incident-activities";

import type {
    IncidentActivity,
    IncidentActivityType,
} from "@/types/incident-activity";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";


interface IncidentActivityTimelineProps {
    incidentId: number;
}


function getActivityIcon(
    activityType: IncidentActivityType
) {
    switch (activityType) {
        case "INCIDENT_CREATED":
            return CirclePlus;

        case "ASSIGNED":
            return UserRoundCheck;

        case "STATUS_CHANGED":
            return RefreshCcw;

        case "NOTE_ADDED":
            return FileText;
        
        case "EVENT_LINKED":
            return Link2;
        
        case "ALERT_LINKED":
            return BellRing;

        default:
            return Activity;
    }
}


function getActivityTitle(
    activity: IncidentActivity
) {
    switch (activity.activity_type) {
        case "INCIDENT_CREATED":
            return "Incident created";

        case "ASSIGNED":
            return "Assignment changed";

        case "STATUS_CHANGED":
            return "Status changed";

        case "NOTE_ADDED":
            return "Investigation note added";
        
        case "EVENT_LINKED":
            return "Event linked";
        
        case "ALERT_LINKED":
            return "Alert linked";

        default:
            return "Incident activity";
    }
}


function formatActivityValue(
    activity: IncidentActivity
) {
    if (
        !activity.old_value
        && !activity.new_value
    ) {
        return null;
    }

    if (
        activity.old_value
        && activity.new_value
    ) {
        return `${activity.old_value} → ${activity.new_value}`;
    }

    return activity.new_value
        ?? activity.old_value;
}


export default function IncidentActivityTimeline({
    incidentId,
}: IncidentActivityTimelineProps) {
    const {
        data: activities = [],
        isLoading,
        error,
    } = useIncidentActivities(incidentId);


    return (
        <Card>
            <CardHeader>
                <CardTitle>
                    Incident Timeline
                </CardTitle>
            </CardHeader>

            <CardContent>
                {isLoading && (
                    <p className="text-sm text-muted-foreground">
                        Loading incident activity...
                    </p>
                )}


                {error && (
                    <p className="text-sm text-red-600">
                        Unable to load incident activity.
                    </p>
                )}


                {!isLoading
                    && !error
                    && activities.length === 0 && (
                        <p className="text-sm text-muted-foreground">
                            No recorded activity for this incident.
                        </p>
                    )}


                {!isLoading
                    && !error
                    && activities.length > 0 && (
                        <div>
                            {activities.map(
                                (
                                    activity,
                                    index
                                ) => {
                                    const Icon =
                                        getActivityIcon(
                                            activity.activity_type
                                        );

                                    const value =
                                        formatActivityValue(
                                            activity
                                        );

                                    const isLast =
                                        index
                                        === activities.length - 1;

                                    return (
                                        <div
                                            key={activity.id}
                                            className="relative flex gap-4"
                                        >
                                            {!isLast && (
                                                <div
                                                    className="
                                                        absolute
                                                        left-4
                                                        top-8
                                                        bottom-0
                                                        w-px
                                                        bg-border
                                                    "
                                                />
                                            )}

                                            <div
                                                className="
                                                    relative
                                                    z-10
                                                    flex
                                                    h-8
                                                    w-8
                                                    shrink-0
                                                    items-center
                                                    justify-center
                                                    rounded-full
                                                    border
                                                    bg-background
                                                "
                                            >
                                                <Icon className="h-4 w-4" />
                                            </div>


                                            <div
                                                className={
                                                    isLast
                                                        ? "pb-0"
                                                        : "pb-6"
                                                }
                                            >
                                                <p className="font-semibold">
                                                    {getActivityTitle(
                                                        activity
                                                    )}
                                                </p>


                                                <p className="mt-1 text-sm text-muted-foreground">
                                                    {
                                                        activity.description
                                                    }
                                                </p>


                                                {value && (
                                                    <p className="mt-1 text-sm font-medium">
                                                        {value}
                                                    </p>
                                                )}


                                                <div
                                                    className="
                                                        mt-2
                                                        flex
                                                        flex-wrap
                                                        gap-x-2
                                                        gap-y-1
                                                        text-xs
                                                        text-muted-foreground
                                                    "
                                                >
                                                    <span>
                                                        {new Date(
                                                            activity.created_at
                                                        ).toLocaleString()}
                                                    </span>

                                                    <span>
                                                        •
                                                    </span>

                                                    <span>
                                                        {activity.actor
                                                            ? (
                                                                `${activity.actor.full_name} (${activity.actor.role})`
                                                            )
                                                            : "System"}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                }
                            )}
                        </div>
                    )}
            </CardContent>
        </Card>
    );
}