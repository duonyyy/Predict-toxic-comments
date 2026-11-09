import express from "express";
import {
  getTikTokLiveController,
  stopTikTokCrawlerController,
  sseTikTokStreamEventsController,
} from "../../controller/tiktokController";
import analysisRouter from "../youtube/analysis";
import metricsRouter from "../youtube/metrics";
import toxicUsersRouter from "../youtube/toxic-users";

const router = express.Router();

router.post("/live-chat", getTikTokLiveController);
router.post("/stop-crawler", stopTikTokCrawlerController);
router.get("/events/:videoId", sseTikTokStreamEventsController);
router.use("/analysis", analysisRouter);
router.use("/metrics", metricsRouter);
router.use("/toxic-users", toxicUsersRouter);

export default router;
