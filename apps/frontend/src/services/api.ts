import axios from "axios";

import {
    getAccessToken,
    removeAccessToken,
} from "@/lib/auth";

const API_URL =
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000/api/v1";

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

/**
 * REQUEST INTERCEPTOR
 *
 * Attaches the JWT access token to authenticated API requests.
 */
api.interceptors.request.use((config) => {
    const token = getAccessToken();

    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
});

/**
 * RESPONSE INTERCEPTOR
 *
 * Removes the current token if the backend rejects it with 401.
 * Prevents an old request from invalidating a newer session.
 */
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const requestToken =
            error.config?.headers?.Authorization;

        const currentToken = getAccessToken();

        if (
            error.response?.status === 401 &&
            currentToken &&
            requestToken === `Bearer ${currentToken}`
        ) {
            removeAccessToken();
        }

        return Promise.reject(error);
    }
);