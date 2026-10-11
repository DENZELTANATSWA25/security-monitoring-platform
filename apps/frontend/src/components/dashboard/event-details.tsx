"use client";

import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

import { ScrollArea } from "@/components/ui/scroll-area";

import { SecurityEvent } from "@/types/event";

import ThreatIntelligence from "./threat-intelligence";

interface Props {

    event: SecurityEvent | null;

    open: boolean;

    onOpenChange: (open: boolean) => void;

}

export default function EventDetails({

    event,

    open,

    onOpenChange,

}: Props) {

    if (!event) return null;

    return (

        <Dialog
            open={open}
            onOpenChange={onOpenChange}
        >

            <DialogContent className="max-w-3xl">

                <DialogHeader>

                    <DialogTitle>

                        Event Investigation

                    </DialogTitle>

                </DialogHeader>

                <ScrollArea className="max-h-[600px]">

                    <div className="space-y-5">

                        <div>

                            <strong>ID</strong>

                            <p>{event.id}</p>

                        </div>

                        <div>

                            <strong>Event Type</strong>

                            <p>{event.event_type}</p>

                        </div>

                        <div>

                            <strong>Severity</strong>

                            <p>{event.severity}</p>

                        </div>

                        <div>

                            <strong>Source</strong>

                            <p>{event.source}</p>

                        </div>

                        <div>

                            <strong>Message</strong>

                            <p>{event.message}</p>

                        </div>

                        <div>

                            <strong>Created</strong>

                            <p>{event.created_at}</p>

                        </div>

                        <div>

                            <strong>Metadata</strong>

                            <div className="space-y-3">

{event.event_metadata &&
Object.entries(event.event_metadata).map(([key,value])=>(

<div
key={key}
className="flex min-w-0 flex-col gap-1 border-b border-border pb-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4"
>
    <span className="shrink-0 text-sm font-semibold capitalize text-foreground">
        {key.replaceAll("_"," ")}
    </span>

    <span className="min-w-0 break-all text-sm text-muted-foreground sm:text-right">
        {String(value)}
    </span>
</div>

))}

</div>

                        </div>

                    </div>

                    <ThreatIntelligence
                        eventType={event.event_type}
                        metadata={event.event_metadata ?? {}}
                    />

                </ScrollArea>

            </DialogContent>

        </Dialog>

    );

}