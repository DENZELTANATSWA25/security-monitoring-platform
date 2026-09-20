"use client";

import {
    useState,
} from "react";

import {
    FileKey2,
    Plus,
} from "lucide-react";

import {
    useAddIncidentEvidence,
    useIncidentEvidence,
} from "@/hooks/use-incident-evidence";

import type {
    EvidenceType,
} from "@/types/incident-evidence";

import {
    Button,
} from "@/components/ui/button";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

import {
    Input,
} from "@/components/ui/input";

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";


interface IncidentEvidenceProps {
    incidentId: number;
    canManage: boolean;
}


const EVIDENCE_TYPES: Array<{
    value: EvidenceType;
    label: string;
}> = [
    {
        value: "IP_ADDRESS",
        label: "IP Address",
    },
    {
        value: "DOMAIN",
        label: "Domain",
    },
    {
        value: "URL",
        label: "URL",
    },
    {
        value: "FILE_HASH",
        label: "File Hash",
    },
    {
        value: "USERNAME",
        label: "Username",
    },
    {
        value: "HOSTNAME",
        label: "Hostname",
    },
    {
        value: "PROCESS",
        label: "Process",
    },
    {
        value: "OTHER",
        label: "Other",
    },
];


function getEvidenceTypeLabel(
    evidenceType: EvidenceType
): string {
    return (
        EVIDENCE_TYPES.find(
            (item) =>
                item.value === evidenceType
        )?.label
        ?? evidenceType
    );
}


