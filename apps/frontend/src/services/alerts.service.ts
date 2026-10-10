import { api } from "./api";
import { Alert } from "@/types/alert";

export interface AlertQueryParams {
    limit?: number;
    offset?: number;
    resolved?: boolean;
    severity?: string;
    alert_type?: string;
    start_date?: string;
    end_date?: string;
    search?: string;
    sort_order?: "asc" | "desc";
}

export async function getAlerts(
    params: AlertQueryParams = {}
): Promise<Alert[]> {
    const response = await api.get<Alert[]>(
        "/alerts/",
        { params }
    );

    return response.data;
}

export async function getAlertById(
    id: number
): Promise<Alert> {
    const response = await api.get<Alert>(
        `/alerts/${id}`
    );

    return response.data;
}

export async function resolveAlert(
    id: number
): Promise<Alert> {
    const response = await api.patch<Alert>(
        `/alerts/${id}/resolve`
    );
    
    return response.data;
}