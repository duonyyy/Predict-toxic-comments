'use client';

import React, { useMemo } from 'react';
import { MessageSquare, AlertTriangle, Users, Ban, EyeOff, Clock, Sparkles, Flame } from 'lucide-react';
import { Message, MetricData, LeaderboardUser } from '@/hooks/useLiveStream';

interface StatsOverviewProps {
    messages: Message[];
    metrics: MetricData[];
    leaderboard: LeaderboardUser[];
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ messages, metrics, leaderboard }) => {
    const stats = useMemo(() => {
        const total = messages.length;
        const toxicList = messages.filter((m) =>
            m.toxicity === 'TOXIC' || m.toxic_label === 'TOXIC' || m.toxic_label === 'Toxic'
        );
        const toxicCount = toxicList.length;
        const ratio = total > 0 ? Math.round((toxicCount / total) * 100) : 0;

        const explicitCount = messages.filter(
            (m) =>
                (m.toxicity === 'TOXIC' || m.toxic_label === 'TOXIC' || m.toxic_label === 'Toxic') &&
                (m.expression_type === 'EXPLICIT' || m.toxic_category === 'EXPLICIT')
        ).length;

        const implicitCount = messages.filter(
            (m) =>
                (m.toxicity === 'TOXIC' || m.toxic_label === 'TOXIC' || m.toxic_label === 'Toxic') &&
                (m.expression_type === 'IMPLICIT' || m.toxic_category === 'IMPLICIT')
        ).length;

        const banCount = messages.filter((m) => m.recommended_action === 'Ban').length;
        const hideCount = messages.filter((m) => m.recommended_action === 'Hide').length;
        const pendingCount = messages.filter((m) => m.recommended_action === 'Pending').length;
        const safeCount = messages.filter((m) => m.recommended_action === 'Safe').length;

        // Health Status determination
        let healthLabel = 'An Toàn';
        let healthColor = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
        if (ratio > 20) {
            healthLabel = 'Cực Kỳ Nguy Hiểm';
            healthColor = 'text-red-400 bg-red-500/10 border-red-500/20';
        } else if (ratio > 10) {
            healthLabel = 'Mức Cảnh Báo';
            healthColor = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
        } else if (ratio > 5) {
            healthLabel = 'Mức Trung Bình';
            healthColor = 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20';
        }

        return {
            total,
            toxicCount,
            ratio,
            explicitCount,
            implicitCount,
            banCount,
            hideCount,
            pendingCount,
            safeCount,
            violatorsCount: leaderboard.length,
            healthLabel,
            healthColor,
        };
    }, [messages, leaderboard]);

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Card 1: Tổng bình luận */}
            <div className="relative overflow-hidden rounded-3xl border border-gray-800/80 bg-[#10121a]/90 backdrop-blur-xl p-5 shadow-xl transition-all duration-300 hover:border-gray-700">
                <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Tổng Bình Luận</span>
                    <div className="p-2.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                        <MessageSquare className="h-5 w-5" />
                    </div>
                </div>
                <div className="mt-4 flex items-baseline gap-2">
                    <span className="text-3xl font-black text-white">{stats.total.toLocaleString()}</span>
                    <span className="text-xs text-gray-400 font-medium">tin nhắn</span>
                </div>
                <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-400">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span>Đang cập nhật luồng liên tục</span>
                </div>
            </div>

            {/* Card 2: Bình luận Độc hại (Tầng 1) */}
            <div className="relative overflow-hidden rounded-3xl border border-gray-800/80 bg-[#10121a]/90 backdrop-blur-xl p-5 shadow-xl transition-all duration-300 hover:border-red-500/30">
                <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Tác Vụ 1: Độc Hại</span>
                    <div className="p-2.5 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400">
                        <AlertTriangle className="h-5 w-5" />
                    </div>
                </div>
                <div className="mt-4 flex items-baseline gap-2">
                    <span className="text-3xl font-black text-red-400">{stats.ratio}%</span>
                    <span className="text-xs text-gray-400 font-medium">({stats.toxicCount} phát ngôn)</span>
                </div>
                <div className="mt-3 flex items-center">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-black uppercase border ${stats.healthColor}`}>
                        {stats.healthLabel}
                    </span>
                </div>
            </div>

            {/* Card 3: Kiểu Biểu Đạt (Tầng 2: Explicit vs Implicit) */}
            <div className="relative overflow-hidden rounded-3xl border border-gray-800/80 bg-[#10121a]/90 backdrop-blur-xl p-5 shadow-xl transition-all duration-300 hover:border-purple-500/30">
                <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Tác Vụ 2: Biểu Đạt</span>
                    <div className="p-2.5 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
                        <Sparkles className="h-5 w-5" />
                    </div>
                </div>
                <div className="mt-3 flex items-center gap-2">
                    <div className="flex-1 rounded-xl bg-red-950/40 border border-red-800/40 p-2">
                        <div className="flex items-center gap-1 text-[11px] font-bold text-red-300">
                            <Flame className="h-3 w-3 text-red-400" />
                            <span>Trực tiếp</span>
                        </div>
                        <div className="text-lg font-black text-red-200 mt-0.5">{stats.explicitCount}</div>
                    </div>
                    <div className="flex-1 rounded-xl bg-purple-950/40 border border-purple-800/40 p-2">
                        <div className="flex items-center gap-1 text-[11px] font-bold text-purple-300">
                            <Sparkles className="h-3 w-3 text-purple-400" />
                            <span>Ẩn ý / Mỉa mai</span>
                        </div>
                        <div className="text-lg font-black text-purple-200 mt-0.5">{stats.implicitCount}</div>
                    </div>
                </div>
                <div className="mt-2 text-[11px] text-gray-400 truncate">
                    Bóc tách ngữ cảnh chuyên sâu DS108
                </div>
            </div>

            {/* Card 4: Hành động đề xuất */}
            <div className="relative overflow-hidden rounded-3xl border border-gray-800/80 bg-[#10121a]/90 backdrop-blur-xl p-5 shadow-xl transition-all duration-300 hover:border-gray-700">
                <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Đề Xuất Xử Lý</span>
                    <div className="p-2.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
                        <Ban className="h-5 w-5" />
                    </div>
                </div>
                <div className="mt-3 flex items-center gap-1.5 flex-wrap">
                    <div className="flex items-center gap-1 px-2 py-1 rounded-xl bg-red-500/10 border border-red-500/20 text-xs">
                        <span className="font-black text-red-400">{stats.banCount}</span>
                        <span className="text-red-300 font-bold">Ban</span>
                    </div>
                    <div className="flex items-center gap-1 px-2 py-1 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs">
                        <span className="font-black text-amber-400">{stats.hideCount}</span>
                        <span className="text-amber-300 font-bold">Hide</span>
                    </div>
                    <div className="flex items-center gap-1 px-2 py-1 rounded-xl bg-yellow-500/10 border border-yellow-500/20 text-xs">
                        <span className="font-black text-yellow-400">{stats.pendingCount}</span>
                        <span className="text-yellow-300 font-bold">Pending</span>
                    </div>
                    <div className="flex items-center gap-1 px-2 py-1 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs">
                        <span className="font-black text-emerald-400">{stats.safeCount}</span>
                        <span className="text-emerald-300 font-bold">Safe</span>
                    </div>
                </div>
                <div className="mt-2 text-[11px] text-gray-500">
                    Phân cấp theo mức độ nguy hại & ẩn ý
                </div>
            </div>
        </div>
    );
};
