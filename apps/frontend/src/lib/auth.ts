const TOKEN_KEY = "access_token";

const AUTH_EVENT = "auth-token-changed";


export function getAccessToken(): string | null {
    if (typeof window === "undefined") {
        return null;
    }

    return localStorage.getItem(TOKEN_KEY);
}


export function setAccessToken(
    token: string
): void {
    localStorage.setItem(
        TOKEN_KEY,
        token
    );

    window.dispatchEvent(
        new Event(AUTH_EVENT)
    );
}


export function removeAccessToken(): void {
    localStorage.removeItem(
        TOKEN_KEY
    );

    window.dispatchEvent(
        new Event(AUTH_EVENT)
    );
}


export function subscribeToAuth(
    callback: () => void
) {
    window.addEventListener(
        AUTH_EVENT,
        callback
    );

    window.addEventListener(
        "storage",
        callback
    );

    return () => {
        window.removeEventListener(
            AUTH_EVENT,
            callback
        );

        window.removeEventListener(
            "storage",
            callback
        );
    };
}


export function getAuthSnapshot(): boolean {
    return Boolean(
        localStorage.getItem(TOKEN_KEY)
    );
}


export function getServerAuthSnapshot(): boolean {
    return false;
}