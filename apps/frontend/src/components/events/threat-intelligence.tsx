import {Card, CardContent, CardHeader, CardTitle} from "@/components/ui/card";

interface Props {
    eventType: string;
    metadata: Record<string, unknown>;
}

export default function ThreatIntelligence({
    eventType,
    metadata
}: Props) {
    let mitre = "";
    let recommendation: string[] = [];
    let risk = "LOW";

    switch (eventType) {

        case "SQL_INJECTION":
            risk = "HIGH";
            mitre = "T1190 - Exploit Public Facing Application";

            recommendation = [
                "Block attacking IP",
                "Review web server logs",
                "Inspect WAF rules",
                "Search for similar attacks",
            ];
            break;

        case "MALWARE_DETECTED":
            risk = "CRITICIAL";
            mitre = "T1204 - User Execution";

            recommendation = [
                "Isolate endpoint",
                "Run antivirus scan",
                "Collect forensic evidence",
            ];
            break;

        case "PRIVILEGE_ESCALATION":
            risk = "CRITICIAL";
            mitre = "T1078 - Valid Accounts";

            recommendation = [
                "Disable affected account",
                "Review administrator activity",
                "Reset credentials",
            ];
            break;

        case "SUSPICIOUS_LOGIN":
            risk = "MEDIUM";
            mitre = "T1078";

            recommendation = [
                "Verify user identity",
                "Check login history",
                "Force password reset",
            ];
            break;

        default:
            recommendation = [
                "Investigate manually"
            ];
    }

    return (
        <Card className="mt-6">
            <CardHeader>
                <CardTitle>Threat Intelligence</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div>
                    <strong>Risk:</strong> {risk}
                </div>

                <div>
                    <strong>MITRE ATT&CK:</strong>
                    <br/>
                    {mitre}
                </div>

                <div>
                    <strong>Indicators of Compromise</strong>

                    <pre className="bg-slate-100 p-3 rounded mt-2">
                        {JSON.stringify(metadata, null, 2)}
                    </pre>
                </div>

                <div>

                    <strong>Recommended Actions</strong>

                    <ul className="list-disc pl-5 mt-2">

                        {recommendation.map(action => (<li key={action}>{action}</li>))}
                    </ul>
                </div>
            </CardContent>
        </Card>
    );
}