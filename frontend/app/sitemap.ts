import type { MetadataRoute } from 'next';

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://read-tube.vercel.app';
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://api.read-tube.com';

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
        // 轻量接口：只返回 [{ id, date }]，不读取 report_data 大字段
        const res = await fetch(`${API_BASE}/sitemap-ids`, {
            next: { revalidate: 3600 },
        });
        if (res.ok) {
            const items: { id: string; date?: string }[] = await res.json();
            resultPages = items.map((item) => ({
                url: `${SITE_URL}/result/${item.id}`,
                lastModified: item.date ? new Date(item.date) : new Date(),
                changeFrequency: 'yearly' as const,
                priority: 0.8,
            }));
        } else {
            console.error(`[sitemap] /sitemap-ids returned ${res.status}`);
        }
    } catch (error) {
        // API 不可用时退化为仅静态页
        console.error('[sitemap] Failed to fetch result pages:', error);
    }

    return [...staticPages, ...resultPages];
}
