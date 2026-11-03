'use client';

import React from 'react';
import { Trophy, ShieldAlert, AlertCircle, Ban, Flame, Award } from 'lucide-react';
import { LeaderboardUser } from '@/hooks/useLiveStream';

interface ToxicLeaderboardProps {
    data: LeaderboardUser[];
}

export const ToxicLeaderboard: React.FC<ToxicLeaderboardProps> = ({ data }) => {
    const maxToxicCount = data && data.length > 0 ? Math.max(...data.map((u) => u.toxic_count || 1)) : 1;

    const getRankBadge = (index: number) => {
        if (index === 0) {
            return (
                <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-gradient-to-tr from-amber-600 to-yellow-400 text-black font-black text-xs shadow-md shadow-amber-500/30">
                    🥇
                </span>
            );
        }
        if (index === 1) {
            return (
                <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-gradient-to-tr from-slate-400 to-gray-200 text-black font-black text-xs shadow-md shadow-gray-400/20">
                    🥈
                </span>
            );
        }
        if (index === 2) {
            return (
                <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-gradient-to-tr from-amber-800 to-orange-400 text-white font-black text-xs shadow-md shadow-orange-700/20">
                    🥉
                </span>
            );
        }
        return (
            <span className="flex h-7 w-7 items-center justify-center rounded-xl bg-[#1a1d2e] border border-gray-800 text-gray-400 font-bold text-xs">
                #{index + 1}
            </span>
        );
    };

    return (
        <div className="flex h-full w-full flex-col rounded-3xl border border-gray-800/80 bg-[#10121a]/90 backdrop-blur-xl p-6 shadow-2xl">
            {/* Header */}
            <div className="mb-5 flex items-center justify-between border-b border-gray-800/60 pb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
                        <Trophy className="h-5 w-5" />
                    </div>
                    <div>
                        <h3 className="text-lg font-black tracking-tight text-white">Bảng Xếp Hạng Vi Phạm</h3>
                        <p className="text-xs text-gray-400">Top người dùng gửi nhiều bình luận tiêu cực</p>
                    </div>
                </div>

                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-950/40 border border-red-800/40 text-[11px] font-bold text-red-400">
                    <Flame className="h-3.5 w-3.5" />
                    <span>Top 5</span>
                </div>
            </div>

            {/* List */}
            <div className="flex-grow space-y-3 overflow-y-auto custom-scrollbar pr-1">
                {!data || data.length === 0 ? (
                    <div className="flex h-48 flex-col items-center justify-center text-gray-500 gap-3">
                        <div className="p-3 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                            <ShieldAlert className="h-6 w-6" />
                        </div>
                        <div className="text-center">
                            <p className="text-sm font-semibold text-gray-300">Chưa ghi nhận đối tượng vi phạm</p>
                            <p className="text-xs text-gray-500 mt-0.5">Không khí phòng chat đang rất tích cực!</p>
                        </div>
                    </div>
                ) : (
                    data.map((user, index) => {
                        const percent = Math.min(Math.round(((user.toxic_count || 0) / maxToxicCount) * 100), 100);

                        return (
                            <div
                                key={user.author_id || index}
                                className="group relative rounded-2xl border border-gray-800/70 bg-[#141724]/60 p-3.5 transition-all duration-200 hover:border-red-500/30 hover:bg-[#181c2d]"
                            >
                                <div className="flex items-center justify-between gap-3">
                                    {/* Rank + Avatar + Name */}
                                    <div className="flex items-center gap-3 min-w-0 flex-grow">
                                        {getRankBadge(index)}

                                        {/* Avatar */}
                                        <div className="relative h-9 w-9 shrink-0 rounded-full overflow-hidden bg-gray-800 ring-2 ring-gray-700 group-hover:ring-red-500/40 transition-all flex items-center justify-center text-xs font-bold text-gray-300">
                                            {user.author_image ? (
                                                <img
                                                    src={user.author_image}
                                                    alt={user.author_name}
                                                    className="h-full w-full object-cover"
                                                    onError={(e) => {
                                                        e.currentTarget.style.display = 'none';
                                                    }}
                                                />
                                            ) : (
                                                <span>{(user.author_name || 'U').slice(0, 2).toUpperCase()}</span>
                                            )}
                                        </div>

                                        {/* Name */}
                                        <div className="min-w-0 flex-grow">
                                            <p className="text-sm font-bold text-gray-200 truncate group-hover:text-white transition-colors">
                                                {user.author_name || 'Người dùng ẩn danh'}
                                            </p>
                                            <p className="text-[11px] text-gray-500 font-mono truncate">
                                                ID: {user.author_id ? user.author_id.slice(0, 12) : '...'}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Count & Progress */}
                                    <div className="flex flex-col items-end gap-1 shrink-0">
                                        <div className="flex items-center gap-1">
                                            <span className="text-sm font-black text-red-400">
                                                {user.toxic_count}
                                            </span>
                                            <span className="text-[10px] text-gray-400 font-medium">lần</span>
                                        </div>

                                        {/* Progress Bar */}
                                        <div className="h-1.5 w-18 overflow-hidden rounded-full bg-gray-800">
                                            <div
                                                className="h-full rounded-full bg-gradient-to-r from-orange-500 to-red-500 transition-all duration-500"
                                                style={{ width: `${percent}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
};
