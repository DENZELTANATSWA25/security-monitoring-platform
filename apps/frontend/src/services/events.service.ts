import {api} from "./api";
import {SecurityEvent} from "@/types/event";

export interface EventQueryParams {
    limit?: number;
    offset?: number;
    severity?: string;
    event_type?: string;
    source?: string;
    start_date?: string;
    end_date?: string;
    search?: string;
    sort_order?: "asc" | "desc";
}


export async function getEvents(
    params: EventQueryParams = {}
): Promise<SecurityEvent[]> {
    const response = await api.get<SecurityEvent[]>(
        "/events",
        {
            params,
        }
    );


    return response.data;

}