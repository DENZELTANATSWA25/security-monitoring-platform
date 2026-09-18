import { api } from "@/services/api";

import type {
    IncidentAlertLink,
    IncidentEventLink,
} from "@/types/incident-link";

/**
 * Return additional security events attached to an incident investigation.
 * The incident's originating event is stored seperately on Incident.event_id.and is therefore not returned by this endpoint.
 */
export async function getIncidentEventLinks(
    incidentId: number
): Promise<IncidentEventLink[]> {
    const response = await api.get<IncidentEventLink[]>(
        `/incidents/${incidentId}/events`
    );

    return response.data;
}

/**
 * Attach an additional security event to an incident investigation.
 */
export async function linkEventToIncident(
    incidentId: number,
    eventId: number
): Promise<IncidentEventLink> {
    const response = await api.post<IncidentEventLink>(
        `/incidents/${incidentId}/events/${eventId}`
    );

    return response.data;
}

/**
 * Return alerts attached to an incident investigation.
 */
export async function getIncidentAlertLinks(
    incidentId: number
): Promise<IncidentAlertLink[]> {
    const response = await api.get<IncidentAlertLink[]>(
        `/incidents/${incidentId}/alerts`
    );

    return response.data;
}

/**
 * Attach an alert to an incident investigation.
 */
export async function linkAlertToIncident(
    incidentId: number,
    alertId: number
): Promise<IncidentAlertLink> {
    const response = await api.post<IncidentAlertLink>(
        `/incidents/${incidentId}/alerts/${alertId}`
    );

    return response.data;
}