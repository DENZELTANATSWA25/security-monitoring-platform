import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

interface Props {
    eventType: string;
    metadata: Record<string, string | number | boolean>;
}

export default function ThreatIntelligence({
    eventType,
    metadata,
}: Props) {

    let risk = "LOW";
    let mitre = "";
    let recommendations: string[] = [];

    switch (eventType) {

        case "SQL_INJECTION":
            risk = "HIGH";
            mitre = "T1190 - Exploit Public Facing Application";
            recommendations = [
                "Block attacking IP",
                "Inspect WAF logs",
                "Review web server logs",
                "Search for similar attacks",
            ];
            break;

        case "MALWARE_DETECTED":
            risk = "CRITICAL";
            mitre = "T1204 - User Execution";
            recommendations = [
                "Isolate affected host",
                "Run antivirus scan",
                "Collect forensic evidence",
            ];
            break;

        case "PRIVILEGE_ESCALATION":
            risk = "CRITICAL";
            mitre = "T1078 - Valid Accounts";
            recommendations = [
                "Disable compromised account",
                "Review admin activity",
                "Reset credentials",
            ];
            break;

        case "SUSPICIOUS_LOGIN":
            risk = "MEDIUM";
            mitre = "T1078 - Valid Accounts";
            recommendations = [
                "Verify user identity",
                "Check login history",
                "Force password reset",
            ];
            break;

        default:
            recommendations = [
                "Investigate manually",
            ];
    }

    return (

        <Card className="mt-6">

            <CardHeader>

                <CardTitle>
                    Threat Intelligence
                </CardTitle>

            </CardHeader>

            <CardContent className="space-y-4">

                <div>
                    <strong>Risk:</strong> {risk}
                </div>

                <div>
                    <strong>MITRE ATT&amp;CK:</strong>
                    <br />
                    {mitre}
                </div>

                <div>

                    <strong>Indicators of Compromise</strong>

                    <div className="mt-2 space-y-2">

                        {Object.entries(metadata).map(([key, value]) => (

                            <div
                                key={key}
                                className="flex justify-between border-b pb-2"
                            >

                                <span className="font-semibold capitalize">
                                    {key.replaceAll("_", " ")}
                                </span>

                                <span className="text-slate-600 break-all">
                                    {String(value)}
                                </span>

                            </div>

                        ))}

                    </div>

                </div>

                <div>

                    <strong>Recommended Actions</strong>

                    <ul className="list-disc pl-6 mt-2">

                        {recommendations.map(action => (

                            <li key={action}>
                                {action}
                            </li>

                        ))}

                    </ul>

                </div>

            </CardContent>

        </Card>

    );
}