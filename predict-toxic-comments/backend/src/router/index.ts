import express from "express";
import youtubeRouter from "./youtube/index";
import tiktokRouter from "./tiktok/index";

const router = express.Router();

router.use("/youtube", youtubeRouter);
router.use("/tiktok", tiktokRouter);

export default router;
