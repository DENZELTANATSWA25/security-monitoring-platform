"use client";

import { FormEvent, useState } from "react";

import { useCurrentUser } from "@/hooks/use-users";
import {
  useCreateIncidentNote,
  useIncidentNotes,
} from "@/hooks/use-incident-notes";
import { canManageIncidents } from "@/lib/permissions";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";


interface InvestigationNotesProps {
  incidentId: number;
}


export default function InvestigationNotes({
  incidentId,
}: InvestigationNotesProps) {
  const [content, setContent] = useState("");

  const {
    data: currentUser,
  } = useCurrentUser();

  const {
    data: notes = [],
    isLoading,
    error,
  } = useIncidentNotes(incidentId);

  const createNote =
    useCreateIncidentNote(incidentId);

  const canAddNotes =
    canManageIncidents(currentUser?.role);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const trimmedContent =
      content.trim();

    if (!trimmedContent) {
      return;
    }

    await createNote.mutateAsync(
      trimmedContent
    );

    setContent("");
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Investigation Notes
        </CardTitle>

        <CardDescription>
          Analyst observations and
          investigation history for this
          incident.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {canAddNotes && (
          <form
            onSubmit={handleSubmit}
            className="space-y-3"
          >
            <textarea
              value={content}
              onChange={(event) =>
                setContent(
                  event.target.value
                )
              }
              placeholder="Add investigation findings, actions taken, evidence reviewed, or next steps..."
              rows={4}
              maxLength={10000}
              className="w-full resize-y rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />

            <div className="flex items-center justify-between gap-4">
              <p className="text-xs text-muted-foreground">
                {content.length}/10000
              </p>

              <Button
                type="submit"
                disabled={
                  !content.trim() ||
                  createNote.isPending
                }
              >
                {createNote.isPending
                  ? "Adding..."
                  : "Add Note"}
              </Button>
            </div>

            {createNote.isError && (
              <p className="text-sm text-destructive">
                Failed to add the
                investigation note.
              </p>
            )}
          </form>
        )}

        <div className="border-t" />

        {isLoading && (
          <p className="text-sm text-muted-foreground">
            Loading investigation notes...
          </p>
        )}

        {error && (
          <p className="text-sm text-destructive">
            Failed to load investigation
            notes.
          </p>
        )}

        {!isLoading &&
          !error &&
          notes.length === 0 && (
            <p className="text-sm text-muted-foreground">
              No investigation notes have
              been added yet.
            </p>
          )}

        <div className="space-y-4">
          {notes.map((note) => (
            <div
              key={note.id}
              className="rounded-lg border p-4"
            >
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm font-medium">
                  {note.author ? (
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">
                            {note.author.full_name}
                        </span>

                        <span className="text-xs text-muted-foreground">
                            {note.author.role}
                        </span>
                    </div>
                  ) : (
                    <span className="text-sm font-medium">
                        Former User
                    </span>
                  )}
                </span>

                <time className="text-xs text-muted-foreground">
                  {new Date(
                    note.created_at
                  ).toLocaleString()}
                </time>
              </div>

              <p className="whitespace-pre-wrap text-sm leading-6">
                {note.content}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}