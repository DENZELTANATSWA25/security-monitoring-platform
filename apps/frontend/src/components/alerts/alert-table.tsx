"use client";


import {
Table,
TableBody,
TableCell,
TableHead,
TableHeader,
TableRow
} from "@/components/ui/table";


import {
Button
} from "@/components/ui/button";


import SeverityBadge
from "./severity-badge";


import {
useAlerts,
useResolveAlert
}
from "@/hooks/use-alerts";



export default function AlertTable(){


const {
data,
isLoading
}=useAlerts();


const resolve =
useResolveAlert();



if(isLoading)
return <p>Loading alerts...</p>;



return (

<div className="
bg-white
rounded-xl
border
p-5
">


<h2 className="
text-xl
font-bold
mb-5
">

Security Alerts

</h2>



<Table>


<TableHeader>

<TableRow>

<TableHead>
Severity
</TableHead>

<TableHead>
Type
</TableHead>

<TableHead>
Message
</TableHead>

<TableHead>
Status
</TableHead>

<TableHead>
Action
</TableHead>

</TableRow>

</TableHeader>



<TableBody>


{
data?.map(alert=>(


<TableRow key={alert.id}>


<TableCell>

<SeverityBadge
severity={alert.severity}
/>

</TableCell>



<TableCell>
{alert.alert_type}
</TableCell>



<TableCell>
{alert.message}
</TableCell>



<TableCell>

{
alert.resolved
?
"Resolved"
:
"Open"
}

</TableCell>



<TableCell>


{
!alert.resolved &&

<Button

onClick={()=>
resolve.mutate(alert.id)
}

>

Resolve

</Button>

}


</TableCell>


</TableRow>


))

}


</TableBody>


</Table>


</div>

)

}