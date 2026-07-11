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


export default function EventsTable(){


const {
data,
isLoading
}=useEvents();



if(isLoading)
return <div>Loading events...</div>



return (

<div className="mt-10">


<h2 className="text-xl font-bold mb-4">
Recent Security Events
</h2>


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
data?.map((event)=>(

<TableRow key={event.id}>

<TableCell>
{event.id}
</TableCell>


<TableCell>
{event.event_type}
</TableCell>


<TableCell>
{event.severity}
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


</div>

);


}