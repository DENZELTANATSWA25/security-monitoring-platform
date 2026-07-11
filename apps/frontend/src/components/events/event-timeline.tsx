"use client";


import {
    Activity,
    AlertTriangle,
    ShieldAlert
} from "lucide-react";


import {
    useEvents
} from "@/hooks/use-events";



function SeverityIcon({
severity
}:{
severity:string
}){


if(severity==="CRITICAL")
return <ShieldAlert className="text-red-600"/>;


if(severity==="WARNING")
return <AlertTriangle className="text-yellow-600"/>;


return <Activity className="text-blue-600"/>;

}



export default function EventTimeline(){


const {
data,
isLoading
}=useEvents();



if(isLoading)
return <p>Loading events...</p>;



return (

<div className="
bg-white
rounded-xl
border
p-6
mt-8
">


<h2 className="
text-xl
font-bold
mb-6
">

Security Event Timeline

</h2>



<div className="
space-y-5
">


{
data?.map(event=>(


<div
key={event.id}
className="
flex
gap-4
border-l-2
pl-4
"
>


<div>

<SeverityIcon
severity={event.severity}
/>

</div>



<div>


<div className="
flex
gap-3
items-center
">

<h3 className="
font-semibold
">

{event.event_type}

</h3>


<span className="
text-sm
text-slate-500
">

{event.severity}

</span>


</div>



<p className="
text-sm
text-slate-600
">

{event.message}

</p>



<p className="
text-xs
text-slate-400
mt-1
">

{new Date(
event.created_at
).toLocaleString()}

</p>


</div>


</div>


))

}


</div>


</div>

)

}