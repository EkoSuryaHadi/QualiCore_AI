import type {Metadata} from "next";import "./globals.css";
export const metadata:Metadata={title:{default:"QualiCore AI",template:"%s | QualiCore AI"},description:"AI-Powered Project Assurance Platform for EPC projects",applicationName:"QualiCore AI",icons:{icon:"/icon.svg"}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
