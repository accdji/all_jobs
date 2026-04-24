from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from time import monotonic
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, Playwright
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


STEALTH_SCRIPT = """
(() => {
  "use strict";
  const nativeFunctionToString = Function.prototype.toString;
  const nativeSourceMap = new WeakMap();

  const registerNativeSource = (fn, source) => {
    try { nativeSourceMap.set(fn, source); } catch (_) {}
  };

  Object.defineProperty(Function.prototype, "toString", {
    configurable: true,
    writable: true,
    value: function toString() {
      if (nativeSourceMap.has(this)) return nativeSourceMap.get(this);
      return nativeFunctionToString.call(this);
    },
  });

  registerNativeSource(Function.prototype.toString, nativeFunctionToString.toString());

  const stealthify = (obj, prop, handler) => {
    const original = obj[prop];
    if (typeof original !== "function") return;

    const wrapped = function (...args) {
      return handler.call(this, original, args);
    };

    Object.defineProperty(wrapped, "name", {
      value: prop,
      configurable: true,
    });

    try { Object.setPrototypeOf(wrapped, Object.getPrototypeOf(original)); } catch (_) {}
    registerNativeSource(wrapped, nativeFunctionToString.call(original));

    const desc = Object.getOwnPropertyDescriptor(obj, prop);
    Object.defineProperty(obj, prop, { ...desc, value: wrapped });
  };

  ["log", "debug", "info", "warn", "error"].forEach((name) => {
    stealthify(console, name, (original, args) => original.apply(this, args));
  });

  ["table", "dir", "dirxml"].forEach((name) => {
    stealthify(console, name, () => undefined);
  });

  registerNativeSource(registerNativeSource, "function registerNativeSource() { [native code] }");
})();
"""


HIDE_WEBDRIVER_SCRIPT = """
(() => {
  Object.defineProperty(navigator, "webdriver", {
    get: () => undefined,
  });
  Object.defineProperty(navigator, "plugins", {
    get: () => [1, 2, 3, 4, 5],
  });
  window.chrome = { runtime: {} };
})();
"""


JOB_CARD_SELECTORS = [
    ".job-card-wrapper",
    ".job-card-body",
    ".search-job-result .job-card-box",
    ".rec-job-list .job-card-wrapper",
]
CHAT_LIST_SELECTORS = [
    ".chat-list",
    ".message-list",
    ".friend-list",
    ".list-warp",
    ".list-wrap",
    ".conversation-list",
    "li[data-id]",
    ".item-friend",
    ".friend-item",
    '[class*="conversation"]',
]
CHAT_INPUT_SELECTORS = [
    'textarea[placeholder*="请输入"]',
    'textarea[placeholder*="消息"]',
    "textarea",
    'div[contenteditable="true"]',
    ".input-area textarea",
    ".chat-input textarea",
]
SEND_BUTTON_SELECTORS = [
    'button:has-text("发送")',
    'button:has-text("发 送")',
    'button:has-text("立即发送")',
    ".btn-send",
    ".send-btn",
]
CHAT_MESSAGE_SELECTORS = [
    ".message-item",
    ".item-myself",
    ".item-friend",
    ".chat-message",
    ".message-card",
    ".chat-record .item",
    ".im-message",
]


