import {api} from "./api";
import {Alert} from "@/types/alert";

export async function getAlerts() {
    const response = await api.get<Alert[]>(
        "/alerts"
    );
    return response.data;
}

export async function resolveAlert(
    id: number
){
    const response = await api.patch<Alert>(
        `/alerts/${id}/resolve`
    );
    
    return response.data;
}