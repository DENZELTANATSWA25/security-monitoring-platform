"use client";

import Sidebar from "./sidebar";
import Header from "./navbar";

export default function AppLayout({
    children
}:{
    children:React.ReactNode
}){
    return(
        <div className="flex">
            <Sidebar/>
            <div className="flex-1">
                <Header/>
                <main className="p-8">
                    {children}
                </main>
            </div>
        </div>
    )
}