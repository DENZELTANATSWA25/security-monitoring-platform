export default function Navbar(){

return (

<header className="
h-16
border-b
flex
items-center
justify-between
px-6
bg-white
">


<div>

<h2 className="
font-semibold
">
Security Operations Center
</h2>

</div>


<div className="
flex
items-center
gap-4
">


<span className="
text-sm
text-green-600
">
● System Online
</span>


<div className="
rounded-full
bg-slate-200
px-3
py-1
text-sm
">
Admin
</div>


</div>


</header>

)

}