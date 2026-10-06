import './globals.css';

export const metadata = {
  title: 'SiteLens AI Dashboard',
  description: 'Construction site safety and management dashboard',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
