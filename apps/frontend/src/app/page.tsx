"use client";


import {useDashboard} from "@/hooks/use-dashboard";
import EventsTable from "@/components/dashboard/event-table";
import AlertsPanel from "@/components/dashboard/alerts-panel";
import StatCard from "@/components/dashboard/stat-card";
import DashboardGrid from "@/components/dashboard/dashboard-grid";


export default function Home(){


const {
data,
isLoading,
error
}=useDashboard();



if(isLoading)
return <div>Loading Dashboard...</div>



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

<DashboardGrid
data={data}
/>

<EventsTable/>

<AlertsPanel/>


</div>

);


}