import Sidebar from "./sidebar";
import Navbar from "./navbar";


export default function DashboardLayout({
children
}:{
children:React.ReactNode
}){


return (

<div className="
flex
min-h-screen
bg-slate-100
">


<Sidebar/>


<div className="
flex-1
">


<Navbar/>


<main className="
p-6
">

{children}

</main>


</div>


</div>

)

}