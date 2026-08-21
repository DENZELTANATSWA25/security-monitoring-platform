import { api } from "./api";

import {
    LoginRequest,
    TokenResponse,
} from "@/types/auth";

import {
    setAccessToken,
    removeAccessToken,
} from "@/lib/auth";


export async function login(
    credentials: LoginRequest
) {
    const response = await api.post<TokenResponse>(
        "/auth/login",
        credentials
    );

    setAccessToken(
        response.data.access_token
    );

    return response.data;
}


export function logout() {
    removeAccessToken();
}