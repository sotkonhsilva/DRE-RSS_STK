import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "Portal de Procedimentos - Diário da República",
    description: "Diário da República - Série II - Parte L",
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="pt-PT">
            <body>{children}</body>
        </html>
    );
}
