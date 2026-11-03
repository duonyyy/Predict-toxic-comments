'use client';

import React, { useState, useMemo, useRef, useEffect } from 'react';
import {
    MessageCircle,
    AlertTriangle,
    ShieldCheck,
    EyeOff,
    Ban,
    Clock,
    Search,
    ArrowDown,
    Copy,
    Check,
    Sparkles,
    Flame,
    HelpCircle,
} from 'lucide-react';
import { Message } from '@/hooks/useLiveStream';

interface MessageListProps {
    messages: Message[];
    totalMessages: number;
}

export const MessageList: React.FC<MessageListProps> = ({ messages, totalMessages }) => {
    const [filter, setFilter] = useState<'all' | 'toxic' | 'explicit' | 'implicit' | 'actions' | 'safe'>('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [autoScroll, setAutoScroll] = useState(true);
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to top when new messages arrive (since messages are displayed reverse chronologically)
    useEffect(() => {
        if (autoScroll && scrollRef.current) {
            scrollRef.current.scrollTop = 0;
        }
    }, [messages, autoScroll]);

    const isCommentToxic = (msg: Message) => {
        return (
            msg.toxicity === 'TOXIC' ||
            msg.toxic_label === 'TOXIC' ||
            msg.toxic_label === 'Toxic'
        );
    };

    const getExpression = (msg: Message) => {
        if (msg.expression_type) return msg.expression_type;
        if (msg.toxic_category === 'EXPLICIT' || msg.toxic_category === 'IMPLICIT') {
            return msg.toxic_category;
        }
        return null;
    };

    const filteredMessages = useMemo(() => {
        return messages.filter((msg) => {
            const toxic = isCommentToxic(msg);
            const expr = getExpression(msg);
            const hasAction =
                msg.recommended_action === 'Ban' ||
                msg.recommended_action === 'Hide' ||
                msg.recommended_action === 'Pending';

            if (filter === 'toxic' && !toxic) return false;
            if (filter === 'explicit' && (!toxic || expr !== 'EXPLICIT')) return false;
            if (filter === 'implicit' && (!toxic || expr !== 'IMPLICIT')) return false;
            if (filter === 'actions' && !hasAction) return false;
            if (filter === 'safe' && toxic) return false;

            if (searchQuery.trim()) {
                const q = searchQuery.toLowerCase();
                const matchAuthor = msg.author_name?.toLowerCase().includes(q);
                const matchMsg = msg.message?.toLowerCase().includes(q);
                if (!matchAuthor && !matchMsg) return false;
            }

            return true;
        });
    }, [messages, filter, searchQuery]);

    const handleCopy = (commentId: string, text: string) => {
        navigator.clipboard.writeText(text);
        setCopiedId(commentId);
        setTimeout(() => setCopiedId(null), 1500);
    };

    const getActionBadge = (action: string) => {
        switch (action) {
            case 'Ban':
                return (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-black bg-red-500/20 text-red-400 border border-red-500/30">
                        <Ban className="h-3 w-3" /> CẤM (BAN)
                    </span>
                );
            case 'Hide':
                return (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        <EyeOff className="h-3 w-3" /> ẨN (HIDE)
                    </span>
                );
            case 'Pending':
                return (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-yellow-500/20 text-yellow-300 border border-yellow-500/30">
                        <Clock className="h-3 w-3" /> CHỜ DUYỆT
                    </span>
                );
            default:
                return (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <ShieldCheck className="h-3 w-3" /> Hợp lệ
                    </span>
                );
        }
    };

    const getExpressionBadge = (expr: string | null | undefined) => {
        if (expr === 'EXPLICIT') {
            return (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider bg-red-950/80 text-red-200 border border-red-700/60 shadow-sm">
                    <Flame className="h-3 w-3 text-red-400" />
                    Trực tiếp (Explicit)
                </span>
            );
        }
        if (expr === 'IMPLICIT') {
            return (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider bg-purple-950/80 text-purple-200 border border-purple-700/60 shadow-sm">
                    <Sparkles className="h-3 w-3 text-purple-400" />
                    Ẩn ý / Mỉa mai (Implicit)
                </span>
            );
        }
        return null;
    };

    const toxicCount = messages.filter((m) => isCommentToxic(m)).length;
    const explicitCount = messages.filter((m) => isCommentToxic(m) && getExpression(m) === 'EXPLICIT').length;
    const implicitCount = messages.filter((m) => isCommentToxic(m) && getExpression(m) === 'IMPLICIT').length;

    return (
        <div className="flex h-full w-full flex-col rounded-3xl border border-gray-800/80 bg-[#10121a]/90 backdrop-blur-xl shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="flex flex-col gap-4 border-b border-gray-800/80 p-5 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400">
                        <MessageCircle className="h-5 w-5" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <h2 className="text-lg font-black tracking-tight text-white">Luồng Bình luận Trực tiếp</h2>
                            <span className="flex h-2 w-2 relative">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </span>
                        </div>
                        <p className="text-xs text-gray-400">Phân loại phân cấp 2 tầng theo chuẩn đề tài DS108</p>
                    </div>
                </div>

                {/* Filter and Search controls */}
                <div className="flex flex-wrap items-center gap-2">
                    {/* Search input */}
                    <div className="relative min-w-[170px] flex-grow sm:flex-grow-0">
                        <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-gray-500" />
                        <input
                            type="text"
                            placeholder="Tìm tác giả, nội dung..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="h-8 w-full rounded-xl border border-gray-800 bg-[#161925] pl-8 pr-3 text-xs text-white placeholder-gray-500 focus:border-red-500/50 focus:outline-none"
                        />
                    </div>

                    {/* Filter Tabs */}
                    <div className="inline-flex rounded-xl bg-[#161925] p-1 border border-gray-800 text-xs flex-wrap gap-1">
                        <button
                            onClick={() => setFilter('all')}
                            className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                                filter === 'all' ? 'bg-red-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            Tất cả ({totalMessages})
                        </button>
                        <button
                            onClick={() => setFilter('toxic')}
                            className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1 ${
                                filter === 'toxic' ? 'bg-red-600 text-white shadow-sm' : 'text-red-400 hover:text-red-300'
                            }`}
                        >
                            <AlertTriangle className="h-3 w-3" />
                            Độc hại ({toxicCount})
                        </button>
                        <button
                            onClick={() => setFilter('explicit')}
                            className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                                filter === 'explicit' ? 'bg-rose-700 text-white shadow-sm' : 'text-rose-400 hover:text-rose-300'
                            }`}
                        >
                            Trực tiếp ({explicitCount})
                        </button>
                        <button
                            onClick={() => setFilter('implicit')}
                            className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                                filter === 'implicit' ? 'bg-purple-700 text-white shadow-sm' : 'text-purple-400 hover:text-purple-300'
                            }`}
                        >
                            Ẩn ý ({implicitCount})
                        </button>
                        <button
                            onClick={() => setFilter('actions')}
                            className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                                filter === 'actions' ? 'bg-amber-600 text-white shadow-sm' : 'text-amber-400 hover:text-amber-300'
                            }`}
                        >
                            Cần xử lý
                        </button>
                        <button
                            onClick={() => setFilter('safe')}
                            className={`px-2.5 py-1 rounded-lg font-bold transition-all cursor-pointer ${
                                filter === 'safe' ? 'bg-emerald-600 text-white shadow-sm' : 'text-emerald-400 hover:text-emerald-300'
                            }`}
                        >
                            An toàn
                        </button>
                    </div>

                    {/* Auto-scroll toggle */}
                    <button
                        onClick={() => setAutoScroll(!autoScroll)}
                        title={autoScroll ? 'Tạm dừng tự động cuộn' : 'Bật tự động cuộn'}
                        className={`p-2 rounded-xl border text-xs font-semibold flex items-center gap-1 cursor-pointer transition-colors ${
                            autoScroll
                                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                                : 'border-gray-700 bg-gray-800 text-gray-400'
                        }`}
                    >
                        <ArrowDown className={`h-3.5 w-3.5 ${autoScroll ? 'animate-bounce' : ''}`} />
                        <span className="hidden sm:inline">{autoScroll ? 'Cuộn tự động' : 'Tạm dừng'}</span>
                    </button>
                </div>
            </div>

            {/* Content Message List */}
            <div className="flex-grow min-h-0 overflow-hidden">
                <div
                    ref={scrollRef}
                    className="h-[520px] overflow-y-auto p-4 space-y-3 custom-scrollbar"
                >
                    {filteredMessages.length === 0 ? (
                        <div className="flex h-56 flex-col items-center justify-center gap-3 text-gray-500">
                            <div className="p-4 rounded-full bg-gray-900/60 border border-gray-800">
                                <MessageCircle className="h-8 w-8 text-gray-600" />
                            </div>
                            <div className="text-center">
                                <p className="text-sm font-semibold text-gray-400">
                                    {searchQuery || filter !== 'all'
                                        ? 'Không tìm thấy bình luận phù hợp bộ lọc.'
                                        : 'Đang lắng nghe bình luận từ luồng phát trực tiếp...'}
                                </p>
                                <p className="text-xs text-gray-600 mt-1">Bình luận mới sẽ xuất hiện tức thì tại đây</p>
                            </div>
                        </div>
                    ) : (
                        // Reversed order so newest comment is on top
                        [...filteredMessages].reverse().map((msg, index) => {
                            const toxic = isCommentToxic(msg);
                            const expr = getExpression(msg);
                            const isExplicit = expr === 'EXPLICIT';
                            const isImplicit = expr === 'IMPLICIT';

                            return (
                                <div
                                    key={msg.comment_id || index}
                                    className={`group relative animate-message rounded-2xl border p-4 transition-all duration-200 hover:scale-[1.005] ${
                                        toxic
                                            ? isExplicit
                                                ? 'border-red-600/50 bg-gradient-to-r from-red-950/50 via-red-900/15 to-transparent shadow-lg shadow-red-950/20'
                                                : isImplicit
                                                ? 'border-purple-600/50 bg-gradient-to-r from-purple-950/50 via-purple-900/15 to-transparent shadow-lg shadow-purple-950/20'
                                                : 'border-rose-500/30 bg-rose-950/20'
                                            : 'border-gray-800/60 bg-[#141724]/70 hover:border-gray-700 hover:bg-[#181c2c]'
                                    }`}
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        {/* Author & Message */}
                                        <div className="flex items-start gap-3.5 flex-grow min-w-0">
                                            {/* Avatar */}
                                            <div
                                                className={`h-10 w-10 shrink-0 rounded-full overflow-hidden flex items-center justify-center font-bold text-xs ring-2 ${
                                                    toxic
                                                        ? isExplicit
                                                            ? 'ring-red-500/60 bg-red-900/50 text-red-200'
                                                            : 'ring-purple-500/60 bg-purple-900/50 text-purple-200'
                                                        : 'ring-gray-700 bg-gray-800 text-gray-300'
                                                }`}
                                            >
                                                {msg.author_image ? (
                                                    <img
                                                        src={msg.author_image}
                                                        alt={msg.author_name}
                                                        className="h-full w-full object-cover"
                                                        onError={(e) => {
                                                            e.currentTarget.style.display = 'none';
                                                        }}
                                                    />
                                                ) : (
                                                    <span>{msg.author_name ? msg.author_name.slice(0, 2).toUpperCase() : '??'}</span>
                                                )}
                                            </div>

                                            {/* Message Content */}
                                            <div className="flex flex-col min-w-0 flex-grow">
                                                <div className="flex items-center gap-2 flex-wrap">
                                                    <span className="text-sm font-bold text-gray-200 truncate">
                                                        {msg.author_name || 'Người dùng ẩn danh'}
                                                    </span>
                                                    <span className="text-[11px] text-gray-500 font-mono">
                                                        {msg.published_at
                                                            ? new Date(msg.published_at).toLocaleTimeString([], {
                                                                  hour: '2-digit',
                                                                  minute: '2-digit',
                                                                  second: '2-digit',
                                                              })
                                                            : ''}
                                                    </span>
                                                    {toxic ? (
                                                        <span className="inline-flex items-center gap-1 text-[10px] font-black uppercase text-red-400 bg-red-950/70 border border-red-800/40 px-2 py-0.5 rounded-full">
                                                            <AlertTriangle className="h-3 w-3" />
                                                            TOXIC
                                                        </span>
                                                    ) : (
                                                        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-950/50 border border-emerald-800/40 px-2 py-0.5 rounded-full">
                                                            NON-TOXIC
                                                        </span>
                                                    )}
                                                    {expr && getExpressionBadge(expr)}
                                                </div>

                                                <p className="mt-1.5 text-sm text-gray-300 break-words leading-relaxed select-text font-normal">
                                                    {msg.message}
                                                </p>

                                                {/* Score details */}
                                                {(msg.toxic_score !== undefined || msg.implicit_score !== undefined) && (
                                                    <div className="mt-2 flex items-center gap-3 text-[11px] text-gray-400">
                                                        {msg.toxic_score !== undefined && (
                                                            <span>
                                                                Điểm Độc hại: <strong className="text-rose-400">{Math.round(msg.toxic_score * 100)}%</strong>
                                                            </span>
                                                        )}
                                                        {isImplicit && msg.implicit_score !== undefined && (
                                                            <span>
                                                                Xác suất Ẩn ý: <strong className="text-purple-400">{Math.round(msg.implicit_score * 100)}%</strong>
                                                            </span>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Badges & Actions */}
                                        <div className="shrink-0 flex flex-col items-end gap-1.5">
                                            {getActionBadge(msg.recommended_action)}

                                            {/* Copy button */}
                                            <button
                                                onClick={() => handleCopy(msg.comment_id, msg.message)}
                                                className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg border border-gray-800 bg-[#161925] text-gray-400 hover:text-white text-xs flex items-center gap-1"
                                                title="Sao chép nội dung"
                                            >
                                                {copiedId === msg.comment_id ? (
                                                    <Check className="h-3 w-3 text-emerald-400" />
                                                ) : (
                                                    <Copy className="h-3 w-3" />
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            </div>
        </div>
    );
};
