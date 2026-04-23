// 所有接口请求统一收口到这里，方便后续替换后端地址。
import axios from "axios";

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || "",
  timeout: 10000
});

export async function fetchSummary() {
  const response = await request.get("/api/summary");
  return response.data;
}

export async function fetchCurrentRanking() {
  const response = await request.get("/api/ranking/current");
  return response.data;
}

export async function fetchTrend(keyword) {
  const response = await request.get("/api/trend", {
    params: { keyword }
  });
  return response.data;
}
