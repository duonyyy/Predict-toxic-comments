'use client';

import React, { useState, useMemo } from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts';
import { MetricData } from '@/hooks/useLiveStream';
import { TrendingUp, Activity, Flame, Sparkles } from 'lucide-react';

interface ToxicityChartProps {
    data: MetricData[];
}

export const ToxicityChart: React.FC<ToxicityChartProps> = ({ data }) => {
    const [viewMode, setViewMode] = useState<'all' | 'toxic' | 'expression' | 'ratio'>('all');

    // Calculate aggregated summary for header stats
    const stats = useMemo(() => {
        if (!data || data.length === 0) {
            return { total: 0, toxic: 0, explicit: 0, implicit: 0, maxRatio: 0, currentRatio: 0 };
        }
        let total = 0;
        let toxic = 0;
        let explicit = 0;
        let implicit = 0;
        let maxRatio = 0;
        data.forEach((d) => {
            total += d.total_comments || 0;
            toxic += d.toxic_count || 0;
            explicit += d.explicit_count || 0;
            implicit += d.implicit_count || 0;
            const r = d.total_comments > 0 ? (d.toxic_count / d.total_comments) * 100 : 0;
            if (r > maxRatio) maxRatio = r;
        });
        const last = data[data.length - 1];
        const currentRatio =
            last && last.total_comments > 0
                ? Math.round((last.toxic_count / last.total_comments) * 100)
                : 0;

        return { total, toxic, explicit, implicit, maxRatio: Math.round(maxRatio), currentRatio };
    }, [data]);

    // Format chart data with toxic ratio percentage
    const chartData = useMemo(() => {
        return data.map((d) => {
            const ratio = d.total_comments > 0 ? Math.round((d.toxic_count / d.total_comments) * 100) : 0;
            return {
                ...d,
                toxic_ratio_percent: ratio,
            };
        });
    }, [data]);

    return (
        <div className="flex h-full w-full flex-col rounded-3xl border border-gray-800/80 bg-[#10121a]/90 backdrop-blur-xl p-6 shadow-2xl">
            {/* Chart Header */}
            <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-gray-800/60 pb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                        <TrendingUp className="h-5 w-5" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className="text-lg font-black tracking-tight text-white">Xu hướng Độc hại Theo Thời Gian</h3>
                            <span className="flex items-center gap-1 rounded-full bg-red-500/10 border border-red-500/20 px-2 py-0.5 text-[10px] font-bold text-red-400">
                                <span className="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse"></span>
                                DS108 REALTIME
                            </span>
                        </div>
                        <p className="text-xs text-gray-400">Phân tích tần suất phát ngôn và biểu đạt (Tầng 1 & Tầng 2) theo từng phút</p>
                    </div>
                </div>

                {/* Stat pills and View mode toggle */}
                <div className="flex flex-wrap items-center gap-3">
                    {/* Stat Badges */}
                    <div className="flex items-center gap-2 text-xs">
                        <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-red-950/40 border border-red-800/40 text-red-300">
                            <Flame className="h-3.5 w-3.5 text-red-400" />
                            <span>Cao điểm: <strong>{stats.maxRatio}%</strong></span>
                        </div>
                        <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-purple-950/40 border border-purple-800/40 text-purple-300">
                            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
                            <span>Ẩn ý: <strong>{stats.implicit}</strong></span>
                        </div>
                    </div>

                    {/* View mode toggle */}
                    <div className="inline-flex rounded-xl bg-[#161925] p-1 border border-gray-800 text-xs">
                        <button
                            onClick={() => setViewMode('all')}
                            className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                                viewMode === 'all' ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            Tất cả
                        </button>
                        <button
                            onClick={() => setViewMode('toxic')}
                            className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                                viewMode === 'toxic' ? 'bg-red-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            Độc hại
                        </button>
                        <button
                            onClick={() => setViewMode('expression')}
                            className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                                viewMode === 'expression' ? 'bg-purple-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            Biểu đạt (Tầng 2)
                        </button>
                        <button
                            onClick={() => setViewMode('ratio')}
                            className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                                viewMode === 'ratio' ? 'bg-amber-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            Tỉ lệ %
                        </button>
                    </div>
                </div>
            </div>

            {/* Chart Canvas */}
            <div className="h-[250px] w-full min-h-[220px]">
                {chartData.length === 0 ? (
                    <div className="flex h-full w-full flex-col items-center justify-center text-gray-500 gap-2">
                        <Activity className="h-8 w-8 text-gray-600 animate-pulse" />
                        <p className="text-sm font-medium">Đang tích lũy dữ liệu thống kê biểu đồ...</p>
                        <p className="text-xs text-gray-600">Dữ liệu sẽ tự động vẽ sau đợt bình luận đầu tiên</p>
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorTotalComments" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorToxicCount" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.5} />
                                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorExplicitCount" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.5} />
                                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorImplicitCount" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.5} />
                                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorRatio" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                                </linearGradient>
                            </defs>

                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.06)" />

                            <XAxis
                                dataKey="window_start"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fontSize: 11, fill: '#64748b' }}
                                dy={10}
                                tickFormatter={(time) => {
                                    try {
                                        return new Date(time).toLocaleTimeString([], {
                                            hour: '2-digit',
                                            minute: '2-digit',
                                        });
                                    } catch {
                                        return '';
                                    }
                                }}
                            />

                            <YAxis
                                axisLine={false}
                                tickLine={false}
                                tick={{ fontSize: 11, fill: '#64748b' }}
                                tickFormatter={(val) => `${val}${viewMode === 'ratio' ? '%' : ''}`}
                            />

                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'rgba(15, 18, 27, 0.95)',
                                    borderColor: 'rgba(255, 255, 255, 0.1)',
                                    borderRadius: '16px',
                                    color: '#fff',
                                    fontSize: '12px',
                                    boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
                                    backdropFilter: 'blur(10px)',
                                }}
                                labelFormatter={(time) => `Thời gian: ${new Date(time).toLocaleTimeString()}`}
                            />

                            <Legend
                                verticalAlign="top"
                                align="right"
                                iconType="circle"
                                wrapperStyle={{ paddingBottom: '10px', fontSize: '12px' }}
                            />

                            {(viewMode === 'all' || viewMode === 'toxic') && (
                                <Area
                                    type="monotone"
                                    dataKey="toxic_count"
                                    name="Bình luận Độc hại"
                                    stroke="#ef4444"
                                    strokeWidth={2.5}
                                    fillOpacity={1}
                                    fill="url(#colorToxicCount)"
                                    isAnimationActive={true}
                                />
                            )}

                            {viewMode === 'all' && (
                                <Area
                                    type="monotone"
                                    dataKey="total_comments"
                                    name="Tổng Bình luận"
                                    stroke="#6366f1"
                                    strokeWidth={2}
                                    fillOpacity={1}
                                    fill="url(#colorTotalComments)"
                                    isAnimationActive={true}
                                />
                            )}

                            {viewMode === 'expression' && (
                                <>
                                    <Area
                                        type="monotone"
                                        dataKey="explicit_count"
                                        name="Công kích Trực tiếp (Explicit)"
                                        stroke="#f43f5e"
                                        strokeWidth={2.5}
                                        fillOpacity={1}
                                        fill="url(#colorExplicitCount)"
                                        isAnimationActive={true}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="implicit_count"
                                        name="Ẩn ý / Mỉa mai (Implicit)"
                                        stroke="#a855f7"
                                        strokeWidth={2.5}
                                        fillOpacity={1}
                                        fill="url(#colorImplicitCount)"
                                        isAnimationActive={true}
                                    />
                                </>
                            )}

                            {viewMode === 'ratio' && (
                                <Area
                                    type="monotone"
                                    dataKey="toxic_ratio_percent"
                                    name="Tỉ lệ Độc hại (%)"
                                    stroke="#f59e0b"
                                    strokeWidth={2.5}
                                    fillOpacity={1}
                                    fill="url(#colorRatio)"
                                    isAnimationActive={true}
                                />
                            )}
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>
        </div>
    );
};
