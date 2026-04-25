const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch (error) {
    throw new Error("接口请求失败，请检查后端服务是否启动");
  }

  if (!response.ok) {
    let message = "接口请求失败，请稍后重试";
    try {
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const data = await response.json();
        message = data.detail || data.message || message;
      } else {
        message = (await response.text()) || message;
      }
    } catch (error) {
      message = "接口返回异常，请稍后重试";
    }
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

export function getTopKeywords(limit = 20) {
  return request(`/api/analysis/keywords/top?limit=${encodeURIComponent(limit)}`);
}

export function getDailyStats() {
  return request("/api/analysis/daily");
}

export function runAnalysisJob() {
  return request("/api/analysis/run", { method: "POST" });
}
