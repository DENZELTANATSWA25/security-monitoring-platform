import axios from "axios";

import { getAccessToken } from "@/lib/auth";

export const api = axios.create({
    baseURL: "http://localhost:8000/api/v1",
    headers: {
        "Content-Type": "application/json",
    },
});

api.interceptors.request.use((config) => {
    const token = getAccessToken();
    if (token) {
        config.headers.Authorization =
            `Bearer ${token}`;
    }

    return config;
});