import AppLayout from "@/components/layout/app-layout";
import AuthGuard from "@/components/auth/auth-guard";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <AuthGuard>
            <AppLayout>
                {children}
            </AppLayout>
        </AuthGuard>
    );
}