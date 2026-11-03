import { MetricModel, ILiveStreamMetric } from "../model/LiveStreamMetric";

/**
 * Dịch vụ xử lý thống kê luồng trực tiếp theo chuẩn DS108.
 */
export const getMetricsByVideoId = async (videoId: string): Promise<Partial<ILiveStreamMetric>[]> => {
    const metrics = await MetricModel
        .find({ video_id: videoId })
        .select({
            _id: 1,
            video_id: 1,
            window_start: 1,
            total_comments: 1,
            toxic_count: 1,
            explicit_count: 1,
            implicit_count: 1,
            toxic_ratio: 1,
            unique_viewers: 1,
        })
        .sort({ window_start: -1 })
        .limit(20)
        .lean();

    return metrics.reverse();
};
