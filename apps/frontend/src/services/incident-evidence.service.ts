import { api } from "@/services/api";

import type {
    IncidentEvidence,
    IncidentEvidenceCreate,
} from "@/types/incident-evidence";

/**
 * Return investigation evidence associated with an incident.
 */
export async function getIncidentEvidence(
    incidentId: number
): Promise<IncidentEvidence[]> {
    const response = await api.get<IncidentEvidence[]>(
        `/incidents/${incidentId}/evidence`
    );

    return response.data;
}

/**
 * Add analyst-provided evidence to an incident investigation.
 * 
 * The backend also creates the corresponding EVIDENCE_ADDED timeline activity as part of the same database transaction.
 */
export async function addIncidentEvidence(
    incidentId: number,
    evidence: IncidentEvidenceCreate
): Promise<IncidentEvidence> {
    const response = await api.post<IncidentEvidence>(
        `/incidents/${incidentId}/evidence`,
        evidence
    );

    return response.data;
}