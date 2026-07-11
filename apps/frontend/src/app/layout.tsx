import "./globals.css";

import QueryProvider from "@/providers/query-provider";


export const metadata = {
  title:"Security Monitoring Platform",
  description:"Enterprise Security Monitoring Dashboard",
};


export default function RootLayout({
 children,
}:{
 children:React.ReactNode;
}){

 return (

<html lang="en">

<body>

<QueryProvider>

{children}

</QueryProvider>

</body>

</html>

 );

}