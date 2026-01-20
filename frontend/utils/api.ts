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
    // Priority: 1. Current Origin (window.location.origin)
    //           2. Environment Variable (NEXT_PUBLIC_SITE_URL)
    //           3. Default fallback (http://localhost:3000)

    let url = typeof window !== "undefined"
        ? window.location.origin
        : (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000");

    // Remove trailing slash to ensure consistency with Supabase white-list
    url = url.replace(/\/$/, "");

    return url;
};
