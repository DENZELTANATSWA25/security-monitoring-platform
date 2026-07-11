"use client";


import {useDashboard} from "@/hooks/use-dashboard";
import EventsTable from "@/components/dashboard/event-table";
import AlertsPanel from "@/components/dashboard/alerts-panel";


export default function Home(){


const {
data,
isLoading,
error
}=useDashboard();



if(isLoading)
return <div>Loading...</div>



if(error)
return <div>
Backend connection failed
</div>



if(!data)
return <div>
No dashboard data available
</div>



return (

<div className="p-10 space-y-8">


<h1 className="text-3xl font-bold">
Security Dashboard
</h1>



<div className="grid grid-cols-3 gap-5">


<div className="border rounded-xl p-5">

<h3>Total Events</h3>

<p className="text-3xl">
{data.total_events}
</p>

</div>



<div className="border rounded-xl p-5">

<h3>Critical Events</h3>

<p className="text-3xl">
{data.critical_events}
</p>

</div>



<div className="border rounded-xl p-5">

<h3>Active Alerts</h3>

<p className="text-3xl">
{data.active_alerts}
</p>

</div>



</div>



<EventsTable/>

<AlertsPanel/>


</div>

);


}