import {useQuery} from "@tanstack/react-query";
import {getDashboardSummary} from "@/services/dashboard.service";

export function useDashboard() {
    return useQuery({
        queryKey: ["dashboard-summary"],
        queryFn: getDashboardSummary,
    });
}