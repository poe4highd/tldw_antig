/**
 * Environment-aware API and Site configuration
 */

export const getApiBase = (): string => {
    if (typeof window === "undefined") return "http://localhost:8000";

    const hostname = window.location.hostname;

    // Production environment
    if (hostname === "read-tube.com") {
        return process.env.NEXT_PUBLIC_API_BASE || "https://api.read-tube.com";
    }

    // Vercel Preview/Branch deployments
    if (hostname.endsWith(".vercel.app")) {
        return process.env.NEXT_PUBLIC_API_BASE || "https://api.read-tube.com";
    }

    // Local development or custom tunnels
    return "http://localhost:8000";
};

export const getSiteUrl = (): string => {
    if (typeof window === "undefined") {
        return process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
    }

    // Always prioritize the current origin for redirects to maintain environment isolation
    return window.location.origin;
};
