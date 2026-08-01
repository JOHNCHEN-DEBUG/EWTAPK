#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EWT360 刷时长工具 · BETA5.0 Android 版
John Studio (c) 2024-2026 · 仅供技术学习研究
============================================
      ONLY JOHN STUDIO CANDO :)
============================================
"""

import os
import math
import time
import random
import hmac
import hashlib
import json
import threading
import socket

import requests

# ========================
# Kivy 导入
# ========================
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.utils import platform
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.behaviors import ToggleButtonBehavior
from kivy.uix.togglebutton import ToggleButton

# ========================
# 全局配置
# ========================
APP_TITLE = "EWT360 刷时长工具 BETA5.0"
APP_VERSION = "5.0"

# GitHub Raw 地址
AUTH_URL = "https://ghproxy.net/https://raw.githubusercontent.com/JOHNCHEN-DEBUG/ewt-keys/main/keys.txt"

# 监测上报配置
REPORT_URL = "https://gateway.ewt360.com/api/homeworkprod/homework/student/reportVideoPoint"
REPORT_KEY = "4dcc69ed56d6"

# 认证锁
AUTH_LOCKED = False

# 颜色主题
COLORS = {
    "bg": [0.063, 0.075, 0.102, 1],       # #10131a
    "panel": [0.086, 0.106, 0.149, 1],    # #161b26
    "card": [0.110, 0.137, 0.200, 1],     # #1c2333
    "accent": [0.0, 0.843, 1.0, 1],       # #00d7ff
    "green": [0.180, 0.804, 0.443, 1],     # #2ecc71
    "yellow": [0.945, 0.769, 0.059, 1],    # #f1c40f
    "red": [0.906, 0.298, 0.235, 1],       # #e74c3c
    "text": [0.831, 0.831, 0.831, 1],      # #d4d4d4
    "dim": [0.478, 0.541, 0.604, 1],       # #7a8a9a
    "input": [0.118, 0.149, 0.220, 1],     # #1e2638
    "border": [0.165, 0.200, 0.275, 1],    # #2a3346
}


# ========================
# 日志管理器（线程安全）
# ========================
class LogManager:
    """全局日志，通过 Clock 调度到主线程更新 UI"""

    def __init__(self, app_ref):
        self.app = app_ref

    def log(self, msg, level="info"):
        # 确保在主线程更新 UI
        Clock.schedule_once(lambda dt: self._do_log(msg, level), 0)

    def _do_log(self, msg, level):
        if self.app and self.app.root:
            self.app.root.add_log(msg, level)


# ========================
# 认证模块
# ========================
def check_internet() -> bool:
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except Exception:
        return False


def verify_key_online(user_key: str, log_func) -> bool:
    """联网验证 Key"""
    global AUTH_LOCKED

    if not check_internet():
        log_func("❌ 无法联网，认证服务器不可达", "error")
        return False

    try:
        log_func("🔐 正在连接认证服务器...", "accent")
        resp = requests.get(AUTH_URL, timeout=15)
        if resp.status_code != 200:
            log_func(f"❌ 服务器响应异常: {resp.status_code}", "error")
            return False

        valid_keys = {k.strip() for k in resp.text.splitlines() if k.strip()}

        if user_key in valid_keys:
            log_func("✅ 授权验证成功！", "ok")
            AUTH_LOCKED = True
            return True
        else:
            log_func("❌ 授权 Key 无效或被禁用", "error")
            return False
    except requests.exceptions.Timeout:
        log_func("❌ 连接认证服务器超时", "error")
        return False
    except Exception as e:
        log_func(f"❌ 认证请求失败: {e}", "error")
        return False


# ========================
# 刷课核心引擎
# ========================
class CourseWorker:
    """刷课引擎 - 与原版逻辑一致"""

    def __init__(self, config, log_cb, progress_cb, stop_flag_fn):
        self.token = config["token"]
        self.hw_id = config["homework_id"]
        self.lesson_ids = config["lesson_ids"]
        self.biz = config["bizcode"]
        self.log = log_cb
        self.progress_cb = progress_cb
        self._stop = stop_flag_fn

    def get_school_user_info(self):
        url = "https://gateway.ewt360.com/api/eteacherproduct/school/getSchoolUserInfo"
        headers = {"token": self.token, "Host": "gateway.ewt360.com"}
        self.log("[STEP1] 获取学校用户信息...", "info")
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"获取用户信息失败: {data}")
        d = data["data"]
        self.log(f"  -> schoolId={d['schoolId']}, userId={d['userId']}", "ok")
        return d["schoolId"], d["userId"]

    def get_lesson_detail(self, lesson_id, school_id):
        url = "https://gateway.ewt360.com/api/homeworkprod/player/getLessonDetailV2"
        headers = {
            "token": self.token,
            "Content-Type": "application/json; charset=UTF-8",
            "Host": "gateway.ewt360.com",
        }
        body = {"homeworkId": self.hw_id, "lessonId": lesson_id, "schoolId": school_id}
        self.log(f"[STEP2] 获取课程 [{lesson_id}] 详情...", "info")
        resp = requests.post(url, headers=headers, json=body, timeout=15)
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"获取课程详情失败: {data}")
        ld = data["data"]
        play_time_str = ld["playTime"]
        point_num = int(play_time_str.split(":")[0]) + 1
        self.log(f"  -> 课程: {ld.get('lessonName','N/A')}", "ok")
        self.log(f"  -> playTime={play_time_str}, point_num={point_num}", "gray")
        return point_num, ld["videoPlayTime"], ld.get("contentType", 1)

    def get_task_info(self, school_id, lesson_id, content_type):
        url = "https://gateway.ewt360.com/api/homeworkprod/homework/student/getUserHomeworkLessonTaskInfo"
        headers = {"Content-Type": "application/json", "token": self.token}
        body = {
            "schoolId": school_id, "homeworkId": self.hw_id,
            "lessonId": lesson_id, "contentType": content_type,
        }
        resp = requests.post(url, headers=headers, json=body, timeout=15)
        data = resp.json()
        if not data.get("success"):
            self.log(f"  [WARN] 获取进度失败: {data}", "warn")
            return None
        info = data["data"]
        return {
            "playTime": info["playTime"],
            "percent": info["percent"],
            "finishPlayTime": info["finishPlayTime"],
            "finishPercent": info["finishPercent"],
            "lessonTime": info["lessonTime"],
        }

    def get_player_config(self):
        url = f"https://gateway.ewt360.com/api/videoplayerprod/videoplayer/getPlayerGlobalConf?token={self.token}"
        headers = {"token": self.token, "Host": "gateway.ewt360.com"}
        self.log("[STEP3] 获取播放器配置...", "info")
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"播放器配置失败: {data}")
        gi = data["data"]["globalInfo"]
        self.log(f"  -> sessionId={gi['sessionId']}", "ok")
        self.log(f"  -> secret={gi['secret'][:8]}...", "gray")
        return gi["secret"], gi["sessionId"]

    def make_signature(self, secret, action, duration, media_time, timestamp_ms):
        raw = (
            f"action={action}&duration={duration}&mediaTime={media_time}"
            f"&mstid={self.token}&platform=2&signatureMethod=HMAC-SHA1"
            f"&signatureVersion=1.0&timestamp={timestamp_ms}&version=2022-08-02"
        )
        return hmac.new(secret.encode(), raw.encode(), hashlib.sha1).hexdigest()

    def report_video_point(self, lesson_id):
        ts = int(time.time() * 1000)
        headers = {
            "Content-Type": "application/json",
            "token": self.token,
            "timestamp": str(ts),
            "sign": hashlib.md5(f"{ts}{REPORT_KEY}".encode()).hexdigest(),
        }
        body = {
            "homeworkId": self.hw_id, "lessonId": lesson_id,
            "type": 1, "platform": 2, "seriousCheckResult": 2,
        }
        try:
            r = requests.post(REPORT_URL, json=body, headers=headers, timeout=15)
            self.log(f"  ReportPoint -> {r.status_code}", "gray")
        except Exception as e:
            self.log(f"  [ERROR] 上报异常: {e}", "error")

    def build_common_package(self, user_id, school_id):
        return {
            "os": "Android", "appBrand": "android",
            "schoolProvinceCode": "320000", "memberProvinceCode": "320000",
            "userid": str(user_id), "resolution": "1080*2306",
            "platform": "2", "appOnline": "1", "osVersion": "10",
            "appDeviceModel": "android",
            "appDevId": "0f99d6c0-693e-3f13-abef-60f6af4d9218",
            "schoolId": str(school_id), "sdkVersion": "2.0.95-test-rc21",
            "appCarrier": "N/A", "appAccess": "NETWORK_MOBILE",
            "mstid": self.token, "appLanguage": "zh",
        }

    def submit_round(self, session_id, user_id, school_id, lesson_id,
                     action, event_type, stay_time, media_time, point_time,
                     begin_time, point_num, secret):
        ts = int(time.time() * 1000)
        sig = self.make_signature(secret, action, stay_time, media_time, ts)
        url = (f"https://bfe.ewt360.com/monitor/app/collect/batch"
               f"?TrLessonId={lesson_id}&TrVideoBizCode={self.biz}"
               f"&TrUuId=12341234&TrFallback=0&TrUserId={user_id}"
               f"&token={self.token}")
        headers = {
            "token": self.token, "x-bfe-session-id": session_id,
            "Content-Type": "application/json; charset=UTF-8",
            "Host": "bfe.ewt360.com",
        }
        body = {
            "CommonPackage": self.build_common_package(user_id, school_id),
            "EventPackage": [{
                "log_id": "12341234-1234-1234-1234-123412341234",
                "course_id": lesson_id, "appVersion": "11.11.11",
                "point_time": point_time, "point_time_id": 0,
                "begin_time": begin_time, "lesson_id": lesson_id,
                "speed": 2.0, "appChannel": "android", "isonline": "1",
                "quality": "高清", "video_type": 1, "point_num": point_num,
                "event_type": event_type, "report_time": ts,
                "media_time": media_time, "action": action,
                "stay_time": stay_time, "video_bizcode": self.biz, "status": 1,
            }],
            "signature": sig,
            "sn": "moses_ewt_video_detail_2026", "_": ts,
        }
        return url, headers, body

    def process_lesson(self, lesson_id, school_id, user_id, secret, session_id, idx, total):
        self.log(f"{'='*40}", "gray")
        self.log(f"[TASK {idx}/{total}] 课程 {lesson_id}", "accent")

        try:
            point_num, video_play_time, content_type = self.get_lesson_detail(
                lesson_id, school_id
            )
        except Exception as e:
            self.log(f"  [ERROR] 课程详情失败: {e}", "error")
            return False

        task = self.get_task_info(school_id, lesson_id, content_type)
        if not task:
            self.log(f"  [WARN] 无法获取进度，跳过", "warn")
            return False

        current_play = task["playTime"]
        finish_need = task["finishPlayTime"]
        current_pct = task["percent"] * 100
        threshold_pct = task["finishPercent"] * 100
        lesson_total_ms = task["lessonTime"]

        self.log(f"  进度: {current_pct:.1f}% / 目标: {threshold_pct:.0f}%", "info")

        HEARTBEAT = 120000
        INTERVAL = 60000
        needed_rounds = math.ceil(lesson_total_ms / HEARTBEAT)

        self.log(f"  总时长: {lesson_total_ms}ms -> {needed_rounds} 轮", "accent")
        self.log(f"  预计耗时约 {needed_rounds} 分钟", "gray")

        begin_time = int(time.time() * 1000)
        last_play = current_play

        for i in range(needed_rounds):
            if self._stop():
                self.log("  ⏹ 用户中止", "warn")
                return False

            is_first = (i == 0)
            is_last = (i == needed_rounds - 1)

            if is_first and is_last:
                action, event_type = 4, "video_oper"
            elif is_first:
                action, event_type = 2, "video_oper"
            elif is_last:
                action, event_type = 4, "video"
            else:
                action, event_type = 1, "video"

            self.log(f"  [第{i+1}/{needed_rounds}轮] action={action} type={event_type}", "info")

            url, headers, body = self.submit_round(
                session_id, user_id, school_id, lesson_id,
                action, event_type, HEARTBEAT, HEARTBEAT, HEARTBEAT,
                begin_time, point_num, secret,
            )

            try:
                r = requests.post(url, headers=headers, json=body, timeout=15)
                self.log(f"    Response -> {r.status_code}", "gray")
            except Exception as e:
                self.log(f"    [ERROR] {e}", "error")

            if is_last:
                self.log("  [ACTION] 发送监测上报...", "accent")
                self.report_video_point(lesson_id)

            time.sleep(1)

            t2 = self.get_task_info(school_id, lesson_id, content_type)
            if t2:
                new_play = t2["playTime"]
                gain = new_play - last_play
                pct = t2["percent"] * 100
                if gain > 0:
                    self.log(f"    Update -> +{gain}ms | {pct:.1f}%", "ok")
                else:
                    self.log(f"    [WARN] 未增长 | {pct:.1f}%", "warn")
                last_play = new_play

            if not is_last and not self._stop():
                delay = INTERVAL + random.randint(-200, 200)
                secs = delay / 1000.0
                self.log(f"    Wait -> {secs:.0f}s", "gray")
                for _ in range(int(secs)):
                    if self._stop():
                        return False
                    time.sleep(1)
                frac = secs - int(secs)
                if frac > 0 and not self._stop():
                    time.sleep(frac)

        final = self.get_task_info(school_id, lesson_id, content_type)
        if final and final["playTime"] >= finish_need:
            self.log(f"  ✅ 课程 {lesson_id} 达标！", "ok")
            return True
        else:
            self.log(f"  [WARN] 课程 {lesson_id} 未达标", "warn")
            return False

    def run(self):
        try:
            total = len(self.lesson_ids)
            self.log(f"共 {total} 个课程任务", "accent")

            school_id, user_id = self.get_school_user_info()
            secret, session_id = self.get_player_config()

            results = []
            for idx, lid in enumerate(self.lesson_ids, 1):
                if self._stop():
                    self.log("用户中止全部任务", "warn")
                    break
                ok = self.process_lesson(lid, school_id, user_id, secret, session_id, idx, total)
                results.append((lid, ok))
                self.progress_cb(idx, total)

                if idx < total and not self._stop():
                    self.log("休息 5 秒后切换下一课...", "gray")
                    for _ in range(5):
                        if self._stop():
                            break
                        time.sleep(1)

            self.progress_cb(total, total)
            ok_count = sum(1 for _, o in results if o)
            self.log(f"✅ 全部任务执行完毕 ({ok_count}/{total} 达标)", "ok")
        except Exception as e:
            self.log(f"❌ 致命错误: {e}", "error")


# ========================
# Kivy UI 组件
# ========================

class ColoredLabel(Label):
    """带颜色级别的标签"""
    pass


class LogLine(Label):
    """日志行"""
    def __init__(self, text, level="info", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        color_map = {
            "info": COLORS["accent"],
            "ok": COLORS["green"],
            "warn": COLORS["yellow"],
            "error": COLORS["red"],
            "accent": COLORS["accent"],
            "gray": COLORS["dim"],
        }
        self.color = color_map.get(level, COLORS["text"])
        self.font_size = '12sp'
        self.font_name = 'RobotoMono'
        self.size_hint_y = None
        self.height = 22
        self.text_size = (self.width, None)
        self.halign = 'left'
        self.valign = 'middle'


class EWT360Root(BoxLayout):
    """主界面根布局"""

    status_text = StringProperty("就绪 | 请先验证授权 Key")
    progress_value = NumericProperty(0.0)
    auth_status_text = StringProperty("● 未认证")
    auth_status_color = ListProperty(COLORS["red"])
    start_disabled = BooleanProperty(True)

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref
        self.orientation = 'vertical'
        self.spacing = 4
        self.padding = [8, 8, 8, 8]
        self.bg_color = COLORS["bg"]

        self._build_ui()

    def _build_ui(self):
        # ---- 标题区 ----
        title_box = BoxLayout(
            orientation='vertical', size_hint_y=None, height=70,
            spacing=2,
        )
        title_label = Label(
            text="EWT360 刷时长工具",
            font_size='22sp', bold=True,
            color=COLORS["accent"],
            size_hint_y=None, height=34,
        )
        title_box.add_widget(title_label)

        subtitle = Label(
            text=f"BETA5.0 Android版 · John Studio (c) 2024-2026",
            font_size='12sp', color=COLORS["dim"],
            size_hint_y=None, height=20,
        )
        title_box.add_widget(subtitle)

        sep = BoxLayout(size_hint_y=None, height=2, bg_color=COLORS["border"])
        title_box.add_widget(sep)

        self.add_widget(title_box)

        # ---- 认证区 ----
        auth_card = self._make_card("🔐 联网认证")
        auth_row = BoxLayout(size_hint_y=None, height=40, spacing=6)

        key_label = Label(
            text="授权 Key:", size_hint_x=None, width=80,
            color=COLORS["text"], font_size='14sp',
        )
        auth_row.add_widget(key_label)

        self.key_input = TextInput(
            text='', password=True, multiline=False,
            size_hint_x=0.45, height=36,
            background_color=COLORS["input"],
            foreground_color=COLORS["text"],
            cursor_color=COLORS["accent"],
            font_size='14sp',
        )
        auth_row.add_widget(self.key_input)

        self.verify_btn = Button(
            text="验  证", size_hint_x=None, width=80, height=36,
            background_color=COLORS["accent"],
            color=[0, 0, 0, 1], bold=True,
            on_press=self._on_verify,
        )
        auth_row.add_widget(self.verify_btn)

        self.auth_status_label = Label(
            text="● 未认证", color=COLORS["red"],
            font_size='14sp', bold=True, size_hint_x=None, width=100,
        )
        auth_row.add_widget(self.auth_status_label)

        auth_card.add_widget(auth_row)

        # 机器码
        self.machine_code = self._gen_machine_code()
        mc_label = Label(
            text=f"机器码: {self.machine_code}",
            color=COLORS["dim"], font_size='11sp',
            size_hint_y=None, height=22, halign='left',
        )
        mc_label.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
        auth_card.add_widget(mc_label)

        self.add_widget(auth_card)

        # ---- 配置区 ----
        cfg_card = self._make_card("⚙️ 任务配置")
        cfg_items = [
            ("Token:", "token_input", True),
            ("Homework ID:", "hw_input", False),
            ("Lesson IDs\n(逗号分隔):", "lid_input", False),
            ("BizCode:", "biz_input", False),
        ]
        for label, attr, is_pwd in cfg_items:
            row = BoxLayout(size_hint_y=None, height=38, spacing=6)
            lbl = Label(
                text=label, size_hint_x=None, width=100,
                color=COLORS["text"], font_size='13sp',
            )
            row.add_widget(lbl)
            e = TextInput(
                multiline=False, password=is_pwd,
                background_color=COLORS["input"],
                foreground_color=COLORS["text"],
                cursor_color=COLORS["accent"],
                font_size='13sp', height=34,
            )
            row.add_widget(e)
            setattr(self, attr, e)
            cfg_card.add_widget(row)

        self.add_widget(cfg_card)

        # ---- 控制栏 ----
        ctrl = BoxLayout(size_hint_y=None, height=46, spacing=8)

        self.start_btn = Button(
            text="▶ 开始刷课", size_hint_x=0.3, height=42,
            background_color=COLORS["green"],
            color=[0, 0, 0, 1], bold=True, font_size='15sp',
            disabled=True,
            on_press=self._on_start,
        )
        ctrl.add_widget(self.start_btn)

        self.stop_btn = Button(
            text="■ 停止", size_hint_x=0.2, height=42,
            background_color=COLORS["red"],
            color=[1, 1, 1, 1], bold=True, font_size='15sp',
            on_press=self._on_stop,
        )
        ctrl.add_widget(self.stop_btn)

        # Kivy ProgressBar
        self.progress_bar = ProgressBar(
            max=1.0, value=0.0, size_hint_x=0.5, height=42,
        )
        # 用 canvas 自定义颜色
        with self.progress_bar.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*COLORS["border"])
            self._pb_bg = Rectangle(pos=self.progress_bar.pos, size=self.progress_bar.size)
            Color(*COLORS["accent"])
            self._pb_fg = Rectangle(pos=self.progress_bar.pos, size=(0, self.progress_bar.height))
        self.progress_bar.bind(pos=self._update_pb, size=self._update_pb)
        ctrl.add_widget(self.progress_bar)

        self.add_widget(ctrl)

        # ---- 日志区 ----
        log_card = self._make_card("📋 运行日志", expand=True)

        self.log_scroll = ScrollView(
            size_hint=(1, 1),
            scroll_type=['bars', 'content'],
            bar_width=6,
        )
        self.log_container = BoxLayout(
            orientation='vertical', size_hint_y=None, spacing=1,
        )
        self.log_container.bind(minimum_height=self.log_container.setter('height'))
        self.log_scroll.add_widget(self.log_container)
        log_card.add_widget(self.log_scroll)

        self.add_widget(log_card)

        # ---- 状态栏 ----
        self.status_bar = Label(
            text="就绪 | 请先验证授权 Key",
            size_hint_y=None, height=26,
            color=COLORS["dim"], font_size='11sp',
            halign='left', valign='middle',
        )
        self.status_bar.bind(size=lambda s, w: setattr(s, 'text_size', (w[0]-12, None)))
        self.add_widget(self.status_bar)

    def _update_pb(self, *args):
        """更新进度条外观"""
        pb = self.progress_bar
        w, h = pb.size
        x, y = pb.pos
        pct = pb.value / pb.max if pb.max > 0 else 0
        self._pb_bg.pos = (x, y)
        self._pb_bg.size = (w, h)
        self._pb_fg.pos = (x, y)
        self._pb_fg.size = (w * pct, h)

    def _make_card(self, title, expand=False):
        """创建卡片容器"""
        outer = BoxLayout(
            orientation='vertical', spacing=3,
            size_hint_y=None if not expand else 1,
        )
        if not expand:
            outer.height = 140  # 认证区高度稍后调整

        header = Label(
            text=title, size_hint_y=None, height=24,
            color=COLORS["accent"], font_size='13sp', bold=True,
            halign='left',
        )
        header.bind(size=lambda s, w: setattr(s, 'text_size', (w[0]-8, None)))
        outer.add_widget(header)

        # 内容区
        content = BoxLayout(
            orientation='vertical', spacing=3, padding=[4, 2, 4, 2],
            size_hint_y=1 if expand else None,
        )
        if not expand:
            content.height = outer.height - 28

        outer.add_widget(content)
        outer._content = content  # 保存引用

        # 调整认证区高度
        if "认证" in title:
            outer.height = 100
            content.height = outer.height - 28
        elif "配置" in title:
            outer.height = 170
            content.height = outer.height - 28

        return outer

    def add_log(self, msg, level="info"):
        """添加日志行"""
        line = LogLine(text=msg, level=level)
        # 找到日志卡片的内容区
        for child in self.children:
            if isinstance(child, BoxLayout) and hasattr(child, '_content'):
                content = child._content
                # 检查是否是日志区（有 ScrollView）
                for sub in content.children:
                    if isinstance(sub, ScrollView):
                        sub.children[0].add_widget(line)
                        # 自动滚动到底部
                        Clock.schedule_once(lambda dt: setattr(
                            sub, 'scroll_y', 0
                        ), 0.05)
                        return

    def clear_logs(self):
        for child in self.children:
            if isinstance(child, BoxLayout) and hasattr(child, '_content'):
                content = child._content
                for sub in content.children:
                    if isinstance(sub, ScrollView):
                        log_cont = sub.children[0]
                        log_cont.clear_widgets()
                        return

    def _gen_machine_code(self):
        import uuid, platform
        raw = f"{platform.node()}-{uuid.getnode()}-{platform.machine()}"
        h = hashlib.sha256(raw.encode()).digest()
        import base64
        return base64.b64encode(h).decode()[:20]

    # ---- 按钮回调 ----
    def _on_verify(self, *args):
        key = self.key_input.text.strip()
        if not key:
            self.add_log("⚠️ 请输入授权 Key", "warn")
            return

        self.verify_btn.disabled = True
        self.verify_btn.text = "验证中..."
        self.auth_status_label.text = "● 验证中..."
        self.auth_status_label.color = COLORS["yellow"]

        def on_result(ok):
            self.verify_btn.disabled = False
            self.verify_btn.text = "验  证"
            if ok:
                self.auth_status_label.text = "● 已认证"
                self.auth_status_label.color = COLORS["green"]
                self.start_btn.disabled = False
                self.status_bar.text = "已认证 | 请填写配置后开始"
            else:
                self.auth_status_label.text = "● 失败"
                self.auth_status_label.color = COLORS["red"]
                self.status_bar.text = "认证失败 | 请检查 Key"

        # 后台线程验证
        def task():
            ok = verify_key_online(key, self.app.log_manager.log)
            Clock.schedule_once(lambda dt: on_result(ok), 0)

        threading.Thread(target=task, daemon=True).start()

    def _on_start(self, *args):
        token = self.token_input.text.strip()
        hwid = self.hw_input.text.strip()
        lids_raw = self.lid_input.text.strip()
        biz = self.biz_input.text.strip()

        if not all([token, hwid, lids_raw, biz]):
            self.add_log("⚠️ 请填写所有配置项", "warn")
            return

        lids = [x.strip() for x in lids_raw.replace("，", ",").split(",") if x.strip()]
        if not lids:
            self.add_log("⚠️ 请输入有效 Lesson IDs", "warn")
            return

        cfg = {"token": token, "homework_id": hwid, "lesson_ids": lids, "bizcode": biz}
        self.app.start_worker(cfg, len(lids))

    def _on_stop(self, *args):
        self.app.stop_worker()
        self.add_log("⏹ 正在停止...", "warn")

    def update_progress(self, cur, total):
        if total > 0:
            self.progress_bar.value = cur / total
            self.status_bar.text = f"运行中... [{cur}/{total}]"
            if cur >= total:
                self.status_bar.text = "✅ 全部完成"
                self.start_btn.disabled = False
        self._update_pb()


# ========================
# 主应用
# ========================
class EWT360App(App):
    """Kivy 应用主类"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.worker = None
        self.stop_flag = False
        self.log_manager = None

    def build(self):
        self.title = f"{APP_TITLE}"
        # 设置窗口背景色
        from kivy.core.window import Window
        Window.clearcolor = COLORS["bg"]

        root = EWT360Root(app_ref=self)
        self.root = root
        self.log_manager = LogManager(self)
        root.add_log("请输入授权 Key 并点击 [验证]", "accent")
        return root

    def start_worker(self, cfg, total):
        self.stop_flag = False
        self.root.progress_bar.value = 0
        self.root.start_btn.disabled = True
        self.root.status_bar.text = f"运行中... 0/{total}"
        self.root.add_log("▶ 开始任务", "ok")

        def progress_cb(cur, total):
            Clock.schedule_once(lambda dt: self.root.update_progress(cur, total), 0)

        def log_cb(msg, level="info"):
            self.log_manager.log(msg, level)

        self.worker = CourseWorker(cfg, log_cb, progress_cb, self._is_stopped)
        threading.Thread(target=self.worker.run, daemon=True).start()

    def stop_worker(self):
        self.stop_flag = True

    def _is_stopped(self):
        return self.stop_flag


# ========================
# 启动
# ========================
if __name__ == "__main__":
    EWT360App().run()
