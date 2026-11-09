import { Request, Response, NextFunction } from "express";
import { ResponseDTO } from "../model/response";
import { startTikTokCrawler, stopTikTokCrawler } from "../service/tiktok-service";
import { AppError } from "../error/AppError";
import { addSSEClient } from "../service/sse-service";

export const getTikTokLiveController = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { url } = req.body;
    if (!url) {
      throw new AppError("TikTok username hoặc live URL là bắt buộc", 400);
    }

    const streamId = await startTikTokCrawler(url);

    res.status(202).json(
      ResponseDTO.successData(
        {
          streamId,
          videoId: streamId,
          platform: "tiktok",
        },
        "Khởi động theo dõi TikTok LIVE thành công",
        202
      )
    );
  } catch (error) {
    next(error);
  }
};

export const stopTikTokCrawlerController = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { url } = req.body;
    if (!url) {
      throw new AppError("TikTok username hoặc live URL là bắt buộc", 400);
    }

    const message = await stopTikTokCrawler(url);
    res.status(200).json(ResponseDTO.success(message));
  } catch (error) {
    next(error);
  }
};

export const sseTikTokStreamEventsController = async (
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> => {
  try {
    const { videoId } = req.params;
    if (!videoId) {
      throw new AppError("Stream ID là bắt buộc", 400);
    }

    // Thiết lập header cho SSE
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("X-Accel-Buffering", "no");
    res.flushHeaders();

    // Đăng ký client vào SSE Service
    await addSSEClient(videoId, res);
  } catch (error) {
    next(error);
  }
};
