import { api } from "./api";
import { EventTrend } from "@/types/analytics";

export async function getEventTrend() {
    const response = await api.get<EventTrend[]>(
        "/analytics/events"
    );
    
    return response.data;
}