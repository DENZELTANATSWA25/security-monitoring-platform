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

/**
 * Locate an event by ID using the existing paginated events endpoint.
 *
 * The backend currently exposes event listing but no single-event
 * lookup. We therefore scan successive pages rather than assuming
 * the originating event is in the first 50 records.
 */
export async function getEventById(
    eventId: number
): Promise<SecurityEvent | null> {
    if (!Number.isInteger(eventId) || eventId <= 0) {
        return null;
    }

    const PAGE_SIZE = 100;
    let offset = 0;

    while (true) {
        const events = await getEvents({
            limit: PAGE_SIZE,
            offset,
        });

        const matchingEvent = events.find(
            (event) => event.id === eventId
        );

        if (matchingEvent) {
            return matchingEvent;
        }

        if (events.length < PAGE_SIZE) {
            return null;
        }

        offset += PAGE_SIZE;
    }
}