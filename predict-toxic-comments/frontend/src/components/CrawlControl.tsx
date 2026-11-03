'use client';

import React from 'react';
import { Play, Square, Youtube, Sparkles, X } from 'lucide-react';

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

    const handlePasteSample = () => {
        setUrl('https://www.youtube.com/watch?v=5qap5aO4i9A'); // Popular Lo-Fi Live Stream URL as example
    };

    return (
        <div className={`flex flex-col gap-3 ${isHero ? 'w-full' : 'w-full'}`}>
            <div className={`flex flex-col gap-3 sm:flex-row sm:items-center ${isHero ? 'w-full' : 'w-full'}`}>
                <div className="group relative flex-grow">
                    {!isTracking && isHero && (
                        <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-red-600 via-rose-500 to-indigo-600 opacity-30 blur-md transition duration-500 group-hover:opacity-60"></div>
                    )}
                    <div className="relative flex items-center">
                        <div className="pointer-events-none absolute left-4 text-red-500 flex items-center justify-center">
                            <Youtube className={isHero ? "h-6 w-6" : "h-4 w-4"} />
                        </div>
                        <input
                            type="text"
                            placeholder="Dán link YouTube Live tại đây (ví dụ: https://www.youtube.com/watch?v=...)"
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            disabled={isTracking || isLoading}
                            className={`relative flex w-full rounded-2xl border transition-all text-white placeholder-gray-500 focus:outline-none ${
                                isHero
                                    ? 'h-14 border-gray-700/60 bg-[#12141d]/90 pl-13 pr-10 text-base shadow-xl focus:border-red-500 focus:ring-4 focus:ring-red-500/20'
                                    : 'h-10 border-gray-800 bg-[#151722]/80 pl-10 pr-8 text-sm focus:border-red-500 focus:ring-2 focus:ring-red-500/20'
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
                            : 'bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 shadow-red-600/30 hover:shadow-red-500/40'
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
                <div className="flex items-center justify-center gap-2 text-xs text-gray-400">
                    <span>Chưa có link live?</span>
                    <button
                        type="button"
                        onClick={handlePasteSample}
                        className="inline-flex items-center gap-1 text-red-400 hover:text-red-300 underline underline-offset-2 font-medium cursor-pointer transition-colors"
                    >
                        <Sparkles className="h-3.5 w-3.5" />
                        Dùng thử URL stream mẫu
                    </button>
                </div>
            )}
        </div>
    );
};
