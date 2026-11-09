import { apiClient } from './apiClient';
import { CONFIG } from '@/config';

export type StreamPlatform = 'youtube' | 'tiktok';

export function detectPlatform(url: string): StreamPlatform {
    const trimmed = url.trim().toLowerCase();
    if (trimmed.includes('tiktok.com') || trimmed.startsWith('@') || trimmed.startsWith('tiktok-')) {
        return 'tiktok';
    }
    return 'youtube';
}

export function extractStreamId(url: string): { streamId: string | null; platform: StreamPlatform } {
    const trimmed = url.trim();
    const platform = detectPlatform(trimmed);

    if (platform === 'tiktok') {
        let username = trimmed.replace(/^@/, '');
        if (username.includes('tiktok.com')) {
            const parts = username.split('/');
            for (const p of parts) {
                if (p.startsWith('@')) {
                    username = p.replace(/^@/, '').replace(/\/$/, '').split('?')[0];
                    break;
                }
            }
        }
        username = username.replace(/\/$/, '').split('?')[0];
        return {
            streamId: username ? `tiktok-${username}` : null,
            platform: 'tiktok',
        };
    }

    // YouTube
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = trimmed.match(regExp);
    const videoId = match && match[7].length === 11 ? match[7] : null;
    return {
        streamId: videoId,
        platform: 'youtube',
    };
}

export const streamService = {
    startTracking: async (url: string, platform?: StreamPlatform) => {
        const resolvedPlatform = platform || detectPlatform(url);
        const endpoint = resolvedPlatform === 'tiktok' ? '/tiktok/live-chat' : '/youtube/live-chat';
        const response = await apiClient.post(endpoint, { url });
        return response.data;
    },

    stopTracking: async (url: string, action: string = 'stop', platform?: StreamPlatform) => {
        const resolvedPlatform = platform || detectPlatform(url);
        const endpoint = resolvedPlatform === 'tiktok' ? '/tiktok/stop-crawler' : '/youtube/stop-crawler';
        const response = await apiClient.post(endpoint, { url, action });
        return response.data;
    },

    sseStreamEvents: (streamId: string, platform?: StreamPlatform) => {
        const resolvedPlatform = platform || (streamId.startsWith('tiktok-') ? 'tiktok' : 'youtube');
        const endpoint = resolvedPlatform === 'tiktok' ? '/api/tiktok' : '/api/youtube';
        return new EventSource(`${CONFIG.API_URL}${endpoint}/events/${streamId}`);
    },
};

// Backward-compatible alias
export const youtubeService = streamService;
