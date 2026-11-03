import { CommentModel } from "../model/LiveCommentAnalysis";
import { ILiveCommentAnalysis } from "../model/LiveCommentAnalysis";

/**
 * Dịch vụ xử lý phân tích bình luận trực tiếp theo chuẩn DS108.
 */
export const getCommentsByVideoId = async (videoId: string): Promise<Partial<ILiveCommentAnalysis>[]> => {
    const comments = await CommentModel
        .find({ video_id: videoId })
        .select({
            _id: 1,
            comment_id: 1,
            video_id: 1,
            author_id: 1,
            author_name: 1,
            author_image: 1,
            message: 1,
            toxicity: 1,
            expression_type: 1,
            toxic_label: 1,
            toxic_category: 1,
            toxic_score: 1,
            implicit_score: 1,
            recommended_action: 1,
            published_at: 1,
        })
        .limit(100)
        .sort({ published_at: -1 })
        .lean();

    return comments;
};
