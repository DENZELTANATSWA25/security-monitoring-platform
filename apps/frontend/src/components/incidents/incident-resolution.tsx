"use client";

import {
    useState,
} from "react";

import {
    CheckCircle2,
    Pencil,
    Save,
} from "lucide-react";

import {
    useIncidentResolution,
    useUpsertIncidentResolution,
} from "@/hooks/use-incident-resolution";

import type {
    ResolutionClassification,
} from "@/types/incident-resolution";

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
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";


interface IncidentResolutionProps {
    incidentId: number;
    canManage: boolean;
}


const CLASSIFICATIONS: Array<{
    value: ResolutionClassification;
    label: string;
}> = [
    {
        value: "TRUE_POSITIVE",
        label: "True Positive",
    },
    {
        value: "FALSE_POSITIVE",
        label: "False Positive",
    },
    {
        value: "BENIGN",
        label: "Benign",
    },
    {
        value: "DUPLICATE",
        label: "Duplicate",
    },
    {
        value: "INCONCLUSIVE",
        label: "Inconclusive",
    },
];


function getClassificationLabel(
    classification: ResolutionClassification
): string {
    return (
        CLASSIFICATIONS.find(
            (item) =>
                item.value === classification
        )?.label
        ?? classification
    );
}


export default function IncidentResolution({
    incidentId,
    canManage,
}: IncidentResolutionProps) {
    const {
        data: resolution,
        isLoading,
        error,
    } = useIncidentResolution(incidentId);

    const upsertResolution =
        useUpsertIncidentResolution(incidentId);

    const [isEditing, setIsEditing] =
        useState(false);

    const [classification, setClassification] =
        useState<ResolutionClassification>(
            "TRUE_POSITIVE"
        );

    const [summary, setSummary] =
        useState("");

    const [rootCause, setRootCause] =
        useState("");

    const [remediation, setRemediation] =
        useState("");

    const [formError, setFormError] =
        useState<string | null>(null);


    function beginEditing() {
        if (resolution) {
            setClassification(
                resolution.classification
            );
            setSummary(
                resolution.summary
            );
            setRootCause(
                resolution.root_cause ?? ""
            );
            setRemediation(
                resolution.remediation ?? ""
            );
        } else {
            setClassification(
                "TRUE_POSITIVE"
            );
            setSummary("");
            setRootCause("");
            setRemediation("");
        }

        setFormError(null);
        setIsEditing(true);
    }


    function cancelEditing() {
        setFormError(null);
        setIsEditing(false);
    }


    async function handleSave() {
        const cleanedSummary =
            summary.trim();

        if (!cleanedSummary) {
            setFormError(
                "Resolution summary is required."
            );
            return;
        }

        setFormError(null);

        try {
            await upsertResolution.mutateAsync({
                classification,
                summary: cleanedSummary,
                root_cause:
                    rootCause.trim() || null,
                remediation:
                    remediation.trim() || null,
            });

            setIsEditing(false);
        } catch {
            setFormError(
                "Unable to save the incident resolution. Please try again."
            );
        }
    }


    const showEditor =
        canManage
        && (
            isEditing
            || !resolution
        );


    return (
        <Card>
            <CardHeader>
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
                    <div>
                        <CardTitle>
                            Resolution / Conclusion
                        </CardTitle>

                        <p className="mt-1 text-sm text-muted-foreground">
                            Document the final investigation
                            conclusion and response taken.
                        </p>
                    </div>


                    {canManage
                        && resolution
                        && !isEditing && (
                            <Button
                                type="button"
                                variant="outline"
                                onClick={beginEditing}
                            >
                                <Pencil className="mr-2 h-4 w-4" />

                                Edit resolution
                            </Button>
                        )}
                </div>
            </CardHeader>


            <CardContent className="space-y-5">

                {isLoading && (
                    <p className="text-sm text-muted-foreground">
                        Loading resolution...
                    </p>
                )}


                {error && (
                    <p className="text-sm text-red-600">
                        Unable to load the incident resolution.
                    </p>
                )}


                {!isLoading
                    && !error
                    && !resolution
                    && !showEditor && (
                        <div
                            className="
                                rounded-lg
                                border
                                border-dashed
                                p-6
                                text-center
                            "
                        >
                            <CheckCircle2
                                className="
                                    mx-auto
                                    h-6
                                    w-6
                                    text-muted-foreground
                                "
                            />

                            <p className="mt-3 font-medium">
                                No resolution recorded
                            </p>

                            <p
                                className="
                                    mt-1
                                    text-sm
                                    text-muted-foreground
                                "
                            >
                                The investigation has not yet
                                been given a final conclusion.
                            </p>
                        </div>
                    )}


                {!isLoading
                    && !error
                    && resolution
                    && !isEditing && (
                        <div className="space-y-5">
                            <div>
                                <p
                                    className="
                                        text-xs
                                        font-medium
                                        uppercase
                                        tracking-wide
                                        text-muted-foreground
                                    "
                                >
                                    Classification
                                </p>

                                <div
                                    className="
                                        mt-2
                                        inline-flex
                                        items-center
                                        gap-2
                                        rounded-md
                                        border
                                        px-3
                                        py-1.5
                                        text-sm
                                        font-medium
                                    "
                                >
                                    <CheckCircle2 className="h-4 w-4" />

                                    {getClassificationLabel(
                                        resolution.classification
                                    )}
                                </div>
                            </div>


                            <div>
                                <p className="text-sm font-medium">
                                    Resolution summary
                                </p>

                                <p
                                    className="
                                        mt-1
                                        whitespace-pre-wrap
                                        text-sm
                                        text-muted-foreground
                                    "
                                >
                                    {resolution.summary}
                                </p>
                            </div>


                            {resolution.root_cause && (
                                <div>
                                    <p className="text-sm font-medium">
                                        Root cause
                                    </p>

                                    <p
                                        className="
                                            mt-1
                                            whitespace-pre-wrap
                                            text-sm
                                            text-muted-foreground
                                        "
                                    >
                                        {resolution.root_cause}
                                    </p>
                                </div>
                            )}


                            {resolution.remediation && (
                                <div>
                                    <p className="text-sm font-medium">
                                        Remediation
                                    </p>

                                    <p
                                        className="
                                            mt-1
                                            whitespace-pre-wrap
                                            text-sm
                                            text-muted-foreground
                                        "
                                    >
                                        {resolution.remediation}
                                    </p>
                                </div>
                            )}


                            <div
                                className="
                                    flex
                                    flex-wrap
                                    gap-x-4
                                    gap-y-1
                                    border-t
                                    pt-4
                                    text-xs
                                    text-muted-foreground
                                "
                            >
                                <span>
                                    Resolved by:{" "}
                                    {resolution.resolved_by
                                        ? `${resolution.resolved_by.full_name} (${resolution.resolved_by.role})`
                                        : "Deleted user"}
                                </span>

                                <span>
                                    Updated:{" "}
                                    {new Date(
                                        resolution.updated_at
                                    ).toLocaleString()}
                                </span>
                            </div>
                        </div>
                    )}


                {!isLoading
                    && !error
                    && showEditor && (
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
                                    {resolution
                                        ? "Update resolution"
                                        : "Record resolution"}
                                </p>

                                <p className="text-sm text-muted-foreground">
                                    Capture the investigation
                                    classification and conclusion.
                                </p>
                            </div>


                            <div className="space-y-2">
                                <label
                                    className="text-sm font-medium"
                                    htmlFor="resolution-classification"
                                >
                                    Classification
                                </label>

                                <Select
                                    value={classification}
                                    onValueChange={(selected) => {
                                        setClassification(
                                            selected as ResolutionClassification
                                        )
                                    }}
                                    disabled={
                                        upsertResolution.isPending
                                    }
                                >
                                    <SelectTrigger
                                        id="resolution-classification"
                                        className="w-full"
                                    >
                                        <SelectValue />
                                    </SelectTrigger>

                                    <SelectContent>
                                        {CLASSIFICATIONS.map(
                                            (item) => (
                                                <SelectItem
                                                    key={item.value}
                                                    value={item.value}
                                                >
                                                    {item.label}
                                                </SelectItem>
                                            )
                                        )}
                                    </SelectContent>
                                </Select>
                            </div>


                            <div className="space-y-2">
                                <label
                                    className="text-sm font-medium"
                                    htmlFor="resolution-summary"
                                >
                                    Resolution summary
                                </label>

                                <textarea
                                    id="resolution-summary"
                                    value={summary}
                                    onChange={(event) =>
                                        setSummary(
                                            event.target.value
                                        )
                                    }
                                    placeholder="Summarise the investigation conclusion."
                                    maxLength={10_000}
                                    disabled={
                                        upsertResolution.isPending
                                    }
                                    className="
                                        min-h-28
                                        w-full
                                        rounded-md
                                        border
                                        bg-background
                                        px-3
                                        py-2
                                        text-sm
                                        outline-none
                                        placeholder:text-muted-foreground
                                        focus-visible:ring-2
                                        focus-visible:ring-ring
                                        disabled:cursor-not-allowed
                                        disabled:opacity-50
                                    "
                                />
                            </div>


                            <div className="space-y-2">
                                <label
                                    className="text-sm font-medium"
                                    htmlFor="resolution-root-cause"
                                >
                                    Root cause
                                </label>

                                <textarea
                                    id="resolution-root-cause"
                                    value={rootCause}
                                    onChange={(event) =>
                                        setRootCause(
                                            event.target.value
                                        )
                                    }
                                    placeholder="Root cause (optional)"
                                    maxLength={10_000}
                                    disabled={
                                        upsertResolution.isPending
                                    }
                                    className="
                                        min-h-24
                                        w-full
                                        rounded-md
                                        border
                                        bg-background
                                        px-3
                                        py-2
                                        text-sm
                                        outline-none
                                        placeholder:text-muted-foreground
                                        focus-visible:ring-2
                                        focus-visible:ring-ring
                                        disabled:cursor-not-allowed
                                        disabled:opacity-50
                                    "
                                />
                            </div>


                            <div className="space-y-2">
                                <label
                                    className="text-sm font-medium"
                                    htmlFor="resolution-remediation"
                                >
                                    Remediation
                                </label>

                                <textarea
                                    id="resolution-remediation"
                                    value={remediation}
                                    onChange={(event) =>
                                        setRemediation(
                                            event.target.value
                                        )
                                    }
                                    placeholder="Response or remediation taken (optional)"
                                    maxLength={10_000}
                                    disabled={
                                        upsertResolution.isPending
                                    }
                                    className="
                                        min-h-24
                                        w-full
                                        rounded-md
                                        border
                                        bg-background
                                        px-3
                                        py-2
                                        text-sm
                                        outline-none
                                        placeholder:text-muted-foreground
                                        focus-visible:ring-2
                                        focus-visible:ring-ring
                                        disabled:cursor-not-allowed
                                        disabled:opacity-50
                                    "
                                />
                            </div>


                            {formError && (
                                <p className="text-sm text-red-600">
                                    {formError}
                                </p>
                            )}


                            <div className="flex flex-wrap gap-2">
                                <Button
                                    type="button"
                                    onClick={handleSave}
                                    disabled={
                                        upsertResolution.isPending
                                        || !summary.trim()
                                    }
                                >
                                    <Save className="mr-2 h-4 w-4" />

                                    {upsertResolution.isPending
                                        ? "Saving..."
                                        : resolution
                                            ? "Save changes"
                                            : "Record resolution"}
                                </Button>


                                {resolution && (
                                    <Button
                                        type="button"
                                        variant="outline"
                                        onClick={cancelEditing}
                                        disabled={
                                            upsertResolution.isPending
                                        }
                                    >
                                        Cancel
                                    </Button>
                                )}
                            </div>
                        </div>
                    )}
            </CardContent>
        </Card>
    );
}