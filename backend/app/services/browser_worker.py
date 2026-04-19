from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import monotonic
from urllib.parse import quote

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


@dataclass
class BrowserWorker:
    base_url: str
    state_dir: str
    headless: bool = False

    def __post_init__(self) -> None:
        Path(self.state_dir).mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        state_path = Path(self.state_dir)
        return {
            "base_url": self.base_url,
            "state_dir": str(state_path),
            "state_exists": state_path.exists() and any(state_path.iterdir()),
            "headless": self.headless,
            "engine": "playwright-python",
            "mode": "manual-login-persistent-context",
        }

    def manual_login(self, timeout_seconds: int = 300) -> dict:
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.state_dir,
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(f"{self.base_url}/web/user/?ka=header-login", wait_until="domcontentloaded")

                deadline = monotonic() + timeout_seconds
                success = False
                while monotonic() < deadline:
                    page.wait_for_timeout(1500)
                    if self._looks_logged_in(page):
                        success = True
                        break

                context.close()
        except PlaywrightError as error:
            return {"login_status": "error", "next_step": f"无法启动浏览器：{error}"}

        return {
            "login_status": "logged_in" if success else "logged_out",
            "next_step": "会话已保存到本地持久化目录。" if success else "登录超时，请重新执行登录流程。",
        }

    def login_check(self) -> dict:
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.state_dir,
                    headless=self.headless,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                page = context.pages[0] if context.pages else context.new_page()
                try:
                    page.goto(f"{self.base_url}/web/geek/job-recommend", wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(2500)
                    success = self._looks_logged_in(page)
                finally:
                    context.close()
        except PlaywrightError as error:
            return {
                "login_status": "error",
                "checked_at": datetime.utcnow().isoformat(),
                "next_step": f"浏览器不可用：{error}",
            }

        return {
            "login_status": "logged_in" if success else "logged_out",
            "checked_at": datetime.utcnow().isoformat(),
            "next_step": "可以开始抓取职位和同步消息。" if success else "请先手动登录 BOSS。",
        }

    def collect_jobs(self, keyword: str, city: str = "101010100") -> dict:
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.state_dir,
                    headless=self.headless,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                page = context.pages[0] if context.pages else context.new_page()
                try:
                    page.goto(
                        f"{self.base_url}/web/geek/job?query={quote(keyword)}&city={city}&page=1",
                        wait_until="domcontentloaded",
                        timeout=45000,
                    )
                    page.wait_for_timeout(3500)
                    if not self._looks_logged_in(page):
                        return {
                            "collected": 0,
                            "keyword": keyword,
                            "source": "boss",
                            "jobs": [],
                            "note": "当前登录态无效，请先手动登录。",
                        }

                    jobs = page.locator(".job-card-wrapper").evaluate_all(
                    """
                    (nodes) => nodes.slice(0, 20).map((node) => {
                      const pick = (selectors) => {
                        for (const selector of selectors) {
                          const match = node.querySelector(selector);
                          if (match && match.textContent && match.textContent.trim()) {
                            return match.textContent.trim();
                          }
                        }
                        return "";
                      };
                      const tags = Array.from(node.querySelectorAll('.tag-list li, .job-card-footer .tag-item, .labels-tag span'))
                        .map((tag) => (tag.textContent || '').trim())
                        .filter(Boolean);
                      const link = node.querySelector('a[href*="job_detail"]');
                      return {
                        role: pick(['.job-name', '.job-title']),
                        company: pick(['.company-name', '.brand-name']),
                        salary: pick(['.salary', '.job-salary']),
                        location: pick(['.job-area', '.job-area-wrapper']),
                        summary: pick(['.info-desc', '.job-card-body', '.job-labels']),
                        tags,
                        url: link ? link.href : '',
                      };
                    })
                    """,
                    )
                except PlaywrightTimeoutError:
                    jobs = []
                finally:
                    context.close()
        except PlaywrightError as error:
            return {
                "collected": 0,
                "keyword": keyword,
                "source": "boss",
                "jobs": [],
                "note": f"浏览器不可用：{error}",
            }

        normalized = [
            {
                "company": item.get("company") or "未知公司",
                "role": item.get("role") or "未知职位",
                "salary": item.get("salary") or "薪资待沟通",
                "location": item.get("location") or "未知地点",
                "tags": item.get("tags") or [],
                "summary": item.get("summary") or "需要打开职位详情查看",
                "score": self._score_job(item),
                "boss_url": item.get("url") or "",
                "collected_at": datetime.utcnow().isoformat(),
            }
            for item in jobs
            if item.get("role") or item.get("company")
        ]

        return {
            "collected": len(normalized),
            "keyword": keyword,
            "source": "boss",
            "jobs": normalized,
            "note": "已完成列表抓取。",
        }

    def sync_messages(self) -> dict:
        candidate_urls = [f"{self.base_url}/web/geek/chat", f"{self.base_url}/web/chat/index"]
        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.state_dir,
                    headless=self.headless,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                page = context.pages[0] if context.pages else context.new_page()
                threads: list[str] = []
                try:
                    for url in candidate_urls:
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=30000)
                            page.wait_for_timeout(3000)
                            if not self._looks_logged_in(page):
                                continue
                            threads = page.locator("li, .item-friend, .friend-item, [class*='conversation']").evaluate_all(
                            """
                            (nodes) => nodes.slice(0, 12).map((node) => {
                              const text = node.textContent ? node.textContent.replace(/\\s+/g, ' ').trim() : '';
                              return text;
                            }).filter(Boolean)
                            """,
                            )
                            if threads:
                                break
                        except Exception:
                            continue
                finally:
                    context.close()
        except PlaywrightError as error:
            return {"threads_synced": 0, "messages": [], "note": f"浏览器不可用：{error}"}

        messages = [
            {
                "company": raw.split(" ")[0][:24] or f"会话 {index + 1}",
                "time": datetime.now().strftime("%H:%M"),
                "incoming": raw[:180],
                "reply": "待生成回复",
            }
            for index, raw in enumerate(threads[:6])
        ]

        return {
            "threads_synced": len(messages),
            "messages": messages,
            "note": "已同步会话列表摘要。" if messages else "没有抓到会话列表，可能当前页结构发生变化。",
        }

    def send_message(self, payload: dict) -> dict:
        return {
            "sent": False,
            "mode": "human_reviewed",
            "thread_id": payload.get("thread_id"),
            "note": "当前版本先保留人工发送，下一步再补页面输入与点击。",
        }

    def _looks_logged_in(self, page) -> bool:
        url = page.url
        if "login" in url or "/web/user" in url:
            return False
        try:
            content = page.content()
        except PlaywrightError:
            return False
        indicators = ["立即沟通", "在线简历", "面试", "聊天", "职位", "牛人"]
        return any(token in content for token in indicators)

    def _score_job(self, item: dict) -> int:
        text = f"{item.get('role', '')} {item.get('summary', '')} {' '.join(item.get('tags', []))}".lower()
        score = 55
        for token in ["react", "typescript", "three.js", "webgl", "ai", "前端", "可视化"]:
            if token in text:
                score += 7
        for token in ["销售", "直播", "外包"]:
            if token in text:
                score -= 18
        return max(0, min(100, score))
