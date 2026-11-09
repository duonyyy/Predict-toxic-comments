import { spawn, ChildProcess } from "child_process";
import path from "path";
import {
  StatusCrawler,
  redisStream,
  REDIS_KEYS,
  setStatusActiveCrawlers,
  delLockActiveCrawlers,
  acquireLockActiveCrawlers,
} from "./redis-service";
import { KAFKA_BOOTSTRAP_SERVER, KAFKA_TOPIC } from "../utils/config";
import { AppError } from "../error/AppError";

const activeTikTokProcesses = new Map<string, ChildProcess>();

export function extractTikTokUsername(urlOrUsername: string): string {
  let raw = urlOrUsername.trim().replace(/^@/, "");
  if (raw.includes("tiktok.com")) {
    const parts = raw.split("/");
    for (const part of parts) {
      if (part.startsWith("@")) {
        return part.replace(/^@/, "").replace(/\/$/, "").split("?")[0];
      }
    }
  }
  return raw.replace(/\/$/, "").split("?")[0];
}

export function getTikTokStreamId(urlOrUsername: string): string {
  const username = extractTikTokUsername(urlOrUsername);
  return `tiktok-${username}`;
}

export async function startTikTokCrawler(urlOrUsername: string): Promise<string> {
  const username = extractTikTokUsername(urlOrUsername);
  if (!username) {
    throw new AppError("Username hoặc đường link TikTok không hợp lệ", 400);
  }

  const streamId = `tiktok-${username}`;

  // Kiểm tra xem tiến trình đã chạy trong bộ nhớ chưa
  if (activeTikTokProcesses.has(streamId)) {
    console.log(`TikTok crawler đã chạy cho streamId=${streamId}`);
    return streamId;
  }

  const locked = await acquireLockActiveCrawlers(streamId);
  if (!locked) {
    console.log(`Lock active cho TikTok crawler streamId=${streamId}`);
    return streamId;
  }

  const scriptPath = path.resolve(__dirname, "../../scripts/tiktok_crawler.py");
  const pythonCmd = process.platform === "win32" ? "python" : "python3";

  console.log(`▶ Khởi động TikTok Live Crawler cho @${username} (streamId=${streamId})...`);

  await setStatusActiveCrawlers(streamId, StatusCrawler.RUNNING);
  await redisStream.xadd(
    REDIS_KEYS.STREAM_CRAWLER,
    "MAXLEN",
    "~",
    1000,
    "*",
    "data",
    JSON.stringify({
      type: StatusCrawler.RUNNING,
      liveChatId: streamId,
      videoId: streamId,
      platform: "tiktok",
    })
  );

  const proc = spawn(
    pythonCmd,
    [
      scriptPath,
      "--username",
      username,
      "--stream_id",
      streamId,
      "--kafka",
      KAFKA_BOOTSTRAP_SERVER,
      "--topic",
      KAFKA_TOPIC,
    ],
    {
      stdio: ["ignore", "pipe", "pipe"],
    }
  );

  activeTikTokProcesses.set(streamId, proc);

  proc.stdout?.on("data", (data) => {
    console.log(`[TikTok-stdout] ${data.toString().trim()}`);
  });

  proc.stderr?.on("data", (data) => {
    console.error(`[TikTok-stderr] ${data.toString().trim()}`);
  });

  proc.on("exit", async (code) => {
    console.log(`🛑 TikTok crawler cho ${streamId} đã thoát với mã code ${code}`);
    activeTikTokProcesses.delete(streamId);
    await setStatusActiveCrawlers(streamId, StatusCrawler.STOPPED);
    await delLockActiveCrawlers(streamId);
    await redisStream.xadd(
      REDIS_KEYS.STREAM_CRAWLER,
      "MAXLEN",
      "~",
      1000,
      "*",
      "data",
      JSON.stringify({
        type: StatusCrawler.STOPPED,
        liveChatId: streamId,
        videoId: streamId,
        platform: "tiktok",
      })
    );
  });

  return streamId;
}

export async function stopTikTokCrawler(urlOrUsername: string): Promise<string> {
  const username = extractTikTokUsername(urlOrUsername);
  const streamId = `tiktok-${username}`;

  const proc = activeTikTokProcesses.get(streamId);
  if (proc) {
    proc.kill("SIGTERM");
    activeTikTokProcesses.delete(streamId);
  }

  await setStatusActiveCrawlers(streamId, StatusCrawler.STOPPED);
  await delLockActiveCrawlers(streamId);
  await redisStream.xadd(
    REDIS_KEYS.STREAM_CRAWLER,
    "MAXLEN",
    "~",
    1000,
    "*",
    "data",
    JSON.stringify({
      type: StatusCrawler.STOPPED,
      liveChatId: streamId,
      videoId: streamId,
      platform: "tiktok",
    })
  );

  return `Đã dừng TikTok live crawler cho @${username}`;
}
