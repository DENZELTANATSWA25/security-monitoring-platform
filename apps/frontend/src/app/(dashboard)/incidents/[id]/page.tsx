"use client";

import axios from "axios";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useIncident } from "@/hooks/use-incidents";
import { useIncidentResolution } from "@/hooks/use-incident-resolution";
import {
  useAssignableUsers,
  useCurrentUser,
} from "@/hooks/use-users";
import { useEvent } from "@/hooks/use-events";

import {
  assignIncident,
  updateIncidentStatus,
} from "@/services/incident.service";

import type { IncidentStatus } from "@/types/incident";

import { canManageIncidents } from "@/lib/permissions";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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

import InvestigationNotes from "@/components/incidents/investigation-notes";
import IncidentActivityTimeline from "@/components/incidents/incident-activity-timeline";
import IncidentEvidence from "@/components/incidents/incident-evidence";
import IncidentResolution from "@/components/incidents/incident-resolution";
import OriginatingEvent from "@/components/incidents/originating-event";
import LinkedEvents from "@/components/incidents/linked-events";
import LinkedAlerts from "@/components/incidents/linked-alerts";


export default function IncidentDetailsPage() {
  const params = useParams();
  const id = Number(params.id);

  const queryClient = useQueryClient();

  const {
    data: currentUser,
  } = useCurrentUser();

  const canManage =
    canManageIncidents(currentUser?.role);

  const {
    data: incident,
    isLoading,
    error,
  } = useIncident(id);

  /*
   * The status-management UI needs to know whether a documented
   * resolution exists before offering the RESOLVED transition.
   *
   * This does not replace backend enforcement. The backend remains
   * authoritative and independently validates every transition.
   */
  const {
    data: incidentResolution,
    isLoading: isLoadingResolution,
  } = useIncidentResolution(id);

  const {
    data: originatingEvent,
    isLoading: isLoadingSecurityEvents,
  } = useEvent(incident?.event_id ?? 0);

  const {
    data: assignableUsers = [],
    isLoading: isLoadingAssignableUsers,
  } = useAssignableUsers();

  const [
    selectedUserId,
    setSelectedUserId,
  ] = useState("");

  const [
    isAssigning,
    setIsAssigning,
  ] = useState(false);

  const [
    isUpdatingStatus,
    setIsUpdatingStatus,
  ] = useState(false);

  const [
    statusError,
    setStatusError,
  ] = useState<string | null>(null);


  if (isLoading) {
    return (
      <div className="p-6">
        Loading incident...
      </div>
    );
  }


  if (error || !incident) {
    return (
      <div className="p-6 space-y-4">
        <p className="text-red-600">
          Incident not found.
        </p>

        <Link
          href="/incidents"
          className="underline"
        >
          Back to incidents
        </Link>
      </div>
    );
  }


  const currentIncident = incident;


  /**
   * Assign an analyst or administrator to the incident.
   *
   * Assignment and lifecycle transitions are deliberately separate.
   * The backend only moves OPEN incidents to IN_PROGRESS as a side
   * effect of assignment; terminal incidents are never reopened here.
   */
  async function handleAssign() {
    if (!selectedUserId) {
      return;
    }

    const userId = Number(selectedUserId);

    if (Number.isNaN(userId)) {
      return;
    }

    try {
      setIsAssigning(true);

      await assignIncident(
        currentIncident.id,
        userId,
      );

      setSelectedUserId("");

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            "incident",
            currentIncident.id,
          ],
        }),

        queryClient.invalidateQueries({
          queryKey: ["incidents"],
        }),

        queryClient.invalidateQueries({
          queryKey: [
            "incident-activities",
            currentIncident.id,
          ],
        }),
      ]);
    } finally {
      setIsAssigning(false);
    }
  }


  /**
   * Request a lifecycle transition from the backend.
   *
   * The UI exposes only known-valid workflow actions, but backend
   * validation remains the source of truth. Any domain conflict is
   * therefore still surfaced to the analyst.
   */
  async function handleStatusChange(
    status: IncidentStatus,
  ) {
    try {
      setIsUpdatingStatus(true);
      setStatusError(null);

      await updateIncidentStatus(
        currentIncident.id,
        status,
      );

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            "incident",
            currentIncident.id,
          ],
        }),

        queryClient.invalidateQueries({
          queryKey: ["incidents"],
        }),

        queryClient.invalidateQueries({
          queryKey: [
            "incident-activities",
            currentIncident.id,
          ],
        }),
      ]);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detail =
          error.response?.data?.detail;

        if (typeof detail === "string") {
          setStatusError(detail);
          return;
        }
      }

      setStatusError(
        "Unable to update the incident status.",
      );
    } finally {
      setIsUpdatingStatus(false);
    }
  }


  return (
    <div className="space-y-6">

      {/* Header */}

      <div>
        <Link
          href="/incidents"
          className="text-sm underline"
        >
          ← Back to incidents
        </Link>

        <div className="flex items-center justify-between mt-4">
          <div>
            <h1 className="text-3xl font-bold">
              {currentIncident.title}
            </h1>

            <p className="text-muted-foreground mt-1">
              Incident #{currentIncident.id}
            </p>
          </div>

          <Badge>
            {currentIncident.status}
          </Badge>
        </div>
      </div>


      {/* Incident Overview */}

      <Card>
        <CardHeader>
          <CardTitle>
            Incident Overview
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">

          <div>
            <p className="text-sm text-muted-foreground">
              Description
            </p>

            <p className="mt-1">
              {currentIncident.description}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">

            <div>
              <p className="text-sm text-muted-foreground">
                Severity
              </p>

              <p className="font-semibold mt-1">
                {currentIncident.severity}
              </p>
            </div>


            <div>
              <p className="text-sm text-muted-foreground">
                Status
              </p>

              <p className="font-semibold mt-1">
                {currentIncident.status}
              </p>
            </div>


            <div>
              <p className="text-sm text-muted-foreground">
                Assigned Analyst
              </p>

              <p className="font-semibold mt-1">
                {
                  currentIncident.assigned_to
                  ?? "Unassigned"
                }
              </p>
            </div>


            <div>
              <p className="text-sm text-muted-foreground">
                Related Event
              </p>

              {currentIncident.event_id ? (
                <Link
                  href="/events"
                  className="font-semibold underline"
                >
                  Event #{currentIncident.event_id}
                </Link>
              ) : (
                <p className="font-semibold mt-1">
                  None
                </p>
              )}
            </div>

          </div>
        </CardContent>
      </Card>


      {/* Originating and linked events */}

      <div>
        <OriginatingEvent
          eventId={currentIncident.event_id}
          event={originatingEvent ?? undefined}
          isLoading={isLoadingSecurityEvents}
        />

        <LinkedEvents
          incidentId={currentIncident.id}
          originatingEventId={
            currentIncident.event_id
          }
          canManage={canManage}
        />
      </div>


      {/* Linked alerts */}

      <LinkedAlerts
        incidentId={currentIncident.id}
        canManage={canManage}
      />


      {/* Investigation evidence / artifacts */}

      <IncidentEvidence
        incidentId={currentIncident.id}
        canManage={canManage}
      />


      {/* Investigation resolution */}

      <IncidentResolution
        incidentId={currentIncident.id}
        canManage={canManage}
      />


      {/* Analyst Assignment */}

      {canManage && (
        <Card>
          <CardHeader>
            <CardTitle>
              Analyst Assignment
            </CardTitle>
          </CardHeader>

          <CardContent>
            <div className="flex flex-col sm:flex-row gap-3 max-w-xl">

              <Select
                value={selectedUserId}
                onValueChange={(value) =>
                  setSelectedUserId(
                    value ?? "",
                  )
                }
                disabled={
                  isAssigning
                  || isLoadingAssignableUsers
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue
                    placeholder={
                      isLoadingAssignableUsers
                        ? "Loading users..."
                        : "Select analyst or administrator"
                    }
                  />
                </SelectTrigger>

                <SelectContent>
                  {assignableUsers.map(
                    (user) => (
                      <SelectItem
                        key={user.id}
                        value={String(user.id)}
                      >
                        {user.full_name}
                        {" — "}
                        {user.role}
                      </SelectItem>
                    ),
                  )}
                </SelectContent>
              </Select>


              <Button
                onClick={handleAssign}
                disabled={
                  isAssigning
                  || !selectedUserId
                }
              >
                {
                  isAssigning
                    ? "Assigning..."
                    : "Assign"
                }
              </Button>

            </div>
          </CardContent>
        </Card>
      )}


      {/* Lifecycle-aware Status Management */}

      {canManage && (
        <Card>
          <CardHeader>
            <CardTitle>
              Incident Status
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">

            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">
                Current status
              </span>

              <Badge variant="outline">
                {currentIncident.status.replace(
                  "_",
                  " ",
                )}
              </Badge>
            </div>


            {/* OPEN */}

            {currentIncident.status === "OPEN" && (
              <div className="space-y-3">

                <div className="flex flex-wrap gap-3">

                  <Button
                    variant="outline"
                    disabled={isUpdatingStatus}
                    onClick={() =>
                      handleStatusChange(
                        "IN_PROGRESS",
                      )
                    }
                  >
                    {
                      isUpdatingStatus
                        ? "Updating..."
                        : "Start investigation"
                    }
                  </Button>


                  <Button
                    variant="outline"
                    disabled={
                      isUpdatingStatus
                      || isLoadingResolution
                      || !incidentResolution
                    }
                    onClick={() =>
                      handleStatusChange(
                        "RESOLVED",
                      )
                    }
                  >
                    Resolve incident
                  </Button>

                </div>


                {
                  !isLoadingResolution
                  && !incidentResolution
                  && (
                    <p className="text-sm text-muted-foreground">
                      Add an investigation resolution
                      before resolving this incident.
                    </p>
                  )
                }

              </div>
            )}


            {/* IN PROGRESS */}

            {
              currentIncident.status
              === "IN_PROGRESS"
              && (
                <div className="space-y-3">

                  <div className="flex flex-wrap gap-3">

                    <Button
                      variant="outline"
                      disabled={isUpdatingStatus}
                      onClick={() =>
                        handleStatusChange(
                          "OPEN",
                        )
                      }
                    >
                      Move to Open
                    </Button>


                    <Button
                      disabled={
                        isUpdatingStatus
                        || isLoadingResolution
                        || !incidentResolution
                      }
                      onClick={() =>
                        handleStatusChange(
                          "RESOLVED",
                        )
                      }
                    >
                      {
                        isUpdatingStatus
                          ? "Updating..."
                          : "Resolve incident"
                      }
                    </Button>

                  </div>


                  {
                    !isLoadingResolution
                    && !incidentResolution
                    && (
                      <p className="text-sm text-muted-foreground">
                        Add an investigation resolution
                        before resolving this incident.
                      </p>
                    )
                  }

                </div>
              )
            }


            {/* RESOLVED */}

            {
              currentIncident.status
              === "RESOLVED"
              && (
                <div className="flex flex-wrap gap-3">

                  <Button
                    variant="outline"
                    disabled={isUpdatingStatus}
                    onClick={() =>
                      handleStatusChange(
                        "IN_PROGRESS",
                      )
                    }
                  >
                    Reopen investigation
                  </Button>


                  <Button
                    disabled={isUpdatingStatus}
                    onClick={() =>
                      handleStatusChange(
                        "CLOSED",
                      )
                    }
                  >
                    {
                      isUpdatingStatus
                        ? "Updating..."
                        : "Close incident"
                    }
                  </Button>

                </div>
              )
            }


            {/* CLOSED */}

            {
              currentIncident.status
              === "CLOSED"
              && (
                <div className="space-y-3">

                  <Button
                    variant="outline"
                    disabled={isUpdatingStatus}
                    onClick={() =>
                      handleStatusChange(
                        "IN_PROGRESS",
                      )
                    }
                  >
                    {
                      isUpdatingStatus
                        ? "Reopening..."
                        : "Reopen investigation"
                    }
                  </Button>


                  <p className="text-sm text-muted-foreground">
                    Closed incidents must be
                    explicitly reopened before
                    investigation work continues.
                  </p>

                </div>
              )
            }


            {/* Backend lifecycle error */}

            {statusError && (
              <p
                role="alert"
                className="text-sm text-destructive"
              >
                {statusError}
              </p>
            )}

          </CardContent>
        </Card>
      )}


      {/* Investigation Notes */}

      <InvestigationNotes
        incidentId={currentIncident.id}
      />


      {/* Incident Timeline */}

      <IncidentActivityTimeline
        incidentId={currentIncident.id}
      />

    </div>
  );
}