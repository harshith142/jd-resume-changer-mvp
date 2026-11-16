import { DashboardLayoutClient } from './DashboardLayoutClient';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: 'LayoutDashboard' },
  { name: 'Resumes', href: '/dashboard/resumes', icon: 'FileText' },
  { name: 'Job Descriptions', href: '/dashboard/job-descriptions', icon: 'Briefcase' },
  { name: 'History', href: '/dashboard/history', icon: 'History' },
  { name: 'Settings', href: '/dashboard/settings', icon: 'Settings' },
];

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <DashboardLayoutClient
      navigation={navigation}
      session={{ user: { name: 'User', email: '' } }}
    >
      {children}
    </DashboardLayoutClient>
  );
}