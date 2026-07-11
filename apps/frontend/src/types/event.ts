export interface SecurityEvent {
    id: number;
    event_type: string;
    severity:
        | "INFO"
        | "WARNING"
        | "ERROR"
        | "CRITICAL";
    source: string;
    message: string;
    created_at: string
}