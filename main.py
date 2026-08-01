#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EWT360 刷时长工具 · BETA5.0 Android 版 (Buildozer 可打包版)
John Studio (c) 2024-2026 · 仅供技术学习研究
"""
import os, math, time, random, hmac, hashlib, json, threading, socket
import requests

# ============ Kivy 导入（仅保留用到的、路径确认存在的） ============
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.graphics import Color, Rectangle

# ============ 全局配置 ============
APP_TITLE = "EWT360 刷时长工具 BETA5.0"
AUTH_URL  = "https://ghproxy.net/https://raw.githubusercontent.com/JOHNCHEN-DEBUG/ewt-keys/main/keys.txt"
REPORT_URL = "https://gateway.ewt360.com/api/homeworkprod/homework/student/reportVideoPoint"
REPORT_KEY = "4dcc69ed56d6"

# 颜色（Kivy 用 0-1 浮点 RGBA）
C = {
    "bg":     (0.063, 0.075, 0.102, 1),
    "panel":  (0.086, 0.106, 0.149, 1),
    "accent": (0.0,   0.843, 1.0,   1),
    "green":  (0.180, 0.804, 0.443, 1),
    "yellow": (0.945, 0.769, 0.059, 1),
    "red":    (0.906, 0.298, 0.235, 1),
    "text":   (0.831, 0.831, 0.831, 1),
    "dim":    (0.478, 0.541, 0.604, 1),
    "input":  (0.118, 0.149, 0.220, 1),
    "border": (0.165, 0.200, 0.275, 1),
}

AUTH_LOCKED = False

# ============ 日志管理器 ============
class LogMgr:
    def __init__(self, app): self.app = app
    def log(self, msg, lvl="info"):
        Clock.schedule_once(lambda dt: self._do(msg, lvl), 0)
    def _do(self, msg, lvl):
        if self.app and self.app.root:
            self.app.root.add_log(msg, lvl)

# ============ 认证 ============
def check_inet():
    try: socket.create_connection(("8.8.8.8", 53), timeout=3); return True
    except: return False

def verify_key_online(key, log):
    global AUTH_LOCKED
    if not check_inet():
        log("❌ 无法联网，认证服务器不可达", "error"); return False
    try:
        log("🔐 正在连接认证服务器...", "accent")
        r = requests.get(AUTH_URL, timeout=15)
        if r.status_code != 200:
            log(f"❌ 服务器响应异常: {r.status_code}", "error"); return False
        keys = {k.strip() for k in r.text.splitlines() if k.strip()}
        if key in keys:
            log("✅ 授权验证成功！", "ok"); AUTH_LOCKED = True; return True
        log("❌ 授权 Key 无效或被禁用", "error"); return False
    except Exception as e:
        log(f"❌ 认证请求失败: {e}", "error"); return False

# ============ 刷课引擎（核心逻辑保持不变） ============
class CourseWorker:
    def __init__(self, cfg, log_cb, prog_cb, stop_fn):
        self.token = cfg["token"]; self.hw = cfg["homework_id"]
        self.lids = cfg["lesson_ids"]; self.biz = cfg["bizcode"]
        self.log = log_cb; self.prog = prog_cb; self._stop = stop_fn

    def get_user(self):
        url = "https://gateway.ewt360.com/api/eteacherproduct/school/getSchoolUserInfo"
        r = requests.get(url, headers={"token": self.token}, timeout=15).json()
        if not r.get("success"): raise RuntimeError(r)
        d = r["data"]
        self.log(f"  -> schoolId={d['schoolId']}, userId={d['userId']}", "ok")
        return d["schoolId"], d["userId"]

    def lesson_detail(self, lid, sid):
        url = "https://gateway.ewt360.com/api/homeworkprod/player/getLessonDetailV2"
        body = {"homeworkId": self.hw, "lessonId": lid, "schoolId": sid}
        r = requests.post(url, headers={"token": self.token, "Content-Type": "application/json"}, json=body, timeout=15).json()
        if not r.get("success"): raise RuntimeError(r)
        d = r["data"]
        pt = d["playTime"].split(":"); pts = int(pt[0]) + 1
        self.log(f"  -> {d.get('lessonName','')}, points={pts}", "ok")
        return pts, d.get("videoPlayTime"), d.get("contentType", 1)

    def task_info(self, sid, lid, ct):
        url = "https://gateway.ewt360.com/api/homeworkprod/homework/student/getUserHomeworkLessonTaskInfo"
        body = {"schoolId": sid, "homeworkId": self.hw, "lessonId": lid, "contentType": ct}
        r = requests.post(url, headers={"token": self.token, "Content-Type": "application/json"}, json=body, timeout=15).json()
        if not r.get("success"): self.log(f"  [WARN] {r}", "warn"); return None
        i = r["data"]
        return {"playTime": i["playTime"], "percent": i["percent"],
                "finishPlayTime": i["finishPlayTime"], "finishPercent": i["finishPercent"],
                "lessonTime": i["lessonTime"]}

    def player_cfg(self):
        url = f"https://gateway.ewt360.com/api/videoplayerprod/videoplayer/getPlayerGlobalConf?token={self.token}"
        r = requests.get(url, headers={"token": self.token}, timeout=15).json()
        if not r.get("success"): raise RuntimeError(r)
        g = r["data"]["globalInfo"]
        self.log(f"  -> sessionId={g['sessionId']}", "ok")
        return g["secret"], g["sessionId"]

    def sign(self, secret, action, dur, mt, ts):
        raw = f"action={action}&duration={dur}&mediaTime={mt}&mstid={self.token}&platform=2&signatureMethod=HMAC-SHA1&signatureVersion=1.0&timestamp={ts}&version=2022-08-02"
        return hmac.new(secret.encode(), raw.encode(), hashlib.sha1).hexdigest()

    def report(self, lid):
        ts = int(time.time()*1000)
        h = {"token": self.token, "timestamp": str(ts),
             "sign": hashlib.md5(f"{ts}{REPORT_KEY}".encode()).hexdigest(),
             "Content-Type": "application/json"}
        body = {"homeworkId": self.hw, "lessonId": lid, "type": 1, "platform": 2, "seriousCheckResult": 2}
        try: requests.post(REPORT_URL, json=body, headers=h, timeout=15)
        except Exception as e: self.log(f"  [ERROR] 上报: {e}", "error")

    def common_pkg(self, uid, sid):
        return {"os":"Android","appBrand":"android","schoolProvinceCode":"320000",
                "memberProvinceCode":"320000","userid":str(uid),"resolution":"1080 * 2306",
                "platform":"2","appOnline":"1","osVersion":"10","appDeviceModel":"android",
                "appDevId":"0f99d6c0-693e-3f13-abef-60f6af4d9218","schoolId":str(sid),
                "sdkVersion":"2.0.95-test-rc21","appCarrier":"N/A","appAccess":"NETWORK_MOBILE",
                "mstid":self.token,"appLanguage":"zh"}

    def run(self):
        try:
            total = len(self.lids)
            self.log(f"共 {total} 个课程任务", "accent")
            sid, uid = self.get_user()
            secret, sess = self.player_cfg()
            ok_n = 0
            for idx, lid in enumerate(self.lids, 1):
                if self._stop(): self.log("用户中止","warn"); break
                self.log(f"{'='*40}","gray")
                self.log(f"[TASK {idx}/{total}] {lid}","accent")
                try:
                    pts, _, ct = self.lesson_detail(lid, sid)
                except Exception as e:
                    self.log(f"  [ERROR] 详情失败: {e}","error"); continue
                t = self.task_info(sid, lid, ct)
                if not t: continue
                cur = t["playTime"]; need = t["finishPlayTime"]
                pct = t["percent"]*100; thr = t["finishPercent"]*100
                self.log(f"  进度: {pct:.1f}% / 目标: {thr:.0f}%","info")
                HB = 120000; INTER = 60000
                rounds = math.ceil(t["lessonTime"] / HB)
                self.log(f"  {rounds} 轮，约 {rounds} 分钟","gray")
                begin = int(time.time()*1000); last = cur
                for i in range(rounds):
                    if self._stop(): break
                    first = (i==0); last_r = (i==rounds-1)
                    if first and last_r: act, et = 4, "video_oper"
                    elif first: act, et = 2, "video_oper"
                    elif last_r: act, et = 4, "video"
                    else: act, et = 1, "video"
                    self.log(f"  [第{i+1}/{rounds}轮] act={act}","info")
                    ts = int(time.time()*1000)
                    sig = self.sign(secret, act, HB, HB, ts)
                    url = (f"https://bfe.ewt360.com/monitor/app/collect/batch"
                           f"?TrLessonId={lid}&TrVideoBizCode={self.biz}"
                           f"&TrUuId=12341234&TrFallback=0&TrUserId={uid}"
                           f"&token={self.token}")
                    hdr = {"token":self.token,"x-bfe-session-id":sess,
                           "Content-Type":"application/json; charset=UTF-8"}
                    body = {"CommonPackage":self.common_pkg(uid,sid),
                            "EventPackage":[{"log_id":"12341234-1234-1234-1234-123412341234",
                                            "course_id":lid,"appVersion":"11.11.11",
                                            "point_time":HB,"point_time_id":0,
                                            "begin_time":begin,"lesson_id":lid,
                                            "speed":2.0,"appChannel":"android","isonline":"1",
                                            "quality":"高清","video_type":1,"point_num":pts,
                                            "event_type":et,"report_time":ts,
                                            "media_time":HB,"action":act,
                                            "stay_time":HB,"video_bizcode":self.biz,"status":1}],
                            "signature":sig,"sn":"moses_ewt_video_detail_2026","_":ts}
                    try: requests.post(url, headers=hdr, json=body, timeout=15)
                    except Exception as e: self.log(f"    [E] {e}","error")
                    if last_r: self.report(lid)
                    time.sleep(1)
                    t2 = self.task_info(sid, lid, ct)
                    if t2:
                        g = t2["playTime"]-last; pct2 = t2["percent"]*100
                        self.log(f"    +{g}ms | {pct2:.1f}%","ok" if g>0 else "warn")
                        last = t2["playTime"]
                    if not last_r and not self._stop():
                        d = INTERVAL = INTER + random.randint(-200,200)
                        for _ in range(d//1000):
                            if self._stop(): break
                            time.sleep(1)
                final = self.task_info(sid, lid, ct)
                ok = final and final["playTime"] >= need
                if ok: ok_n+=1; self.log(f"  ✅ {lid} 达标","ok")
                else: self.log(f"  [WARN] {lid} 未达标","warn")
                self.prog(idx, total)
                if idx<total and not self._stop():
                    self.log("休息5秒...","gray")
                    for _ in range(5):
                        if self._stop(): break
                        time.sleep(1)
            self.prog(total, total)
            self.log(f"✅ 完成 ({ok_n}/{total} 达标)","ok")
        except Exception as e:
            self.log(f"❌ 致命错误: {e}","error")

# ============ UI ============
class LogLine(Label):
    def __init__(self, text, level="info", **kw):
        super().__init__(**kw)
        self.text = text
        self.color = {"info":C["accent"],"ok":C["green"],"warn":C["yellow"],
                      "error":C["red"],"accent":C["accent"],"gray":C["dim"]}.get(level, C["text"])
        self.font_size = "12sp"; self.size_hint_y = None; self.height = 22
        self.halign = "left"; self.valign = "middle"

class Root(BoxLayout):
    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app; self.orientation = "vertical"
        self.spacing = 4; self.padding = 8
        self.bg_color = C["bg"]
        self._build()

    def _build(self):
        # 标题
        t = Label(text="EWT360 刷时长工具", font_size="22sp", bold=True,
                  color=C["accent"], size_hint_y=None, height=34)
        self.add_widget(t)
        self.add_widget(Label(text="BETA5.0 Android · John Studio", font_size="12sp",
                              color=C["dim"], size_hint_y=None, height=20))
        self.add_widget(BoxLayout(size_hint_y=None, height=2,
                                  canvas_before=[Color(*C["border"]),
                                                Rectangle(pos=self.pos, size=self.size)]))
        # 认证
        self.add_widget(Label(text="🔐 联网认证", color=C["accent"], size_hint_y=None, height=24))
        row = BoxLayout(size_hint_y=None, height=40, spacing=6)
        row.add_widget(Label(text="授权Key:", size_hint_x=None, width=80, color=C["text"]))
        self.key_in = TextInput(password=True, multiline=False, size_hint_x=0.45, height=36,
                                background_color=C["input"], foreground_color=C["text"],
                                cursor_color=C["accent"])
        row.add_widget(self.key_in)
        self.vbtn = Button(text="验  证", size_hint_x=None, width=80, height=36,
                            background_color=C["accent"], color=(0,0,0,1), bold=True,
                            on_press=self._verify)
        row.add_widget(self.vbtn)
        self.astat = Label(text="● 未认证", color=C["red"], size_hint_x=None, width=100)
        row.add_widget(self.astat)
        self.add_widget(row)
        self.mc = hashlib.sha256(os.urandom(16)).hexdigest()[:20]
        self.add_widget(Label(text=f"机器码: {self.mc}", color=C["dim"],
                              font_size="11sp", size_hint_y=None, height=22))
        # 配置
        self.add_widget(Label(text="⚙️ 任务配置", color=C["accent"], size_hint_y=None, height=24))
        self.cfg = {}
        for lab, attr in [("Token:","tok"),("HomeworkID:","hw"),
                          ("LessonIDs(逗号):","lid"),("BizCode:","biz")]:
            r = BoxLayout(size_hint_y=None, height=38, spacing=6)
            r.add_widget(Label(text=lab, size_hint_x=None, width=100, color=C["text"]))
            e = TextInput(multiline=False, background_color=C["input"],
                          foreground_color=C["text"], cursor_color=C["accent"], height=34)
            r.add_widget(e); setattr(self, attr, e)
            self.cfg[attr] = e
            self.add_widget(r)
        # 控制
        ctrl = BoxLayout(size_hint_y=None, height=46, spacing=8)
        self.sbtn = Button(text="▶ 开始", size_hint_x=0.3, height=42,
                            background_color=C["green"], color=(0,0,0,1), bold=True,
                            disabled=True, on_press=self._start)
        ctrl.add_widget(self.sbtn)
        ctrl.add_widget(Button(text="■ 停止", size_hint_x=0.2, height=42,
                                background_color=C["red"], color=(1,1,1,1), bold=True,
                                on_press=self._stop))
        self.pb = ProgressBar(max=1.0, value=0.0, size_hint_x=0.5, height=42)
        ctrl.add_widget(self.pb)
        self.add_widget(ctrl)
        # 日志
        self.add_widget(Label(text="📋 运行日志", color=C["accent"], size_hint_y=None, height=24))
        sv = ScrollView(size_hint=(1,1), bar_width=6)
        self.lc = BoxLayout(orientation="vertical", size_hint_y=None, spacing=1)
        self.lc.bind(minimum_height=self.lc.setter("height"))
        sv.add_widget(self.lc)
        self.add_widget(sv)
        # 状态栏
        self.sb = Label(text="就绪 | 请先验证授权 Key", size_hint_y=None, height=26,
                         color=C["dim"], font_size="11sp")
        self.add_widget(self.sb)

    def add_log(self, msg, lvl):
        self.lc.add_widget(LogLine(msg, lvl))
        Clock.schedule_once(lambda dt: setattr(self.lc.parent, "scroll_y", 0), 0.05)

    def _verify(self, *_):
        key = self.key_in.text.strip()
        if not key: self.add_log("⚠️ 请输入Key","warn"); return
        self.vbtn.disabled = True; self.vbtn.text = "验证中..."
        self.astat.text = "● 验证中..."; self.astat.color = C["yellow"]
        def task():
            ok = verify_key_online(key, self.app.log_mgr.log)
            Clock.schedule_once(lambda dt: self._on_v(ok), 0)
        threading.Thread(target=task, daemon=True).start()

    def _on_v(self, ok):
        self.vbtn.disabled = False; self.vbtn.text = "验  证"
        if ok:
            self.astat.text = "● 已认证"; self.astat.color = C["green"]
            self.sbtn.disabled = False; self.sb.text = "已认证 | 请填写配置后开始"
        else:
            self.astat.text = "● 失败"; self.astat.color = C["red"]
            self.sb.text = "认证失败 | 请检查 Key"

    def _start(self, *_):
        tok = self.tok.text.strip(); hw = self.hw.text.strip()
        lids = [x.strip() for x in self.lid.text.replace("，",",").split(",") if x.strip()]
        biz = self.biz.text.strip()
        if not all([tok,hw,lids,biz]): self.add_log("⚠️ 配置不全","warn"); return
        self.sbtn.disabled = True; self.pb.value = 0
        self.sb.text = f"运行中... 0/{len(lids)}"
        self.add_log("▶ 开始任务","ok")
        cfg = {"token":tok,"homework_id":hw,"lesson_ids":lids,"bizcode":biz}
        self.app.start(cfg, len(lids))

    def _stop(self, *_):
        self.app.stop(); self.add_log("⏹ 停止中","warn")

    def set_prog(self, cur, tot):
        self.pb.value = cur/tot if tot else 0
        self.sb.text = f"运行中... [{cur}/{tot}]" if cur<tot else "✅ 完成"

# ============ App ============
class EWTApp(App):
    def build(self):
        from kivy.core.window import Window
        Window.clearcolor = C["bg"]
        self.title = APP_TITLE
        self.root = Root(app=self); self.log_mgr = LogMgr(self)
        self.worker = None; self.stop_flag = False
        self.root.add_log("请输入授权 Key 并点击 [验证]","accent")
        return self.root

    def start(self, cfg, tot):
        self.stop_flag = False
        def prog(c,t): Clock.schedule_once(lambda dt: self.root.set_prog(c,t),0)
        self.worker = CourseWorker(cfg, self.log_mgr.log, prog, lambda: self.stop_flag)
        threading.Thread(target=self.worker.run, daemon=True).start()

    def stop(self): self.stop_flag = True

if __name__ == "__main__":
    EWTApp().run()
