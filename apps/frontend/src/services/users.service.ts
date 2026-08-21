import { api } from "./api";

import { User } from "@/types/user";

export async function getUsers() {
    const response = await api.get<User[]>(
        "/users"
    );

    return response.data;
}

export async function getCurrentUser() {
    const response = await api.get<User>(
        "/users/me"
    );

    return response.data;
}