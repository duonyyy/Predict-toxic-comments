'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { useState } from 'react';
import { useLiveStream } from '@/hooks/useLiveStream';
import { CrawlControl } from '@/components/CrawlControl';
import { ToxicityChart } from '@/components/ToxicityChart';
import { ToxicLeaderboard } from '@/components/ToxicLeaderboard';
import { MessageList } from '@/components/MessageList';
import { StatsOverview } from '@/components/StatsOverview';
import { streamService } from '@/services/streamService';
import {
    ShieldCheck,
    Zap,
    Cpu,
    Radio,
    ExternalLink,
    AlertCircle,
} from 'lucide-react';

export default function Home() {
    const [url, setUrl] = useState('');
    const [isTracking, setIsTracking] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    // Custom Hook to manage all Live logic (SSE, Metrics, Messages, Leaderboard)
    const { messages, leaderboard, metrics, crawlerStatus, videoId, platform } = useLiveStream(url, isTracking);

    const handleStart = async () => {
        setErrorMessage(null);
        const trimmed = url.trim();
        const isYT = trimmed.includes('youtube.com') || trimmed.includes('youtu.be');
        const isTT = trimmed.includes('tiktok.com') || trimmed.startsWith('@') || trimmed.length > 2;

        if (isYT || isTT) {
            setIsLoading(true);
            try {
                await streamService.startTracking(trimmed);
                setIsTracking(true);
            } catch (error: any) {
                console.error('Lỗi khi bắt đầu theo dõi:', error);
                setErrorMessage(
                    error.response?.data?.message ||
                    'Không thể kết nối đến Backend hoặc link stream không hợp lệ. Vui lòng kiểm tra lại.'
                );
            } finally {
                setIsLoading(false);
            }
        } else {
            setErrorMessage('Vui lòng nhập đường link YouTube Live hoặc TikTok Live (@username).');
        }
    };

    const handleStop = async () => {
        setIsLoading(true);
        try {
            await streamService.stopTracking(url, 'stop');
            setIsTracking(false);
        } catch (error) {
            console.error('Lỗi khi dừng theo dõi:', error);
            setIsTracking(false); // Force stop in UI even if API fails
        } finally {
            setIsLoading(false);
        }
    };

    const isTikTok = platform === 'tiktok' || (videoId && videoId.startsWith('tiktok-'));
    const cleanTikTokUser = videoId ? videoId.replace('tiktok-', '') : '';

    return (
        <div className="relative min-h-screen bg-[#07080d] text-gray-100 overflow-x-hidden selection:bg-red-500/30 selection:text-white">
            {/* Background ambient lighting */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[-10%] left-[20%] w-[500px] h-[500px] bg-red-600/10 rounded-full blur-[130px]" />
                <div className="absolute bottom-[-10%] right-[15%] w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[150px]" />
                <div className="absolute inset-0 bg-[radial-gradient(#1f2438_1px,transparent_1px)] [background-size:24px_24px] opacity-25" />
            </div>

            {/* Error Notification Banner */}
            <AnimatePresence>
                {errorMessage && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="fixed top-5 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-5 py-3 rounded-2xl bg-red-950/90 border border-red-500/40 text-red-200 shadow-2xl backdrop-blur-xl text-sm max-w-lg"
                    >
                        <AlertCircle className="h-5 w-5 text-red-400 shrink-0" />
                        <span className="flex-grow">{errorMessage}</span>
                        <button
                            onClick={() => setErrorMessage(null)}
                            className="p-1 text-red-400 hover:text-white transition-colors"
                        >
                            ✕
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence mode="wait">
                {!isTracking ? (
                    /* HERO LAYOUT */
                    <motion.div
                        key="hero"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0, scale: 0.96 }}
                        transition={{ duration: 0.4 }}
                        className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-16"
                    >
                        <main className="w-full max-w-3xl text-center space-y-10">
                            {/* Logo & Version Badge */}
                            <motion.div
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.1 }}
                                className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-red-500/10 border border-red-500/20 shadow-lg shadow-red-500/5 backdrop-blur-md"
                            >
                                <div className="h-2 w-2 rounded-full bg-red-500 animate-ping" />
                                <span className="text-xs font-black tracking-widest text-red-400 uppercase">
                                    DS108 AI Engine • YouTube & TikTok Live
                                </span>
                            </motion.div>

                            {/* Main Title */}
                            <motion.div
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.2 }}
                                className="space-y-4"
                            >
                                <h1 className="text-5xl sm:text-7xl font-black tracking-tight leading-[1.08] text-white">
                                    Kiểm Soát Phòng Chat <br />
                                    <span className="bg-gradient-to-r from-red-500 via-rose-500 to-orange-400 bg-clip-text text-transparent">
                                        Thời Gian Thực Phân Cấp
                                    </span>
                                </h1>

                                <p className="mx-auto max-w-xl text-base sm:text-lg text-gray-400 leading-relaxed font-normal">
                                    Nhận diện phát ngôn độc hại và bóc tách kiểu biểu đạt trực tiếp (Explicit) vs ẩn ý mỉa mai (Implicit)
                                    trên <strong>YouTube Live</strong> & <strong>TikTok Live</strong> chuẩn nghiên cứu DS108.
                                </p>
                            </motion.div>

                            {/* URL Input Box */}
                            <motion.div
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.3 }}
                                className="w-full max-w-2xl mx-auto"
                            >
                                <CrawlControl
                                    url={url}
                                    setUrl={setUrl}
                                    isTracking={isTracking}
                                    isLoading={isLoading}
                                    onStart={handleStart}
                                    onStop={handleStop}
                                    variant="hero"
                                />
                            </motion.div>

                            {/* Feature Highlights Grid */}
                            <motion.div
                                initial={{ y: 20, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.4 }}
                                className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 text-left"
                            >
                                <div className="p-4 rounded-2xl border border-gray-800/80 bg-[#12141e]/60 backdrop-blur-md">
                                    <div className="flex items-center gap-2.5 text-red-400 mb-1.5 font-bold text-sm">
                                        <Zap className="h-4 w-4" />
                                        <span>Đa Nền Tảng (YT + TikTok)</span>
                                    </div>
                                    <p className="text-xs text-gray-400">
                                        Hỗ trợ stream trực tiếp từ YouTube Live và TikTok Live qua Kafka, Redis và SSE.
                                    </p>
                                </div>

                                <div className="p-4 rounded-2xl border border-gray-800/80 bg-[#12141e]/60 backdrop-blur-md">
                                    <div className="flex items-center gap-2.5 text-indigo-400 mb-1.5 font-bold text-sm">
                                        <Cpu className="h-4 w-4" />
                                        <span>Phân Cấp 2 Tầng DS108</span>
                                    </div>
                                    <p className="text-xs text-gray-400">
                                        Tầng 1: TOXIC vs NON-TOXIC (PhoBERT). Tầng 2: EXPLICIT vs IMPLICIT mỉa mai (XLM-R).
                                    </p>
                                </div>

                                <div className="p-4 rounded-2xl border border-gray-800/80 bg-[#12141e]/60 backdrop-blur-md">
                                    <div className="flex items-center gap-2.5 text-emerald-400 mb-1.5 font-bold text-sm">
                                        <ShieldCheck className="h-4 w-4" />
                                        <span>Kiểm Duyệt Phân Hạng</span>
                                    </div>
                                    <p className="text-xs text-gray-400">
                                        Tự động Cấm (Ban) công kích thô tục, Gắn cờ Pending kiểm duyệt cho câu mỉa mai, ẩn ý.
                                    </p>
                                </div>
                            </motion.div>
                        </main>

                        {/* Footer */}
                        <footer className="absolute bottom-6 w-full text-center text-[11px] font-bold text-gray-600 uppercase tracking-widest">
                            Đồ Án DS108 • Hệ Thống Phân Loại Phân Cấp Phát Ngôn Độc Hại Mạng Xã Hội Tiếng Việt
                        </footer>
                    </motion.div>
                ) : (
                    /* DASHBOARD LAYOUT */
                    <motion.div
                        key="dashboard"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="relative z-10 flex flex-col min-h-screen"
                    >
                        {/* Top Navigation Bar */}
                        <header className="sticky top-0 z-50 w-full border-b border-gray-800/80 bg-[#090b12]/80 backdrop-blur-xl">
                            <div className="mx-auto flex h-16 max-w-[1700px] items-center justify-between px-4 sm:px-6 gap-4">
                                {/* Brand Logo */}
                                <div className="flex items-center gap-3 shrink-0">
                                    <div className="p-2 rounded-xl bg-gradient-to-tr from-red-600 to-rose-500 shadow-md shadow-red-500/20 text-white">
                                        <Radio className="h-4 w-4 animate-pulse" />
                                    </div>
                                    <div className="hidden md:flex flex-col">
                                        <span className="text-sm font-black tracking-tight text-white uppercase">
                                            StreamGuard AI
                                        </span>
                                        <span className="text-[10px] text-gray-400 font-medium">
                                            {isTikTok ? 'TikTok Live Monitor' : 'YouTube Live Monitor'}
                                        </span>
                                    </div>
                                </div>

                                {/* Compact Crawl Control Bar */}
                                <div className="flex-grow max-w-2xl">
                                    <CrawlControl
                                        url={url}
                                        setUrl={setUrl}
                                        isTracking={isTracking}
                                        isLoading={isLoading}
                                        onStart={handleStart}
                                        onStop={handleStop}
                                        variant="topbar"
                                    />
                                </div>

                                {/* Status Badges & External Link */}
                                <div className="flex items-center gap-2.5 shrink-0">
                                    {videoId && (
                                        <a
                                            href={
                                                isTikTok
                                                    ? `https://www.tiktok.com/@${cleanTikTokUser}/live`
                                                    : `https://www.youtube.com/watch?v=${videoId}`
                                            }
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-gray-800 bg-[#141724] text-xs font-semibold text-gray-300 hover:text-white hover:border-gray-700 transition-colors"
                                        >
                                            <span>{isTikTok ? 'Xem TikTok Live' : 'Xem YouTube Live'}</span>
                                            <ExternalLink className="h-3 w-3" />
                                        </a>
                                    )}

                                    {/* Crawler Status Indicator */}
                                    <div
                                        className={`flex h-9 items-center gap-2 rounded-full border px-3.5 text-xs font-bold transition-colors ${
                                            crawlerStatus === 'running'
                                                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                                                : crawlerStatus === 'stopped' || crawlerStatus === 'ended'
                                                ? 'border-amber-500/30 bg-amber-500/10 text-amber-400'
                                                : 'border-blue-500/30 bg-blue-500/10 text-blue-400'
                                        }`}
                                    >
                                        <div
                                            className={`h-2 w-2 rounded-full ${
                                                crawlerStatus === 'running'
                                                    ? 'bg-emerald-400 animate-pulse'
                                                    : 'bg-amber-400'
                                            }`}
                                        />
                                        <span className="uppercase text-[11px] tracking-wider">
                                            {crawlerStatus || (isTikTok ? 'TikTok Live' : 'YouTube Live')}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </header>

                        {/* Main Grid Content */}
                        <div className="mx-auto w-full max-w-[1700px] flex-grow p-4 sm:p-6 space-y-6">
                            {/* Row 1: KPI Stats Overview */}
                            <StatsOverview messages={messages} metrics={metrics} leaderboard={leaderboard} />

                            {/* Row 2: Live Activity Chart */}
                            <div className="w-full">
                                <ToxicityChart data={metrics} />
                            </div>

                            {/* Row 3: Messages Stream & Leaderboard Split */}
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                <div className="lg:col-span-2 min-h-[580px]">
                                    <MessageList messages={messages} totalMessages={messages.length} />
                                </div>

                                <div className="lg:col-span-1 min-h-[580px]">
                                    <ToxicLeaderboard data={leaderboard} />
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
