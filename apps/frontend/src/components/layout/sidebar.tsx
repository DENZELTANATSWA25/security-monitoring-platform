"use client";

import Link from "next/link";
import {
    LayoutDashboard,
    ShieldAlert,
    Search,
    Users,
    Settings,
    FileText,
    ScrollText
} from "lucide-react";


const navigation = [

    {
        name:"Dashboard",
        href:"/",
        icon:LayoutDashboard,
    },

    {
        name:"Alerts",
        href:"/alerts",
        icon:ShieldAlert,
    },

    {
        name:"Investigations",
        href:"/investigations",
        icon:Search,
    },

    {
        name:"Users",
        href:"/users",
        icon:Users,
    },

    {
        name:"Rules",
        href:"/rules",
        icon:ScrollText,
    },

    {
        name:"Reports",
        href:"/reports",
        icon:FileText,
    },

    {
        name:"Settings",
        href:"/settings",
        icon:Settings,
    }

];


export default function Sidebar(){

return (

<aside className="
w-64
min-h-screen
border-r
bg-slate-950
text-white
p-5
">


<h1 className="
text-xl
font-bold
mb-8
">
Security Monitor
</h1>


<nav className="space-y-2">


{
navigation.map((item)=>{

const Icon=item.icon;


return (

<Link
key={item.name}
href={item.href}
className="
flex
items-center
gap-3
rounded-lg
px-3
py-2
hover:bg-slate-800
transition
"
>


<Icon size={18}/>

<span>
{item.name}
</span>


</Link>

)

})
}


</nav>


</aside>

)

}