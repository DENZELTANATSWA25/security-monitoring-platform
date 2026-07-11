import {Badge} from "@/components/ui/badge";


export default function SeverityBadge({
    severity
}:{
    severity:string
}){


const styles:Record<string,string> = {

CRITICAL:
"bg-red-600 text-white",

ERROR:
"bg-orange-500 text-white",

WARNING:
"bg-yellow-400 text-black",

INFO:
"bg-blue-500 text-white"

};


return (

<Badge
className={styles[severity]}
>

{severity}

</Badge>

)

}