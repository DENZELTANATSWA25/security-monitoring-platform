import { api } from "./api";

import type {
    User,
    UserRole,
} from "@/types/user";


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


export async function updateUserRole(
    userId: number,
    role: UserRole
) {
    const response = await api.patch<User>(
        `/users/${userId}/role`,
        {
            role,
        }
    );

    return response.data;
}


export async function updateUserStatus(
    userId: number,
    isActive: boolean
) {
    const response = await api.patch<User>(
        `/users/${userId}/status`,
        {
            is_active: isActive,
        }
    );

    return response.data;
}


export async function updateUserVerification(
    userId: number,
    isVerified: boolean
) {
    const response = await api.patch<User>(
        `/users/${userId}/verification`,
        {
            is_verified: isVerified,
        }
    );

    return response.data;
}