// frontend/app/layout.tsx
import "./globals.css";

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
      <body className="font-body bg-background text-on-background min-h-screen pb-32">
        {children}
      </body>
    </html>
  );
}
