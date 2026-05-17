// frontend/app/layout.tsx
import "./globals.css";
import { Inter, Playfair_Display } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
});

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined"
        />
      </head>
      {/* Attached bg-background and text-on-background right here */}
      <body className={`${inter.variable} ${playfair.variable} font-body bg-background text-on-background min-h-screen pb-32`}>
        {children}
      </body>
    </html>
  );
}