@dataclass
class BrowserWorker:
    base_url: str
    state_dir: str
    headless: bool = False
    _executor: ThreadPoolExecutor = field(
        default_factory=lambda: ThreadPoolExecutor(max_workers=1, thread_name_prefix="boss-browser"),
        init=False,
        repr=False,
    )
    _playwright: Playwright | None = field(default=None, init=False, repr=False)
    _browser: Browser | None = field(default=None, init=False, repr=False)
    _context: BrowserContext | None = field(default=None, init=False, repr=False)
    _page: Page | None = field(default=None, init=False, repr=False)

    def _run(self, fn, *args, **kwargs):
        future: Future = self._executor.submit(fn, *args, **kwargs)
        return future.result()

    def _launch_args(self) -> dict:
        return {
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--window-size=1920,1080",
            ],
        }

    def _new_context(self, browser: Browser) -> BrowserContext:
        return browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            permissions=["notifications"],
        )

    def _inject_stealth(self, page: Page) -> None:
        page.add_init_script(STEALTH_SCRIPT)
        page.add_init_script(HIDE_WEBDRIVER_SCRIPT)

    def _cleanup(self) -> None:
        for target in (self._page, self._context, self._browser):
            if target is None:
                continue
            try:
                target.close()
            except Exception:
                pass

        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:
                pass

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def _get_live_page(self) -> Page | None:
        page = self._page
        if page is None:
            return None

        try:
            if page.is_closed():
                raise PlaywrightError("page closed")
            _ = page.url
        except Exception:
            self._cleanup()
            return None

        return page

    def status(self) -> dict:
        return self._run(self._status_impl)

    def _status_impl(self) -> dict:
        page = self._get_live_page()
        session_active = page is not None
        login_status = "logged_in" if session_active and self._looks_logged_in(page) else "logged_out"
        page_url = ""
        page_title = ""
        if page is not None:
            try:
                page_url = page.url
                page_title = page.title()
            except Exception:
                page_url = ""
                page_title = ""
        return {
            "base_url": self.base_url,
            "state_dir": "浏览器关闭后不会保留登录状态",
            "state_exists": session_active,
            "login_status": login_status,
            "page_url": page_url,
            "page_title": page_title,
            "headless": self.headless,
            "engine": "playwright-python",
            "mode": "single-main-page-real-actions",
        }

    def manual_login(self, timeout_seconds: int = 300) -> dict:
        return self._run(self._manual_login_impl, timeout_seconds)

    def _manual_login_impl(self, timeout_seconds: int = 300) -> dict:
        self._cleanup()
        try:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(**self._launch_args())
            self._context = self._new_context(self._browser)
            self._page = self._context.new_page()
            self._inject_stealth(self._page)
            self._page.goto(f"{self.base_url}/web/user/?ka=header-login", wait_until="domcontentloaded")
        except PlaywrightError as error:
            self._cleanup()
            return {"login_status": "error", "next_step": f"无法启动浏览器：{error}"}

        deadline = monotonic() + timeout_seconds
        while monotonic() < deadline:
            page = self._get_live_page()
            if page is None:
                return {"login_status": "logged_out", "next_step": "浏览器已关闭，当前登录状态不会保留。"}
            try:
                page.wait_for_timeout(1500)
                if self._looks_logged_in(page):
                    return {
                        "login_status": "logged_in",
                        "checked_at": datetime.utcnow().isoformat(),
                        "next_step": "已检测到登录成功，后续只会在当前主页面进行点击操作。",
                    }
            except PlaywrightError:
                self._cleanup()
                return {"login_status": "logged_out", "next_step": "浏览器已关闭，当前登录状态不会保留。"}

        return {"login_status": "logged_out", "next_step": "登录超时，请重新打开浏览器登录。"}

    def login_check(self) -> dict:
        return self._run(self._login_check_impl)

    def _login_check_impl(self) -> dict:
        page = self._get_live_page()
        if page is None:
            return {
                "login_status": "logged_out",
                "checked_at": datetime.utcnow().isoformat(),
                "next_step": "浏览器未打开，需要重新登录。",
            }

        success = self._looks_logged_in(page)
        return {
            "login_status": "logged_in" if success else "logged_out",
            "checked_at": datetime.utcnow().isoformat(),
            "next_step": "浏览器在线，登录状态正常。" if success else "浏览器在线，但当前未登录。",
        }

    def collect_jobs(
        self,
        keyword: str,
        city: str = "101010100",
        auto_apply_limit: int = 1,
        intro_message: str = "",
        profile: dict[str, Any] | None = None,
    ) -> dict:
        return self._run(self._collect_jobs_impl, keyword, city, auto_apply_limit, intro_message, profile or {})

    def _collect_jobs_impl(
        self,
        keyword: str,
        city: str = "101010100",
        auto_apply_limit: int = 1,
        intro_message: str = "",
        profile: dict[str, Any] | None = None,
    ) -> dict:
        page = self._require_logged_in_page(keyword)
        if isinstance(page, dict):
            return page

        try:
            self._open_jobs_panel(page)
            self._search_jobs(page, keyword)
            self._wait_for_job_cards(page)
            raw_jobs = self._extract_job_cards(page)
        except PlaywrightError as error:
            diagnostics = self._page_diagnostics(page)
            return {
                "collected": 0,
                "keyword": keyword,
                "source": "boss",
                "login_status": "logged_in",
                "jobs": [],
                "note": f"职位页操作失败：{error} | {diagnostics}",
            }

        jobs = [self._normalize_job(item) for item in raw_jobs if item.get("role") or item.get("company")]
        applied_results: list[dict[str, Any]] = []
        messages: list[dict[str, Any]] = []
        max_apply = max(0, min(auto_apply_limit, len(jobs)))

        for index in range(max_apply):
            target = jobs[index]
            apply_result = self._open_job_and_start_chat(page, index, target)
            if not apply_result.get("entered_chat"):
                target["apply_status"] = "failed"
                target["apply_note"] = apply_result.get("note", "未进入沟通页")
                applied_results.append(
                    {
                        "company": target["company"],
                        "role": target["role"],
                        "conversation_id": "",
                        "sent": False,
                        "note": target["apply_note"],
                    }
                )
                self._restore_job_search(page, keyword)
                continue

            content = (intro_message or "").strip() or self._compose_intro_message(target, profile or {})
            send_result = self._send_current_chat_message(page, content)
            current_thread = self._extract_current_conversation(page, fallback=target)

            target["apply_status"] = "sent" if send_result.get("sent") else "opened"
            target["apply_note"] = send_result.get("note", "")
            target["conversation_id"] = current_thread.get("conversation_id", "")
            applied_results.append(
                {
                    "company": current_thread.get("company") or target["company"],
                    "role": current_thread.get("role") or target["role"],
                    "conversation_id": current_thread.get("conversation_id") or "",
                    "sent": bool(send_result.get("sent")),
                    "note": send_result.get("note", ""),
                    "message": content,
                }
            )
            if current_thread.get("incoming") or send_result.get("sent"):
                messages.append(
                    {
                        **current_thread,
                        "reply": content if send_result.get("sent") else current_thread.get("reply", ""),
                        "reply_time": datetime.now().strftime("%H:%M"),
                    }
                )

            if index < max_apply - 1:
                self._restore_job_search(page, keyword)

        return {
            "collected": len(jobs),
            "keyword": keyword,
            "source": "boss",
            "login_status": "logged_in",
            "jobs": jobs,
            "applied_count": sum(1 for item in applied_results if item.get("sent")),
            "applied_results": applied_results,
            "messages": messages,
            "note": "已在主页面完成职位抓取，并尝试进入沟通发送首条消息。",
        }

    def sync_messages(self, known_conversation_ids: list[str] | None = None) -> dict:
        return self._run(self._sync_messages_impl, known_conversation_ids or [])

    def _sync_messages_impl(self, known_conversation_ids: list[str] | None = None) -> dict:
        page = self._require_logged_in_page()
        if isinstance(page, dict):
            return {
                "threads_synced": 0,
                "login_status": page.get("login_status", "logged_out"),
                "messages": [],
                "note": page.get("note") or page.get("next_step") or "无法同步消息。",
            }

        known_ids = {item for item in (known_conversation_ids or []) if item}
        try:
            self._open_chat_panel(page)
            summaries = self._extract_thread_summaries(page)
        except PlaywrightError as error:
            return {
                "threads_synced": 0,
                "login_status": "logged_in",
                "messages": [],
                "note": f"消息页操作失败：{error}",
            }

        messages: list[dict[str, Any]] = []
        for summary in summaries[:10]:
            if not summary.get("has_new_reply") and summary.get("conversation_id") in known_ids:
                continue
            if not self._open_conversation(page, summary):
                continue

            transcript = self._extract_chat_transcript(page)
            if not transcript:
                continue

            company = summary.get("company") or self._extract_chat_meta_text(page, [".chat-top .name", ".chat-title", "h3"])
            role = summary.get("role") or self._extract_chat_meta_text(page, [".position-name", ".job-name", ".chat-top .position"])
            hr_name = summary.get("hr_name") or self._extract_chat_meta_text(page, [".chat-top .friend-name", ".boss-name", ".name"])
            last_hr = next((item for item in reversed(transcript) if item["speaker"] == "hr"), None)
            last_candidate = next((item for item in reversed(transcript) if item["speaker"] == "candidate"), None)

            messages.append(
                {
                    "company": (company or "未知公司")[:40],
                    "role": (role or "")[:40],
                    "hr_name": (hr_name or "")[:40],
                    "conversation_id": summary.get("conversation_id") or f"conversation-{len(messages) + 1}",
                    "time": (last_hr or last_candidate or {}).get("time", datetime.now().strftime("%H:%M")),
                    "incoming": (last_hr or {}).get("content", summary.get("preview", ""))[:500],
                    "reply": (last_candidate or {}).get("content", "")[:500],
                    "has_new_reply": bool(summary.get("has_new_reply")),
                    "transcript": transcript,
                    "synced_message_count": len(transcript),
                }
            )

        return {
            "threads_synced": len(messages),
            "login_status": "logged_in",
            "messages": messages,
            "note": "已在当前主页面点击会话并同步真实聊天记录。" if messages else "当前没有新的会话回复。",
        }

    def send_message(self, payload: dict) -> dict:
        return self._run(self._send_message_impl, payload)

    def _send_message_impl(self, payload: dict) -> dict:
        page = self._require_logged_in_page()
        if isinstance(page, dict):
            return {
                "sent": False,
                "thread_id": payload.get("thread_id"),
                "note": page.get("note") or page.get("next_step") or "当前无法发送消息。",
            }

        message = str(payload.get("message") or "").strip()
        if not message:
            return {"sent": False, "thread_id": payload.get("thread_id"), "note": "发送内容为空。"}

        try:
            self._open_chat_panel(page)
            if payload.get("conversation_id") or payload.get("company"):
                self._open_conversation(
                    page,
                    {
                        "conversation_id": str(payload.get("conversation_id") or ""),
                        "company": str(payload.get("company") or ""),
                        "role": str(payload.get("role") or ""),
                        "hr_name": str(payload.get("hr_name") or ""),
                    },
                )
            result = self._send_current_chat_message(page, message)
        except PlaywrightError as error:
            return {"sent": False, "thread_id": payload.get("thread_id"), "note": f"发送失败：{error}"}

        result["thread_id"] = payload.get("thread_id") or payload.get("conversation_id")
        return result

    def _require_logged_in_page(self, keyword: str | None = None) -> Page | dict[str, Any]:
        page = self._get_live_page()
        if page is None:
            return {
                "collected": 0,
                "keyword": keyword or "",
                "source": "boss",
                "login_status": "logged_out",
                "jobs": [],
                "note": "浏览器未打开，请先重新登录。",
            }
        if not self._looks_logged_in(page):
            return {
                "collected": 0,
                "keyword": keyword or "",
                "source": "boss",
                "login_status": "logged_out",
                "jobs": [],
                "note": "当前未登录，请重新打开浏览器登录。",
            }
        return page

    def _open_jobs_panel(self, page: Page) -> None:
        if self._has_job_cards(page):
            return
        if self._click_candidates(
            page,
            [
                'a[href*="/job-recommend"]',
                'a[href*="/job"]',
                '[ka*="job"]',
                'text=推荐职位',
                'text=职位',
                'text=找工作',
            ],
        ):
            page.wait_for_timeout(1800)
            return
        self._click_navigation(page, ["推荐职位", "职位", "找工作"], ["/job-recommend", "/job"])

    def _open_chat_panel(self, page: Page) -> None:
        if self._is_chat_page(page):
            return
        clicked = self._click_candidates(
            page,
            [
                'a[href*="/chat"]',
                'a[href*="chat/index"]',
                'a[href*="geek/chat"]',
                '[ka*="chat"]',
                '[data-title*="聊天"]',
                '[data-title*="消息"]',
                '[data-name*="聊天"]',
                '[data-name*="消息"]',
                'text=聊天',
                'text=消息',
                'text=沟通',
            ],
        )
        if not clicked:
            clicked = self._click_chat_entry_by_dom(page)
        if not clicked:
            self._click_navigation(page, ["聊天", "消息", "沟通"], ["/chat"])

        if not self._wait_for_any(page, CHAT_LIST_SELECTORS, timeout_ms=8000):
            raise PlaywrightError("点击消息入口后，未出现会话列表。")

    def _search_jobs(self, page: Page, keyword: str) -> None:
        selectors = [
            'input[placeholder*="搜索"]',
            'input[placeholder*="职位"]',
            'input[placeholder*="公司"]',
            'input[type="search"]',
            ".search-input",
            ".ipt-search",
        ]
        for selector in selectors:
            locator = page.locator(selector).first
            try:
                if locator.count() == 0:
                    continue
                locator.click()
                locator.fill(keyword)
                locator.press("Enter")
                return
            except Exception:
                continue
        raise PlaywrightError("未找到职位搜索输入框。")

    def _wait_for_job_cards(self, page: Page, timeout_ms: int = 12000) -> None:
        if not self._wait_for_any(page, JOB_CARD_SELECTORS, timeout_ms=timeout_ms):
            raise PlaywrightTimeoutError("职位列表加载超时。")

    def _wait_for_any(self, page: Page, selectors: list[str], timeout_ms: int = 8000) -> bool:
        deadline = monotonic() + (timeout_ms / 1000)
        while monotonic() < deadline:
            try:
                for selector in selectors:
                    if page.locator(selector).count() > 0:
                        return True
            except Exception:
                pass
            page.wait_for_timeout(300)
        return False

    def _extract_job_cards(self, page: Page) -> list[dict[str, Any]]:
        locator = self._first_existing_locator(page, JOB_CARD_SELECTORS)
        if locator is None:
            return []
        return locator.evaluate_all(
            """
            (nodes) => nodes.slice(0, 20).map((node) => {
              const text = (value) => (value || '').replace(/\\s+/g, ' ').trim();
              const pick = (selectors) => {
                for (const selector of selectors) {
                  const match = node.querySelector(selector);
                  if (match && text(match.textContent)) return text(match.textContent);
                }
                return '';
              };
              const tags = Array.from(node.querySelectorAll('.tag-list li, .job-card-footer .tag-item, .labels-tag span, .job-labels span'))
                .map((tag) => text(tag.textContent))
                .filter(Boolean);
              const link = node.querySelector('a[href*="job_detail"], a[href*="/job/"], a[href*="job-card"]');
              return {
                role: pick(['.job-name', '.job-title', '.job-card-left .job-name']),
                company: pick(['.company-name', '.brand-name', '.company-text']),
                salary: pick(['.salary', '.job-salary']),
                location: pick(['.job-area', '.job-area-wrapper', '.company-location']),
                summary: pick(['.info-desc', '.job-card-body', '.job-labels', '.job-info']),
                tags,
                url: link ? link.href : '',
              };
            })
            """,
        )

    def _normalize_job(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
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

    def _page_diagnostics(self, page: Page) -> str:
        try:
            title = page.title()
        except Exception:
            title = ""
        try:
            snippet = page.evaluate(
                """
                () => {
                  const text = (document.body?.innerText || '').replace(/\\s+/g, ' ').trim();
                  return text.slice(0, 120);
                }
                """
            )
        except Exception:
            snippet = ""
        return f"url={page.url} title={title} snippet={snippet}"

    def _open_job_and_start_chat(self, page: Page, job_index: int, job: dict[str, Any]) -> dict[str, Any]:
        card_locator = self._first_existing_locator(page, JOB_CARD_SELECTORS)
        if card_locator is None or card_locator.count() <= job_index:
            return {"entered_chat": False, "note": "未找到目标职位卡片。"}

        card = card_locator.nth(job_index)
        self._safe_click(card)
        page.wait_for_timeout(1200)

        entered_chat = self._click_candidates(
            page,
            [
                'button:has-text("立即沟通")',
                'button:has-text("立即投递")',
                'button:has-text("立即聊天")',
                'a:has-text("立即沟通")',
                'a:has-text("立即投递")',
                ".op-btn-chat",
                ".btn-startchat",
                ".btn-chat",
            ],
        )
        if not entered_chat:
            entered_chat = bool(
                page.evaluate(
                    """
                    () => {
                      const text = ['立即沟通', '立即投递', '立即聊天', '继续沟通'];
                      const nodes = Array.from(document.querySelectorAll('button, a, div, span'));
                      const visible = (node) => {
                        const style = window.getComputedStyle(node);
                        const rect = node.getBoundingClientRect();
                        return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
                      };
                      for (const node of nodes) {
                        const value = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                        if (!visible(node)) continue;
                        if (text.some((item) => value.includes(item))) {
                          node.click();
                          return true;
                        }
                      }
                      return false;
                    }
                    """
                )
            )
        if entered_chat:
            page.wait_for_timeout(1800)

        if not self._wait_for_any(page, CHAT_INPUT_SELECTORS + CHAT_LIST_SELECTORS, timeout_ms=8000):
            return {"entered_chat": False, "note": f"已打开 {job['company']} / {job['role']}，但没有进入可发送消息的界面。"}

        return {"entered_chat": True, "note": f"已进入 {job['company']} / {job['role']} 沟通页。"}

    def _restore_job_search(self, page: Page, keyword: str) -> None:
        if self._has_job_cards(page):
            return
        try:
            page.go_back(wait_until="domcontentloaded")
            page.wait_for_timeout(1200)
        except Exception:
            pass
        if self._has_job_cards(page):
            return
        try:
            self._open_jobs_panel(page)
            self._search_jobs(page, keyword)
            self._wait_for_job_cards(page)
        except Exception:
            pass

    def _send_current_chat_message(self, page: Page, content: str) -> dict[str, Any]:
        locator = self._first_existing_locator(page, CHAT_INPUT_SELECTORS)
        if locator is None:
            return {"sent": False, "note": "未找到聊天输入框。"}

        try:
            element = locator.first
            element.scroll_into_view_if_needed(timeout=1000)
            tag = (element.evaluate("(node) => node.tagName.toLowerCase()") or "").lower()
            if tag == "textarea":
                element.fill(content)
            else:
                element.click()
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                element.type(content, delay=30)
        except Exception as error:
            return {"sent": False, "note": f"写入聊天输入框失败：{error}"}

        if self._click_candidates(page, SEND_BUTTON_SELECTORS):
            page.wait_for_timeout(1200)
            return {"sent": True, "note": "消息已发送。"}

        try:
            page.keyboard.press("Enter")
            page.wait_for_timeout(1200)
            return {"sent": True, "note": "消息已通过回车发送。"}
        except Exception as error:
            return {"sent": False, "note": f"发送按钮点击失败：{error}"}

    def _extract_thread_summaries(self, page: Page) -> list[dict[str, Any]]:
        locator = self._first_existing_locator(page, CHAT_LIST_SELECTORS)
        if locator is None:
            return []
        return locator.evaluate_all(
            """
            (nodes) => nodes
              .map((node, index) => {
                const text = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const value = text(node.textContent);
                if (!value) return null;
                const company = text(
                  node.querySelector('.name, .friend-name, .title, .company-name, .conversation-title')?.textContent
                ) || value.split(' ')[0];
                const role = text(
                  node.querySelector('.job-name, .position, .desc, .subtitle')?.textContent
                );
                const time = text(node.querySelector('.time, .date, .last-time')?.textContent);
                const preview = text(
                  node.querySelector('.text, .last-msg, .gray, .desc, .message, .conversation-content')?.textContent
                ) || value;
                const unread = !!node.querySelector('.unread, .badge, .dot, [class*="unread"], [class*="badge"]');
                return {
                  company,
                  role,
                  hr_name: text(node.querySelector('.boss-name, .hr-name')?.textContent),
                  preview,
                  time,
                  has_new_reply: unread,
                  conversation_id: node.getAttribute('data-id') || node.getAttribute('ka') || node.getAttribute('data-key') || `conversation-${index + 1}`,
                };
              })
              .filter(Boolean)
              .slice(0, 30)
            """,
        )

    def _open_conversation(self, page: Page, summary: dict[str, Any]) -> bool:
        conversation_id = summary.get("conversation_id") or ""
        if conversation_id:
            selectors = [
                f'[data-id="{conversation_id}"]',
                f'[data-key="{conversation_id}"]',
                f'[ka="{conversation_id}"]',
            ]
            if self._click_candidates(page, selectors):
                page.wait_for_timeout(1200)
                return True

        company = str(summary.get("company") or "").strip()
        role = str(summary.get("role") or "").strip()
        hr_name = str(summary.get("hr_name") or "").strip()
        result = page.evaluate(
            """
            ([company, role, hrName]) => {
              const terms = [company, role, hrName].filter(Boolean);
              if (!terms.length) return false;
              const nodes = Array.from(document.querySelectorAll('li, .item-friend, .friend-item, [class*="conversation"]'));
              const visible = (node) => {
                const style = window.getComputedStyle(node);
                const rect = node.getBoundingClientRect();
                return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
              };
              for (const node of nodes) {
                if (!visible(node)) continue;
                const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                if (terms.every((term) => text.includes(term))) {
                  node.click();
                  return true;
                }
              }
              for (const node of nodes) {
                if (!visible(node)) continue;
                const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                if (terms.some((term) => text.includes(term))) {
                  node.click();
                  return true;
                }
              }
              return false;
            }
            """,
            [company, role, hr_name],
        )
        if result:
            page.wait_for_timeout(1200)
        return bool(result)

    def _extract_chat_transcript(self, page: Page) -> list[dict[str, str]]:
        locator = self._first_existing_locator(page, CHAT_MESSAGE_SELECTORS)
        if locator is None:
            return []
        transcript = locator.evaluate_all(
            """
            (nodes) => nodes
              .map((node) => {
                const text = (value) => (value || '').replace(/\\s+/g, ' ').trim();
                const content =
                  text(node.querySelector('.text, .bubble, .message-content, .content, .rich-text, p')?.textContent) ||
                  text(node.textContent);
                if (!content) return null;
                const className = (node.className || '').toString().toLowerCase();
                let speaker = 'system';
                if (className.includes('myself') || className.includes('mine') || className.includes('right') || className.includes('self')) {
                  speaker = 'candidate';
                } else if (className.includes('friend') || className.includes('left') || className.includes('boss') || className.includes('hr')) {
                  speaker = 'hr';
                }
                const time = text(node.querySelector('.time, .date, .message-time')?.textContent);
                return { speaker, content, time };
              })
              .filter(Boolean)
              .slice(-40)
            """,
        )
        return [item for item in transcript if item.get("content")]

    def _extract_current_conversation(self, page: Page, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
        transcript = self._extract_chat_transcript(page)
        fallback = fallback or {}
        hr_message = next((item for item in reversed(transcript) if item["speaker"] == "hr"), None)
        candidate_message = next((item for item in reversed(transcript) if item["speaker"] == "candidate"), None)
        company = self._extract_chat_meta_text(
            page,
            [".chat-top .company-name", ".chat-title .company", ".company-name", ".title"],
        ) or fallback.get("company", "")
        role = self._extract_chat_meta_text(
            page,
            [".chat-top .position-name", ".job-name", ".position-name", ".job-title"],
        ) or fallback.get("role", "")
        hr_name = self._extract_chat_meta_text(
            page,
            [".chat-top .name", ".friend-name", ".boss-name", ".chat-title .name"],
        )
        conversation_id = self._extract_active_conversation_id(page)
        return {
            "company": company or "未知公司",
            "role": role,
            "hr_name": hr_name,
            "conversation_id": conversation_id,
            "time": (hr_message or candidate_message or {}).get("time", datetime.now().strftime("%H:%M")),
            "incoming": (hr_message or {}).get("content", ""),
            "reply": (candidate_message or {}).get("content", ""),
            "has_new_reply": bool(hr_message),
            "transcript": transcript,
            "synced_message_count": len(transcript),
        }

    def _extract_chat_meta_text(self, page: Page, selectors: list[str]) -> str:
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() == 0:
                    continue
                value = (locator.text_content() or "").strip()
                if value:
                    return value
            except Exception:
                continue
        return ""

    def _extract_active_conversation_id(self, page: Page) -> str:
        try:
            value = page.evaluate(
                """
                () => {
                  const active = document.querySelector('.active[data-id], .item-friend.active, .friend-item.active, [class*="active"][data-id]');
                  if (!active) return '';
                  return active.getAttribute('data-id') || active.getAttribute('data-key') || active.getAttribute('ka') || '';
                }
                """
            )
            return str(value or "")
        except Exception:
            return ""

    def _compose_intro_message(self, job: dict[str, Any], profile: dict[str, Any]) -> str:
        summary = str(profile.get("summary") or "").strip()
        preferred_location = str(profile.get("preferred_location") or "").strip()
        desired_salary_min = str(profile.get("desired_salary_min") or "").strip()
        desired_salary_max = str(profile.get("desired_salary_max") or "").strip()
        skills = [str(item).strip() for item in profile.get("skills", []) if str(item).strip()]
        skill_text = "、".join(skills[:4])
        salary_text = ""
        if desired_salary_min or desired_salary_max:
            salary_text = f"，期望薪资在 {desired_salary_min or '?'} - {desired_salary_max or '?'}"

        parts = [f"你好，我对 {job.get('company', '贵公司')} 的 {job.get('role', '这个岗位')} 很感兴趣。"]
        if summary:
            parts.append(summary)
        elif skill_text:
            parts.append(f"我目前主要做 {skill_text} 相关工作，项目落地和工程协作经验比较完整。")
        else:
            parts.append("我有较完整的项目落地和协作经验，希望进一步了解岗位要求和团队方向。")
        if preferred_location:
            parts.append(f"我目前优先考虑 {preferred_location} 方向的机会{salary_text}。")
        elif salary_text:
            parts.append(f"我的求职期望是技术方向匹配{salary_text}。")
        parts.append("如果方便的话，想和你进一步沟通一下岗位细节。")
        return "".join(parts)

    def _click_candidates(self, page: Page, selectors: list[str]) -> bool:
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.count() == 0:
                    continue
                locator.scroll_into_view_if_needed(timeout=1000)
                locator.click(timeout=2000)
                return True
            except Exception:
                continue
        return False

    def _click_chat_entry_by_dom(self, page: Page) -> bool:
        try:
            result = page.evaluate(
                """
                () => {
                  const clickable = Array.from(document.querySelectorAll('a, button, div, span'));
                  const isVisible = (node) => {
                    const style = window.getComputedStyle(node);
                    const rect = node.getBoundingClientRect();
                    return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
                  };
                  const keywords = ['聊天', '消息', '沟通', 'chat'];
                  const hrefTokens = ['/chat', 'chat/index', 'geek/chat'];
                  const score = (node) => {
                    const text = ((node.textContent || '') + ' ' + (node.getAttribute('aria-label') || '') + ' ' + (node.getAttribute('title') || '')).toLowerCase();
                    const href = (node.getAttribute('href') || '').toLowerCase();
                    let value = 0;
                    for (const token of keywords) {
                      if (text.includes(token.toLowerCase())) value += 3;
                    }
                    for (const token of hrefTokens) {
                      if (href.includes(token)) value += 5;
                    }
                    if ((node.className || '').toString().toLowerCase().includes('chat')) value += 2;
                    if ((node.className || '').toString().toLowerCase().includes('message')) value += 2;
                    return value;
                  };
                  const candidates = clickable
                    .filter((node) => isVisible(node))
                    .map((node) => ({ node, score: score(node) }))
                    .filter((item) => item.score > 0)
                    .sort((a, b) => b.score - a.score);
                  const target = candidates[0]?.node;
                  if (!target) return { clicked: false };
                  target.scrollIntoView({ block: 'center', inline: 'center' });
                  target.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
                  target.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                  target.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                  target.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                  return { clicked: true };
                }
                """
            )
        except Exception:
            return False
        if result.get("clicked"):
            page.wait_for_timeout(1800)
            return True
        return False

    def _click_navigation(self, page: Page, texts: list[str], href_tokens: list[str]) -> None:
        result = page.evaluate(
            """
            ([texts, hrefTokens]) => {
              const nodes = Array.from(document.querySelectorAll('a, button, div, span'));
              const visible = (node) => {
                const style = window.getComputedStyle(node);
                const rect = node.getBoundingClientRect();
                return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
              };
              const matchText = (text) => texts.some((token) => text.includes(token));
              const matchHref = (href) => hrefTokens.some((token) => href.includes(token));
              for (const node of nodes) {
                if (!visible(node)) continue;
                const text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                const href = node.getAttribute('href') || '';
                if (matchText(text) || matchHref(href)) {
                  node.click();
                  return { clicked: true, text, href };
                }
              }
              return { clicked: false };
            }
            """,
            [texts, href_tokens],
        )
        if not result.get("clicked"):
            raise PlaywrightError(f"未找到导航入口：{texts}")
        page.wait_for_timeout(1800)

    def _first_existing_locator(self, page: Page, selectors: list[str]):
        for selector in selectors:
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    return locator
            except Exception:
                continue
        return None

    def _safe_click(self, locator) -> None:
        try:
            locator.scroll_into_view_if_needed(timeout=1000)
        except Exception:
            pass
        try:
            locator.click(timeout=2000)
        except Exception:
            locator.click(force=True, timeout=2000)

    def _has_job_cards(self, page: Page) -> bool:
        return self._first_existing_locator(page, JOB_CARD_SELECTORS) is not None

    def _is_chat_page(self, page: Page) -> bool:
        try:
            if "/chat" in page.url:
                return True
            return self._first_existing_locator(page, CHAT_LIST_SELECTORS) is not None
        except Exception:
            return False

    def _looks_logged_in(self, page: Page) -> bool:
        try:
            url = page.url
            if "login" in url or "/web/user" in url:
                return False
            cookie_names = {
                item.get("name", "")
                for item in page.context.cookies()
                if "zhipin.com" in item.get("domain", "")
            }
            auth_cookies = {"wt2", "__zp_stoken__", "bst", "uid", "t"}
            if cookie_names & auth_cookies:
                return True
            content = page.content()
        except PlaywrightError:
            return False

        if "/web/geek/" in url or "/chat/" in url or "/job/" in url:
            return True

        indicators = ["立即沟通", "在线简历", "面试", "聊天", "职位", "牛人", "我的在线简历", "推荐职位"]
        return any(token in content for token in indicators)

    def _score_job(self, item: dict[str, Any]) -> int:
        text = f"{item.get('role', '')} {item.get('summary', '')} {' '.join(item.get('tags', []))}".lower()
        score = 55
        for token in ["react", "typescript", "three.js", "webgl", "ai", "前端", "可视化"]:
            if token in text:
                score += 7
        for token in ["销售", "直播", "外包"]:
            if token in text:
                score -= 18
        return max(0, min(100, score))
