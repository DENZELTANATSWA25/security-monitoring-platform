/**
 * Authentication bypass is permitted only during local development.
 *
 * Production builds must always enforce authentication, even if
 * NEXT_PUBLIC_DEV_AUTH_BYPASS is accidentally configured as true.
 */
export const DEV_AUTH_BYPASS =
    process.env.NODE_ENV === "development" &&
    process.env.NEXT_PUBLIC_DEV_AUTH_BYPASS === "true";