import { api } from './api';

import {
    Incident,
    IncidentCreate,
    IncidentStatus,
} from '@/types/incident';

export async function getIncidents() {
    const response = await api.get<Incident[]>(
        "/incidents"
    );

    return response.data;
}

export async function getIncident(
    id: number
) {
    const response = await api.get<Incident>(
        `/incidents/${id}`
    );

    return response.data;
}

export async function createIncident(
    data: IncidentCreate
) {
    const response = await api.post<Incident>(
        "/incidents",
        data
    );

    return response.data;
}

export async function assignIncident(
    id: number,
    userId: number
) {
    const response = await api.patch<Incident>(
        `/incidents/${id}/assign`,
        {
            user_id: userId
        }
    );

    return response.data;
}

export async function updateIncidentStatus(
    id: number,
    status: IncidentStatus
) {
    const response = await api.patch<Incident>(
        `/incidents/${id}/status/${status}`
    );

    return response.data;
}