"use client";


import {
Table,
TableBody,
TableCell,
TableHead,
TableHeader,
TableRow
} from "@/components/ui/table";

import {Badge} from "@/components/ui/badge";


import {useEvents} from "@/hooks/use-events";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import EventDetails from "./event-details";
import { SecurityEvent } from "@/types/event";


export default function EventsTable(){


const {
data,
isLoading
}=useEvents();

const [search, setSearch] = useState("");
const [selectedEvent, setSelectedEvent] = useState<SecurityEvent | null>(null);
const [dialogOpen, setDialogOpen] = useState(false);



if(isLoading)
return <div>Loading events...</div>


const filteredEvents =
    data?.filter((event) => {

        const query = search.toLowerCase();

        return (
            event.event_type.toLowerCase().includes(query) ||
            event.source.toLowerCase().includes(query) ||
            event.message.toLowerCase().includes(query)
        );

    }) ?? [];


return (

<div className="mt-10">


<h2 className="text-xl font-bold mb-4">
Recent Security Events
</h2>

<Input
placeholder="Search events..."
value={search}
onChange={(e) => setSearch(e.target.value)}
className="mb-4"
/>

<Table>

<TableHeader>

<TableRow>

<TableHead>
ID
</TableHead>

<TableHead>
Type
</TableHead>

<TableHead>
Severity
</TableHead>


<TableHead>
Source
</TableHead>


<TableHead>
Message
</TableHead>


</TableRow>

</TableHeader>



<TableBody>


{
filteredEvents.map((event)=>(

<TableRow

    key={event.id}

    className="cursor-pointer hover:bg-slate-100"

    onClick={() => {

        setSelectedEvent(event);

        setDialogOpen(true);

    }}

>

<TableCell>
{event.id}
</TableCell>

<TableCell>
{event.event_type}
</TableCell>

<TableCell>


<Badge
variant={
    event.severity === "CRITICAL"
    ? "destructive"
    : "outline"
}
>
{event.severity}
</Badge>
</TableCell>


<TableCell>
{event.source}
</TableCell>


<TableCell>
{event.message}
</TableCell>


</TableRow>


))

}


</TableBody>


</Table>

<EventDetails
event={selectedEvent}
open={dialogOpen}
onOpenChange={setDialogOpen}
/>

</div>

);


}