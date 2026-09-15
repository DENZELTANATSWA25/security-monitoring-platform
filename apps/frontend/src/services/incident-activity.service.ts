import { api } from "./api";

import type {
    IncidentActivity,
} from "@/types/incident-activity";

export async function getIncidentActivities(
    incidentId: number
): Promise<IncidentActivity[]> {
    const response = await api.get<IncidentActivity[]>(
        `/incidents/${incidentId}/activities`
    );

    return response.data;
}
