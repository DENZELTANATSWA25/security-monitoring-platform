export interface Alert {
    id: number;
    alert_type: string;
    severity: string;
    message: string;
    resolved: boolean;
    created_at: string;
}