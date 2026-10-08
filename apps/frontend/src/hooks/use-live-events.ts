"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getAccessToken } from "@/lib/auth";

export function useLiveEvents() {
    const queryClient = useQueryClient();

    useEffect(() => {
        let socket: WebSocket | null = null;
        let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
        let manuallyClosed = false;

        function connect() {
            const token = getAccessToken();

            if (!token) {
                return;
            }

            const websocketUrl = new URL(
                "ws://localhost:8000/ws/events"
            );

            websocketUrl.searchParams.set(
                "token",
                token
            );

            socket = new WebSocket(
                websocketUrl.toString()
            );

            socket.onopen = () => {
                console.log(
                    "Connected to WebSocket server"
                );

                socket?.send("connected");
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === "security_event") {
                        queryClient.invalidateQueries({
                            queryKey: ["events"],
                        });

                        queryClient.invalidateQueries({
                            queryKey: ["dashboard-summary"],
                        });

                        queryClient.invalidateQueries({
                            queryKey: ["event-trend"],
                        });
                    }
                } catch {
                    console.warn(
                        "Received invalid WebSocket message"
                    );
                }
            };

            socket.onclose = (event) => {
                if (manuallyClosed) {
                    return;
                }

                if (event.code === 1008) {
                    console.warn(
                        "Websocket authentication was rejected"
                    );
                    return;
                }

                reconnectTimer = setTimeout(() => {
                    connect();
                }, 3000);
            };

            socket.onerror = () => {
                socket?.close();
            };
        }

        connect();

        return () => {
            manuallyClosed = true;

            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
            }

            socket?.close();
        };
    }, [queryClient]);
}