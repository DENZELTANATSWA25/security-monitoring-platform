import axios from "axios";

import { api } from "@/services/api";

import type {
    IncidentResolution,
    IncidentResolutionUpsert,
} from "@/types/incident-resolution";

/**
 * Return the current investigation resolution for an incident.
 * 
 * A 404 with "Incident resolution not found" represents a valid incident that has not yet been resolved and is therefore returned as null.
 */
export async function getIncidentResolution(
    incidentId: number
): Promise<IncidentResolution | null> {
    try {
        const response = await api.get<IncidentResolution>(
            `/incidents/${incidentId}/resolution`
        );

        return response.data;
    } catch (error) {

        if (
            axios.isAxiosError(error)
            && error.response?.status === 404
            && error.response?.data?.detail
                === "Incident resolution not found"
        ) {
            return null;
        }

        throw error;
    }
}

/**
 * Create or update the investigation resolution for an incident.
 * 
 * The backend records RESOLUTION_ADDED and RESOLUTION_UPDATED in the incident timeline as part of the same database transaction.
 */
export async function upsertIncidentResolution(
    incidentId: number,
    resolution: IncidentResolutionUpsert
): Promise<IncidentResolution> {
    const response = await api.put<IncidentResolution>(
        `/incidents/${incidentId}/resolution`,
        resolution
    );

    return response.data;
}