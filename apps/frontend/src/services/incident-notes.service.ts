import { api } from "./api";

import {
    IncidentNote,
    IncidentNoteCreate,
} from "@/types/incident-note";

export async function getIncidentNotes(
    incidentId: number
) : Promise<IncidentNote[]> {
    const response = await api.get<IncidentNote[]>(
        `/incidents/${incidentId}/notes`
    );

    return response.data;
}

export async function createIncidentNote(
    incidentId: number,
    payload: IncidentNoteCreate
): Promise<IncidentNote> {
    const response = await api.post<IncidentNote>(
        `/incidents/${incidentId}/notes`,
        payload
    );

    return response.data;
}