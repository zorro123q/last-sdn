const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "接口请求失败");
  }
  return response.json();
}

export function getSummary() {
  return request("/api/summary");
}

export function getCurrentRanking() {
  return request("/api/ranking/current");
}

export function getTrend(keyword) {
  return request(`/api/trend?keyword=${encodeURIComponent(keyword)}`);
}