export default function IncidentEvidence({
    incidentId,
    canManage,
}: IncidentEvidenceProps) {
    const {
        data: evidence = [],
        isLoading,
        error,
    } = useIncidentEvidence(incidentId);

    const addEvidence =
        useAddIncidentEvidence(incidentId);

    const [evidenceType, setEvidenceType] =
        useState<EvidenceType>("IP_ADDRESS");

    const [value, setValue] =
        useState("");

    const [description, setDescription] =
        useState("");

    const [source, setSource] =
        useState("");

    const [formError, setFormError] =
        useState<string | null>(null);


    async function handleAddEvidence() {
        const cleanedValue = value.trim();

        if (!cleanedValue) {
            setFormError(
                "Evidence value is required."
            );
            return;
        }

        setFormError(null);

        try {
            await addEvidence.mutateAsync({
                evidence_type: evidenceType,
                value: cleanedValue,
                description:
                    description.trim() || null,
                source:
                    source.trim() || null,
            });

            setValue("");
            setDescription("");
            setSource("");
        } catch {
            setFormError(
                "Unable to add evidence. Please try again."
            );
        }
    }


    return (
        <Card>
            <CardHeader>
                <div
                    className="
                        flex
                        flex-col
                        gap-2
                        sm:flex-row
                        sm:items-center
                        sm:justify-between
                    "
                >
                    <div>
                        <CardTitle>
                            Evidence / Artifacts
                        </CardTitle>

                        <p className="mt-1 text-sm text-muted-foreground">
                            Analyst-provided investigation artifacts
                            associated with this incident.
                        </p>
                    </div>

                    <div
                        className="
                            flex
                            items-center
                            gap-2
                            text-sm
                            text-muted-foreground
                        "
                    >
                        <FileKey2 className="h-4 w-4" />

                        <span>
                            {evidence.length} artifact
                            {evidence.length === 1
                                ? ""
                                : "s"}
                        </span>
                    </div>
                </div>
            </CardHeader>


            <CardContent className="space-y-6">

                {canManage && (
                    <div
                        className="
                            space-y-4
                            rounded-lg
                            border
                            p-4
                        "
                    >
                        <div>
                            <p className="font-medium">
                                Add evidence
                            </p>

                            <p className="text-sm text-muted-foreground">
                                Record an investigation artifact
                                discovered during analysis.
                            </p>
                        </div>


                        <div
                            className="
                                grid
                                grid-cols-1
                                gap-3
                                lg:grid-cols-2
                            "
                        >
                            <Select
                                value={evidenceType}
                                onValueChange={(selected) => {
                                    if (selected) {
                                        setEvidenceType(
                                            selected as EvidenceType
                                        );
                                    }
                                }}
                                disabled={addEvidence.isPending}
                            >
                                <SelectTrigger className="w-full">
                                    <SelectValue />
                                </SelectTrigger>

                                <SelectContent>
                                    {EVIDENCE_TYPES.map(
                                        (type) => (
                                            <SelectItem
                                                key={type.value}
                                                value={type.value}
                                            >
                                                {type.label}
                                            </SelectItem>
                                        )
                                    )}
                                </SelectContent>
                            </Select>


                            <Input
                                value={value}
                                onChange={(event) =>
                                    setValue(
                                        event.target.value
                                    )
                                }
                                placeholder="Evidence value"
                                maxLength={10_000}
                                disabled={addEvidence.isPending}
                            />


                            <Input
                                value={source}
                                onChange={(event) =>
                                    setSource(
                                        event.target.value
                                    )
                                }
                                placeholder="Source (optional)"
                                maxLength={255}
                                disabled={addEvidence.isPending}
                            />


                            <Input
                                value={description}
                                onChange={(event) =>
                                    setDescription(
                                        event.target.value
                                    )
                                }
                                placeholder="Description (optional)"
                                maxLength={10_000}
                                disabled={addEvidence.isPending}
                            />
                        </div>


                        {formError && (
                            <p className="text-sm text-red-600">
                                {formError}
                            </p>
                        )}


                        <Button
                            type="button"
                            onClick={handleAddEvidence}
                            disabled={
                                addEvidence.isPending
                                || !value.trim()
                            }
                        >
                            <Plus className="mr-2 h-4 w-4" />

                            {addEvidence.isPending
                                ? "Adding..."
                                : "Add evidence"}
                        </Button>
                    </div>
                )}


                {isLoading && (
                    <p className="text-sm text-muted-foreground">
                        Loading evidence...
                    </p>
                )}


                {error && (
                    <p className="text-sm text-red-600">
                        Unable to load investigation evidence.
                    </p>
                )}


                {!isLoading
                    && !error
                    && evidence.length === 0 && (
                        <div
                            className="
                                rounded-lg
                                border
                                border-dashed
                                p-6
                                text-center
                            "
                        >
                            <FileKey2
                                className="
                                    mx-auto
                                    h-6
                                    w-6
                                    text-muted-foreground
                                "
                            />

                            <p className="mt-3 font-medium">
                                No evidence recorded
                            </p>

                            <p
                                className="
                                    mt-1
                                    text-sm
                                    text-muted-foreground
                                "
                            >
                                Investigation artifacts added by
                                analysts will appear here.
                            </p>
                        </div>
                    )}


                {!isLoading
                    && !error
                    && evidence.length > 0 && (
                        <div className="space-y-3">
                            {evidence.map((item) => (
                                <div
                                    key={item.id}
                                    className="
                                        rounded-lg
                                        border
                                        p-4
                                    "
                                >
                                    <div
                                        className="
                                            flex
                                            flex-col
                                            gap-3
                                            sm:flex-row
                                            sm:items-start
                                            sm:justify-between
                                        "
                                    >
                                        <div className="min-w-0">
                                            <p
                                                className="
                                                    text-xs
                                                    font-medium
                                                    uppercase
                                                    tracking-wide
                                                    text-muted-foreground
                                                "
                                            >
                                                {getEvidenceTypeLabel(
                                                    item.evidence_type
                                                )}
                                            </p>

                                            <p
                                                className="
                                                    mt-1
                                                    break-all
                                                    font-mono
                                                    text-sm
                                                    font-semibold
                                                "
                                            >
                                                {item.value}
                                            </p>
                                        </div>


                                        <p
                                            className="
                                                shrink-0
                                                text-xs
                                                text-muted-foreground
                                            "
                                        >
                                            {new Date(
                                                item.created_at
                                            ).toLocaleString()}
                                        </p>
                                    </div>


                                    {item.description && (
                                        <p
                                            className="
                                                mt-3
                                                text-sm
                                                text-muted-foreground
                                            "
                                        >
                                            {item.description}
                                        </p>
                                    )}


                                    <div
                                        className="
                                            mt-3
                                            flex
                                            flex-wrap
                                            gap-x-4
                                            gap-y-1
                                            text-xs
                                            text-muted-foreground
                                        "
                                    >
                                        {item.source && (
                                            <span>
                                                Source: {item.source}
                                            </span>
                                        )}

                                        <span>
                                            Added by:{" "}
                                            {item.added_by
                                                ? `${item.added_by.full_name} (${item.added_by.role})`
                                                : "Deleted user"}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
            </CardContent>
        </Card>
    );
}