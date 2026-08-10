"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

export function useLiveEvents() {
    const queryClient = useQueryClient();

    useEffect(() => {
        const socket = new WebSocket("ws://localhost:8000/ws/events")

        socket.onopen = () => {
            console.log("Connected to WebSocket server");

            socket.send("connected");
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === "security_event") {
                console.log("New Event:", data);

                queryClient.invalidateQueries({
                    queryKey: ["events"],
            });

            queryClient.invalidateQueries({
                queryKey: ["dashboard-summary"],
            });
            }
        };

        socket.onclose = () => {
            console.log("WebSocket disconnected");
        };

        socket.onerror = (error) => {
            console.error(error);
        };

        return () => {
            socket.close();
        };
    }, [queryClient]);
}