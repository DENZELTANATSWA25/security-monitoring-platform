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

api.interceptors.request.use((config) => {
    const token = getAccessToken();

    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (
            error.response?.status === 401 &&
            getAccessToken()
        ) {
            removeAccessToken();
        }

        return Promise.reject(error);
    }
);