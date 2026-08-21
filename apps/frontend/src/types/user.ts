export type UserRole = 
    | "admin"
    | "analyst"
    | "viewer";

export interface User {
    id: number;

    email: string;
    username: string;
    full_name: string;

    role: UserRole;

    is_active: boolean;
    is_verified: boolean;
    last_login: string | null;

    created_at: string;
    updated_at: string;
}