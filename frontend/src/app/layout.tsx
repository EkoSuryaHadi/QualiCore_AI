import type {Metadata} from "next";import "./globals.css";
export const metadata:Metadata={title:"QualiCore AI",description:"AI-Powered Project Assurance Platform"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
