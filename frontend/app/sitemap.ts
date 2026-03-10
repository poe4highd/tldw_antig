import type { MetadataRoute } from 'next';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://read-tube.vercel.app';
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
    const staticPages: MetadataRoute.Sitemap = [
        {
            url: `${SITE_URL}/`,
            lastModified: new Date(),
            changeFrequency: 'weekly',
            priority: 1.0,
        },
        {
            url: `${SITE_URL}/login`,
            lastModified: new Date(),
            changeFrequency: 'monthly',
            priority: 0.3,
        },
    ];

    let resultPages: MetadataRoute.Sitemap = [];
    try {
        const res = await fetch(`${API_BASE}/explore?limit=1000`, {
            next: { revalidate: 3600 },
        });
        if (res.ok) {
            const items = await res.json();
            resultPages = items.map((item: { id: string; date?: string }) => ({
                url: `${SITE_URL}/result/${item.id}`,
                lastModified: item.date ? new Date(item.date) : new Date(),
                changeFrequency: 'yearly' as const,
                priority: 0.8,
            }));
        }
    } catch {
        // Silently fall back to static pages only if API is unavailable
    }

    return [...staticPages, ...resultPages];
}
