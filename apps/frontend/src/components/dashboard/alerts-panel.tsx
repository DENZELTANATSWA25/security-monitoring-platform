"use client";

import {Button} from "@/components/ui/button";
import {useMutation, useQueryClient} from "@tanstack/react-query";
import {resolveAlert} from "@/services/alerts.service"; 


import {useAlerts} from "@/hooks/use-alerts";

import {
Badge
} from "@/components/ui/badge";



export default function AlertsPanel(){


const {
data,
isLoading
}=useAlerts();

const queryClient = useQueryClient();
const mutation = useMutation({
    mutationFn: resolveAlert,
    onSuccess: () => {
        queryClient.invalidateQueries({
            queryKey: ["alerts"]
        });
    },
});



if(isLoading)
return <p>
Loading alerts...
</p>;



return (

<div className="mt-10">


<h2 className="text-xl font-bold mb-4">
Active Security Alerts
</h2>



<div className="space-y-4">


{
data
?.filter(alert=>!alert.resolved)
.map(alert=>(


<div
key={alert.id}
className="
border
rounded-xl
p-5
"
>


<div className="
flex
justify-between
"
>


<h3 className="
font-bold
">

{alert.alert_type}

</h3>


<Badge
variant={
    alert.severity==="CRITICAL"
    ?"destructive"
    :"secondary"
}
>

{alert.severity}

</Badge>


</div>



<p className="mt-2">

{alert.message}

</p>
<Button
className="mt-4"
onClick={() => mutation.mutate(alert.id)}
>
    Resolve
</Button>


<p className="
text-sm
text-gray-500
mt-2
">

{
new Date(
alert.created_at
).toLocaleString()
}

</p>


</div>


))


}


</div>


</div>

)

}