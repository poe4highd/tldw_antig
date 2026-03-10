import type { Metadata } from 'next';
import ResultClient from './ResultClient';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

async function getResultMeta(id: string) {
    try {
        const res = await fetch(`${API_BASE}/result/${id}`, {
            next: { revalidate: 3600 },
        });
        if (!res.ok) return null;
        return await res.json();
    } catch {
        return null;
    }
}

export async function generateMetadata(
    { params }: { params: Promise<{ id: string }> }
): Promise<Metadata> {
    const { id } = await params;
    const data = await getResultMeta(id);

    const title = data?.title
        ? `${data.title} | Read-Tube`
        : 'AI Video Transcript | Read-Tube';

    const description = data?.summary
        ? data.summary.replace(/\[\d{2}:\d{2}(?::\d{2})?\]/g, '').replace(/^\d+\.\s*/gm, '').replace(/\n+/g, ' ').trim().slice(0, 155)
        : 'AI-generated transcript and summary. Read transcripts, understand videos faster with Read-Tube.';

    const image = data?.thumbnail
        ? (data.thumbnail.startsWith('http') ? data.thumbnail : `${API_BASE}/media/${data.thumbnail}`)
        : '/og-default.png';

    return {
        title,
        description,
        keywords: data?.keywords?.join(', '),
        openGraph: {
            title: data?.title || 'Video Transcript',
            description,
            images: [{ url: image, width: 1280, height: 720, alt: data?.title || 'Video Transcript' }],
            type: 'article',
            siteName: 'Read-Tube',
        },
        twitter: {
            card: 'summary_large_image',
            title: data?.title || 'Video Transcript',
            description,
            images: [image],
        },
    };
}

export default async function ResultPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    return <ResultClient id={id} />;
}
