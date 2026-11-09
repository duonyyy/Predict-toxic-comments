'use client';

import React, { useState, useEffect } from 'react';
import { Play, Square, Youtube, Sparkles, X } from 'lucide-react';

export const TikTokIcon = ({ className = 'h-5 w-5' }: { className?: string }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64c.298-.002.595.042.88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1.04-.1z" />
    </svg>
);

interface CrawlControlProps {
    url: string;
    setUrl: (url: string) => void;
    isTracking: boolean;
    onStart: () => void;
    onStop: () => void;
    variant?: 'hero' | 'topbar';
    isLoading?: boolean;
}

export const CrawlControl: React.FC<CrawlControlProps> = ({
    url,
    setUrl,
    isTracking,
    onStart,
    onStop,
    variant = 'hero',
    isLoading = false,
}) => {
    const isHero = variant === 'hero';
    const [activeTab, setActiveTab] = useState<'youtube' | 'tiktok'>('youtube');

    // Auto-detect platform from URL input
    useEffect(() => {
        const trimmed = url.trim().toLowerCase();
        if (trimmed.includes('tiktok.com') || trimmed.startsWith('@')) {
            setActiveTab('tiktok');
        } else if (trimmed.includes('youtube.com') || trimmed.includes('youtu.be')) {
            setActiveTab('youtube');
        }
    }, [url]);

    const handlePasteSample = (platform: 'youtube' | 'tiktok') => {
        setActiveTab(platform);
        if (platform === 'youtube') {
            setUrl('https://www.youtube.com/watch?v=5qap5aO4i9A');
        } else {
            setUrl('https://www.tiktok.com/@annie_tran.27/live');
        }
    };

    return (
        <div className={`flex flex-col gap-3 ${isHero ? 'w-full' : 'w-full'}`}>
            {/* Platform Selector Tabs in Hero mode */}
            {isHero && !isTracking && (
                <div className="flex items-center justify-center gap-2 mb-1">
                    <button
                        type="button"
                        onClick={() => {
                            setActiveTab('youtube');
                            if (url.includes('tiktok.com') || url.startsWith('@')) setUrl('');
                        }}
                        className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                            activeTab === 'youtube'
                                ? 'bg-red-600/20 text-red-400 border border-red-500/40 shadow-lg shadow-red-500/10'
                                : 'bg-[#12141e]/60 text-gray-400 border border-gray-800 hover:text-white'
                        }`}
                    >
                        <Youtube className="h-4 w-4 text-red-500" />
                        <span>YouTube Live</span>
                    </button>

                    <button
                        type="button"
                        onClick={() => {
                            setActiveTab('tiktok');
                            if (url.includes('youtube.com') || url.includes('youtu.be')) setUrl('');
                        }}
                        className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                            activeTab === 'tiktok'
                                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 shadow-lg shadow-cyan-500/10'
                                : 'bg-[#12141e]/60 text-gray-400 border border-gray-800 hover:text-white'
                        }`}
                    >
                        <TikTokIcon className="h-4 w-4 text-cyan-400" />
                        <span>TikTok Live</span>
                    </button>
                </div>
            )}

            <div className={`flex flex-col gap-3 sm:flex-row sm:items-center ${isHero ? 'w-full' : 'w-full'}`}>
                <div className="group relative flex-grow">
                    {!isTracking && isHero && (
                        <div
                            className={`absolute -inset-0.5 rounded-2xl bg-gradient-to-r opacity-30 blur-md transition duration-500 group-hover:opacity-60 ${
                                activeTab === 'tiktok'
                                    ? 'from-cyan-500 via-rose-500 to-indigo-600'
                                    : 'from-red-600 via-rose-500 to-indigo-600'
                            }`}
                        />
                    )}
                    <div className="relative flex items-center">
                        <div className="pointer-events-none absolute left-4 flex items-center justify-center">
                            {activeTab === 'tiktok' ? (
                                <TikTokIcon className={isHero ? 'h-6 w-6 text-cyan-400' : 'h-4 w-4 text-cyan-400'} />
                            ) : (
                                <Youtube className={isHero ? 'h-6 w-6 text-red-500' : 'h-4 w-4 text-red-500'} />
                            )}
                        </div>
                        <input
                            type="text"
                            placeholder={
                                activeTab === 'tiktok'
                                    ? 'Dán link TikTok Live hoặc @username (ví dụ: https://www.tiktok.com/@annie_tran.27/live)'
                                    : 'Dán link YouTube Live (ví dụ: https://www.youtube.com/watch?v=...)'
                            }
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            disabled={isTracking || isLoading}
                            className={`relative flex w-full rounded-2xl border transition-all text-white placeholder-gray-500 focus:outline-none ${
                                isHero
                                    ? `h-14 border-gray-700/60 bg-[#12141d]/90 pl-13 pr-10 text-base shadow-xl ${
                                          activeTab === 'tiktok'
                                              ? 'focus:border-cyan-400 focus:ring-4 focus:ring-cyan-500/20'
                                              : 'focus:border-red-500 focus:ring-4 focus:ring-red-500/20'
                                      }`
                                    : `h-10 border-gray-800 bg-[#151722]/80 pl-10 pr-8 text-sm ${
                                          activeTab === 'tiktok'
                                              ? 'focus:border-cyan-400 focus:ring-2 focus:ring-cyan-500/20'
                                              : 'focus:border-red-500 focus:ring-2 focus:ring-red-500/20'
                                      }`
                            } ${isTracking ? 'cursor-not-allowed opacity-75' : ''}`}
                        />
                        {url && !isTracking && !isLoading && (
                            <button
                                type="button"
                                onClick={() => setUrl('')}
                                className="absolute right-3.5 text-gray-400 hover:text-white transition-colors"
                                title="Xóa URL"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        )}
                    </div>
                </div>

                <button
                    onClick={isTracking ? onStop : onStart}
                    disabled={(!url.trim() && !isTracking) || isLoading}
                    className={`group relative overflow-hidden rounded-2xl font-bold text-white transition-all duration-300 disabled:cursor-not-allowed disabled:grayscale disabled:opacity-40 sm:w-auto cursor-pointer shadow-lg active:scale-98 ${
                        isTracking
                            ? 'bg-gradient-to-r from-gray-800 to-gray-900 border border-gray-700 hover:from-red-950 hover:to-red-900 shadow-gray-900/40'
                            : activeTab === 'tiktok'
                            ? 'bg-gradient-to-r from-cyan-600 via-teal-600 to-rose-600 hover:from-cyan-500 hover:to-rose-500 shadow-cyan-600/30'
                            : 'bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 shadow-red-600/30'
                    } ${isHero ? 'h-14 px-8 text-base w-full' : 'h-10 px-5 text-sm shrink-0'}`}
                >
                    <span className="relative z-10 flex items-center justify-center gap-2">
                        {isLoading ? (
                            <>
                                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white" />
                                <span>{isTracking ? 'Đang dừng...' : 'Đang kết nối...'}</span>
                            </>
                        ) : isTracking ? (
                            <>
                                <Square size={isHero ? 18 : 15} fill="currentColor" className="text-red-400" />
                                <span>Dừng theo dõi</span>
                            </>
                        ) : (
                            <>
                                <Play size={isHero ? 18 : 15} fill="currentColor" />
                                <span>Bắt đầu phân tích</span>
                            </>
                        )}
                    </span>
                </button>
            </div>

            {isHero && !isTracking && (
                <div className="flex flex-wrap items-center justify-center gap-3 text-xs text-gray-400 pt-1">
                    <span>Thử nhanh link mẫu:</span>
                    <button
                        type="button"
                        onClick={() => handlePasteSample('youtube')}
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-red-950/40 border border-red-800/40 text-red-300 hover:text-white hover:bg-red-900/50 cursor-pointer transition-all"
                    >
                        <Youtube className="h-3.5 w-3.5 text-red-400" />
                        <span>Mẫu YouTube Live</span>
                    </button>
                    <button
                        type="button"
                        onClick={() => handlePasteSample('tiktok')}
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-cyan-950/40 border border-cyan-800/40 text-cyan-300 hover:text-white hover:bg-cyan-900/50 cursor-pointer transition-all"
                    >
                        <TikTokIcon className="h-3.5 w-3.5 text-cyan-400" />
                        <span>Mẫu TikTok Live (@annie_tran.27)</span>
                    </button>
                </div>
            )}
        </div>
    );
};
