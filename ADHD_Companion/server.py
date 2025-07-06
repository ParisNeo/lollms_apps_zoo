import sqlite3
import datetime
import os
import sys
import math
import threading
import time
from typing import Optional, Dict, List, Tuple

# Pipmaster and package imports (unchanged)
try:
    import pipmaster as pm
    pm.ensure_packages(["plyer","playsound","PyQt5"])
except ImportError:
    print("pipmaster not found. Please install it: pip install pipmaster")
    pass

try:
    from plyer import notification as plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("Plyer library not found. Desktop notifications disabled.")

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False
    print("playsound library not found. Timer sounds disabled.")

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QDesktopWidget, QProgressBar, QGraphicsOpacityEffect,
    QMainWindow, QListWidget, QListWidgetItem, QDialog, QLineEdit,
    QTextEdit, QSpinBox, QDialogButtonBox, QFormLayout, QMessageBox,
    QComboBox, QDateEdit, QAbstractItemView, QSizePolicy, QSpacerItem, QFrame,
    QCheckBox # For Dark Mode Toggle
)
from PyQt5.QtCore import (
    QCoreApplication,
    Qt, QTimer, QPoint, QSize, pyqtSignal, QEvent,
    QPropertyAnimation, QEasingCurve, QDate, QSettings, QObject,
    pyqtSlot, QRect
)
from PyQt5.QtGui import QCursor, QFont, QColor, QIcon, QPalette, QGuiApplication # Added QPalette, QGuiApplication

DATABASE_URL = "./adhd_app.db"
BELL_MP3_PATH_ABS = ""

# --- Constants & Global Theme Setting ---
SKIP_BREAK_PENALTY_POINTS = 5
POINTS_PER_POMODORO_COMPLETION = 1
DEFAULT_WORK_DURATION_MIN = 25
DEFAULT_BREAK_DURATION_MIN = 5
MAX_CONSECUTIVE_SESSIONS = 3

# Global theme state
THEME_LIGHT = "light"
THEME_DARK = "dark"
CURRENT_THEME = THEME_LIGHT # Default, will be loaded from QSettings

backend_pomodoro_instance: Optional['BackendPomodoroManager'] = None
main_app_window_instance: Optional['FocusHubApp'] = None
mini_timer_window_instance: Optional['MiniTimerDisplayWindow'] = None

# --- Theme Helper Functions ---
def set_current_theme(theme_name: str):
    global CURRENT_THEME
    CURRENT_THEME = theme_name
    settings = QSettings()
    settings.setValue("currentTheme", theme_name)
    # Notify windows to update their styles
    if main_app_window_instance:
        main_app_window_instance.apply_styles() # Re-apply styles
        main_app_window_instance.load_tasks() # Re-render task items with new theme
    if mini_timer_window_instance:
        # Mini timer already updates styles based on its internal logic and cached state
        # We just need to trigger a re-evaluation that considers CURRENT_THEME
        mini_timer_window_instance.on_backend_state_updated(mini_timer_window_instance._cached_backend_state)


def load_current_theme():
    global CURRENT_THEME
    settings = QSettings()
    theme = settings.value("currentTheme", THEME_LIGHT)
    CURRENT_THEME = theme if theme in [THEME_LIGHT, THEME_DARK] else THEME_LIGHT


# --- Database Helper (Unchanged, except for config load/save) ---
def get_db():
    db = sqlite3.connect(DATABASE_URL)
    db.row_factory = sqlite3.Row
    return db

def init_db(): # Unchanged
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT,
        due_date TEXT, status TEXT DEFAULT 'todo', pomodoros_completed INTEGER DEFAULT 0,
        pomodoros_estimated INTEGER DEFAULT 1, points_value INTEGER DEFAULT 10,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    try: cursor.execute("SELECT points_value FROM tasks LIMIT 1")
    except sqlite3.OperationalError: cursor.execute("ALTER TABLE tasks ADD COLUMN points_value INTEGER DEFAULT 10")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY CHECK (id = 1), total_points INTEGER DEFAULT 0,
        work_duration_min INTEGER, break_duration_min INTEGER, max_consecutive_sessions INTEGER
    )""")
    cursor.execute("SELECT COUNT(*) FROM user_stats WHERE id = 1")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO user_stats (id, total_points, work_duration_min, break_duration_min, max_consecutive_sessions) 
            VALUES (1, 0, ?, ?, ?)
        """, (DEFAULT_WORK_DURATION_MIN, DEFAULT_BREAK_DURATION_MIN, MAX_CONSECUTIVE_SESSIONS))
    conn.commit(); conn.close()

def update_user_points_in_db(db_conn: sqlite3.Connection, points_to_add: int) -> int: # Unchanged
    cursor = db_conn.cursor(); cursor.execute("INSERT OR IGNORE INTO user_stats (id, total_points) VALUES (1, (SELECT total_points FROM user_stats WHERE id=1))"); cursor.execute("SELECT total_points FROM user_stats WHERE id = 1")
    current_points = (row["total_points"] if (row := cursor.fetchone()) else 0)
    new_points = max(0, current_points + points_to_add); cursor.execute("UPDATE user_stats SET total_points = ? WHERE id = 1", (new_points,)); db_conn.commit(); return new_points

def load_pomodoro_config_from_db() -> Dict: # Unchanged
    try:
        with get_db() as conn:
            cursor = conn.cursor(); cursor.execute("SELECT work_duration_min, break_duration_min, max_consecutive_sessions FROM user_stats WHERE id = 1")
            if (row := cursor.fetchone()) and row["work_duration_min"] is not None:
                return {"work_duration_min": row["work_duration_min"], "break_duration_min": row["break_duration_min"], "max_consecutive_sessions": row["max_consecutive_sessions"], "skip_break_penalty": SKIP_BREAK_PENALTY_POINTS}
    except Exception as e: print(f"Error loading pomodoro config: {e}")
    return {"work_duration_min": DEFAULT_WORK_DURATION_MIN, "break_duration_min": DEFAULT_BREAK_DURATION_MIN, "max_consecutive_sessions": MAX_CONSECUTIVE_SESSIONS, "skip_break_penalty": SKIP_BREAK_PENALTY_POINTS}


# --- Backend Pomodoro Manager (Unchanged from previous deadlock fix version) ---
class BackendPomodoroManager(QObject):
    timer_state_updated = pyqtSignal(dict)
    points_globally_updated = pyqtSignal(int)
    request_ui_refresh = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.timer_thread = None; self.is_running = False; self.is_break = False
        self.current_task_id: Optional[int] = None; self.current_task_title: str = "No Task"
        self.consecutive_focus_sessions = 0; self.internal_lock = threading.Lock()
        self.config = load_pomodoro_config_from_db()
        self.time_left_seconds = self.config['work_duration_min'] * 60
        self.total_duration_seconds = self.config['work_duration_min'] * 60
        self._prepare_and_emit_state()

    def _get_current_status_dict_unsafe(self) -> Dict: # Unchanged
        minutes, seconds = divmod(self.time_left_seconds, 60); time_str = f"{minutes:02d}:{seconds:02d}"; state_str = "Idle"
        task_display = self.current_task_title
        if not self.current_task_id and self.current_task_title == "No Task": task_display = "General Focus"
        elif self.is_break: task_display = "On Break"
        if self.is_running: state_str = "On Break" if self.is_break else f"Focus: {task_display}"
        else:
            if self.time_left_seconds == 0: state_str = f"Break Over. Ready for {self.current_task_title if self.current_task_id else 'General Focus'}?" if self.is_break else "Focus Over. Time for a break!"
            elif self.is_break: state_str = "Ready for Break" if self.time_left_seconds == self.config['break_duration_min']*60 else "Paused (Break)"
            else: state_str = f"Ready: {task_display}" if self.time_left_seconds == self.config['work_duration_min']*60 else f"Paused (Focus on {task_display})"
        return {"is_running_from_widget":self.is_running,"is_break":self.is_break,"numeric_timeLeft":self.time_left_seconds,"numeric_totalTime":self.total_duration_seconds,"time_str":time_str,"current_task_id":self.current_task_id,"task_title":self.current_task_title,"consecutive_focus_sessions":self.consecutive_focus_sessions,"state_str":state_str,"max_consecutive_sessions":self.config['max_consecutive_sessions']}

    def _prepare_and_emit_state(self): # Unchanged
        with self.internal_lock: status_dict = self._get_current_status_dict_unsafe()
        self.timer_state_updated.emit(status_dict)

    def _tick(self): # Unchanged
        should_continue, session_completed = False, False
        with self.internal_lock:
            if not self.is_running: self._stop_timer_thread_unsafe(); return
            self.time_left_seconds -= 1
            if self.time_left_seconds < 0: self.time_left_seconds = 0; self.is_running = False; session_completed = True
            should_continue = self.is_running
        self._prepare_and_emit_state()
        if session_completed: self._handle_session_completion()
        elif should_continue: self.timer_thread = threading.Timer(1.0,self._tick); self.timer_thread.daemon=True; self.timer_thread.start()
        else: 
            with self.internal_lock: self._stop_timer_thread_unsafe()

    def _stop_timer_thread_unsafe(self): # Unchanged
        if self.timer_thread and self.timer_thread.is_alive(): self.timer_thread.cancel()
        self.timer_thread = None

    def _play_sound_notification(self): # Unchanged
        if PLAYSOUND_AVAILABLE and BELL_MP3_PATH_ABS and os.path.exists(BELL_MP3_PATH_ABS):
            try: threading.Thread(target=playsound,args=(BELL_MP3_PATH_ABS,),daemon=True).start()
            except Exception as e: print(f"Sound error: {e}")

    def _send_desktop_notification(self, title, message): # Unchanged
        if PLYER_AVAILABLE:
            try: plyer_notification.notify(title=title,message=message,app_name="Focus Hub",timeout=15)
            except Exception as e: print(f"Notification error: {e}")

    def _handle_session_completion(self): # Unchanged
        self._play_sound_notification(); was_break = False
        with self.internal_lock: was_break = self.is_break
        if not was_break:
            self.consecutive_focus_sessions += 1; new_total_points = None
            try:
                with get_db() as db_conn:
                    if self.current_task_id: db_conn.execute("UPDATE tasks SET pomodoros_completed=pomodoros_completed+1,updated_at=? WHERE id=?",(datetime.datetime.now(datetime.timezone.utc).isoformat(),self.current_task_id))
                    new_total_points = update_user_points_in_db(db_conn, POINTS_PER_POMODORO_COMPLETION)
                if new_total_points is not None: self.points_globally_updated.emit(new_total_points)
            except sqlite3.Error as e: print(f"DB error on pomo completion: {e}")
            title="Focus Complete!"; msg=f"Break time ({self.config['break_duration_min']} min)."
            if self.consecutive_focus_sessions >= self.config['max_consecutive_sessions']: msg+=f"\nMandatory break after {self.consecutive_focus_sessions} sessions!"
            self._send_desktop_notification(title,msg)
            with self.internal_lock: self.is_break=True; self.is_running=True; self.time_left_seconds=self.config['break_duration_min']*60; self.total_duration_seconds=self.time_left_seconds; self._stop_timer_thread_unsafe()
            self.timer_thread=threading.Timer(0.01,self._tick); self.timer_thread.daemon=True; self.timer_thread.start(); self.request_ui_refresh.emit()
        else:
            self._send_desktop_notification("Break Over!","Time for more focus!")
            with self.internal_lock: self.is_break=False; self.is_running=False; self.time_left_seconds=self.config['work_duration_min']*60; self.total_duration_seconds=self.time_left_seconds;
            if not self.current_task_id and self.current_task_title!="General Focus": self.current_task_title="General Focus"
        self._prepare_and_emit_state()

    @pyqtSlot(object, object)
    def start_focus(self, task_id: Optional[int] = None, task_title: Optional[str] = None): # Unchanged
        new_total_pts_penalty=None; penalty_applied=False
        with self.internal_lock:
            if self.is_running and not self.is_break:
                if task_id==self.current_task_id and (task_title==self.current_task_title or (not task_id and not self.current_task_id and (task_title=="General Focus" or self.current_task_title=="General Focus"))): self._prepare_and_emit_state(); return
                self._stop_timer_thread_unsafe()
            if self.is_break:
                if self.consecutive_focus_sessions >= self.config['max_consecutive_sessions']:
                    try: 
                        with get_db() as db: new_total_pts_penalty=update_user_points_in_db(db, -abs(self.config['skip_break_penalty']))
                        penalty_applied=True
                    except sqlite3.Error as e: print(f"DB error on skip penalty: {e}")
                self.consecutive_focus_sessions=0
            self.is_running=True; self.is_break=False; self.time_left_seconds=self.config['work_duration_min']*60; self.total_duration_seconds=self.time_left_seconds
            self.current_task_id=task_id; self.current_task_title=task_title if task_title else "General Focus"
            if self.current_task_title in ["On Break","Task Completed!","No Task"]: self.current_task_title="General Focus"
            self._stop_timer_thread_unsafe(); self.timer_thread=threading.Timer(0.01,self._tick); self.timer_thread.daemon=True; self.timer_thread.start()
        self._prepare_and_emit_state()
        if penalty_applied and new_total_pts_penalty is not None:
            self.points_globally_updated.emit(new_total_pts_penalty); self._send_desktop_notification("Mandatory Break Skipped",f"-{self.config['skip_break_penalty']} pts."); self.request_ui_refresh.emit()

    @pyqtSlot()
    def start_break(self): # Unchanged
        with self.internal_lock:
            if self.is_running and self.is_break: self._prepare_and_emit_state(); return
            self.is_running=True; self.is_break=True; self.time_left_seconds=self.config['break_duration_min']*60; self.total_duration_seconds=self.time_left_seconds; self._stop_timer_thread_unsafe()
            self.timer_thread=threading.Timer(0.01,self._tick); self.timer_thread.daemon=True; self.timer_thread.start()
        self._prepare_and_emit_state()

    @pyqtSlot()
    def pause(self): # Unchanged
        with self.internal_lock:
            if not self.is_running: self._prepare_and_emit_state(); return
            self.is_running=False; self._stop_timer_thread_unsafe()
        self._prepare_and_emit_state()

    @pyqtSlot()
    def resume(self): # Unchanged
        with self.internal_lock:
            if self.is_running or self.time_left_seconds==0: self._prepare_and_emit_state(); return
            self.is_running=True; self._stop_timer_thread_unsafe(); self.timer_thread=threading.Timer(0.01,self._tick); self.timer_thread.daemon=True; self.timer_thread.start()
        self._prepare_and_emit_state()

    @pyqtSlot()
    def reset(self): # Unchanged
        with self.internal_lock:
            self.is_running=False; self._stop_timer_thread_unsafe(); self.is_break=False; self.time_left_seconds=self.config['work_duration_min']*60; self.total_duration_seconds=self.time_left_seconds
            if not self.current_task_id: self.current_task_title="No Task"
            self.consecutive_focus_sessions=0
        self._prepare_and_emit_state()

    @pyqtSlot(int, str)
    def select_task(self, task_id: int, task_title: str): # Unchanged
        with self.internal_lock:
            self.current_task_id=task_id; self.current_task_title=task_title
            if not self.is_running and not self.is_break: self.time_left_seconds=self.config['work_duration_min']*60; self.total_duration_seconds=self.time_left_seconds
        self._prepare_and_emit_state(); print(f"Backend: Selected Task '{task_title}'.")

    def complete_current_task_early(self): # Unchanged
        task_id_to_complete=None
        with self.internal_lock:
            if self.current_task_id and not self.is_break: task_id_to_complete=self.current_task_id
        if not task_id_to_complete: return
        with self.internal_lock:
            if self.current_task_id==task_id_to_complete and not self.is_break:
                original_is_running=self.is_running
                if self.is_running: self._stop_timer_thread_unsafe(); self._play_sound_notification()
                self.is_break=True; self.is_running=True; self.time_left_seconds=self.config['break_duration_min']*60; self.total_duration_seconds=self.time_left_seconds
                if original_is_running: self.consecutive_focus_sessions+=1
                self._stop_timer_thread_unsafe(); self.timer_thread=threading.Timer(0.01,self._tick); self.timer_thread.daemon=True; self.timer_thread.start()
                self._send_desktop_notification("Focus Session Ended Early",f"Task '{self.current_task_title}' done. Break time!")
            elif self.current_task_id==task_id_to_complete and self.is_break: pass
        self._prepare_and_emit_state()

    @pyqtSlot(int)
    def trigger_points_update_signal(self, new_total_points: int): self.points_globally_updated.emit(new_total_points) # Unchanged
    @pyqtSlot()
    def trigger_ui_refresh_signal(self): self.request_ui_refresh.emit() # Unchanged
    @pyqtSlot(dict)
    def update_configuration(self, new_config: Dict): # Unchanged
        with self.internal_lock:
            self.config["work_duration_min"]=new_config.get("work_duration_min",self.config["work_duration_min"]); self.config["break_duration_min"]=new_config.get("break_duration_min",self.config["break_duration_min"]); self.config["max_consecutive_sessions"]=new_config.get("max_consecutive_sessions",self.config["max_consecutive_sessions"])
            if not self.is_running:
                if self.is_break: self.time_left_seconds=self.config['break_duration_min']*60
                else: self.time_left_seconds=self.config['work_duration_min']*60
                self.total_duration_seconds=self.time_left_seconds
            try:
                with get_db() as conn: conn.execute("UPDATE user_stats SET work_duration_min=?,break_duration_min=?,max_consecutive_sessions=? WHERE id=1",(self.config["work_duration_min"],self.config["break_duration_min"],self.config["max_consecutive_sessions"]))
            except Exception as e: print(f"Error saving config to DB: {e}")
        self._prepare_and_emit_state(); print("Config updated.")


# --- MiniTimerDisplayWindow (Theme aware styles) ---
class MiniTimerDisplayWindow(QWidget):
    request_backend_start_focus = pyqtSignal(object, object) 
    request_backend_start_break = pyqtSignal()
    request_backend_pause = pyqtSignal()
    request_backend_resume = pyqtSignal()
    request_backend_reset = pyqtSignal()

    NORMAL_HEIGHT = 145; SHRUNKEN_HEIGHT = 85 
    NORMAL_OPACITY = 0.92; SHRUNKEN_OPACITY = 0.75

    def __init__(self): # Unchanged setup
        super().__init__(); self.drag_position=QPoint(); self.is_expanded=False; self._task_id_for_next_focus=None; self._task_title_for_next_focus="General Focus"; self._cached_backend_state={}
        self.opacity_animation=QPropertyAnimation(self,b"windowOpacity"); self.opacity_animation.setDuration(200); self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.height_animation=QPropertyAnimation(self,b"minimumHeight"); self.height_animation.setDuration(200); self.height_animation.setEasingCurve(QEasingCurve.InOutQuad); self.height_animation.finished.connect(self.adjustSize)
        self.initUI(); self.set_shrunken_state(True,animate=False); self.load_position()

    def initUI(self): # Unchanged UI elements
        self.setWindowTitle("Focus Timer"); self.setWindowFlags(Qt.Tool|Qt.WindowStaysOnTopHint|Qt.FramelessWindowHint|Qt.NoDropShadowWindowHint); self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_Hover)
        self.main_layout=QVBoxLayout(); self.main_layout.setContentsMargins(0,0,0,0); self.main_layout.setSpacing(0)
        self.drag_handle_widget=QFrame(); self.drag_handle_widget.setFixedHeight(18); self.drag_handle_widget.setObjectName("dragHandle"); self.drag_handle_widget.setFrameShape(QFrame.NoFrame)
        self.content_widget=QFrame(); self.content_widget.setObjectName("contentWidget"); self.content_widget.setFrameShape(QFrame.NoFrame)
        content_layout_wrapper=QVBoxLayout(self.content_widget); content_layout_wrapper.setContentsMargins(8,5,8,8); content_layout_wrapper.setSpacing(3)
        self.task_label=QLabel("No Task"); self.task_label.setAlignment(Qt.AlignCenter); self.task_label.setFont(QFont("Arial",10,QFont.Bold)); self.task_label.setWordWrap(True); self.task_label.setObjectName("taskLabel")
        self.time_label=QLabel("00:00"); self.time_label.setAlignment(Qt.AlignCenter); self.time_label.setFont(QFont("Arial",26,QFont.Bold)); self.time_label.setObjectName("timeLabel")
        self.progress_bar=QProgressBar(); self.progress_bar.setFixedHeight(8); self.progress_bar.setTextVisible(False); self.progress_bar.setObjectName("progressBar")
        self.state_label=QLabel("Idle"); self.state_label.setAlignment(Qt.AlignCenter); self.state_label.setFont(QFont("Arial",9,QFont.StyleItalic)); self.state_label.setObjectName("stateLabel")
        self.play_pause_button=QPushButton(); self.play_pause_button.setObjectName("controlButton"); self.play_pause_button.setFixedSize(32,32); self.play_pause_button.setIconSize(QSize(18,18)); self.play_pause_button.clicked.connect(self.on_play_pause_click)
        self.reset_button=QPushButton("R"); self.reset_button.setObjectName("controlButton"); self.reset_button.setFixedSize(32,32); self.reset_button.setToolTip("Reset Timer")
        self.task_mgr_button=QPushButton("T"); self.task_mgr_button.setObjectName("controlButton"); self.task_mgr_button.setFixedSize(32,32); self.task_mgr_button.setToolTip("Toggle Task Manager"); self.task_mgr_button.clicked.connect(self.toggle_main_app_window)
        self.button_layout=QHBoxLayout(); self.button_layout.setSpacing(5); self.button_layout.addStretch(); self.button_layout.addWidget(self.play_pause_button); self.button_layout.addWidget(self.reset_button); self.button_layout.addWidget(self.task_mgr_button); self.button_layout.addStretch()
        content_layout_wrapper.addWidget(self.task_label); content_layout_wrapper.addWidget(self.time_label); content_layout_wrapper.addWidget(self.progress_bar); content_layout_wrapper.addWidget(self.state_label); content_layout_wrapper.addLayout(self.button_layout)
        self.main_layout.addWidget(self.drag_handle_widget); self.main_layout.addWidget(self.content_widget); self.setLayout(self.main_layout)
        self.update_styles_based_on_theme_and_state() # Initial style update
        self.setMinimumHeight(self.SHRUNKEN_HEIGHT)

    def connect_backend_signals(self, backend: BackendPomodoroManager): # Unchanged
        self.request_backend_start_focus.connect(backend.start_focus); self.request_backend_start_break.connect(backend.start_break); self.request_backend_pause.connect(backend.pause); self.request_backend_resume.connect(backend.resume); self.reset_button.clicked.connect(backend.reset)
        backend.timer_state_updated.connect(self.on_backend_state_updated)

    @pyqtSlot(dict)
    def on_backend_state_updated(self, status_dict: dict): # Unchanged
        self._cached_backend_state = status_dict
        self.update_contents(status_dict.get("task_title","No Task"), status_dict.get("time_str","00:00"), status_dict.get("state_str","Idle"), status_dict.get("numeric_timeLeft",0), status_dict.get("numeric_totalTime",1), status_dict.get("is_break",False), status_dict.get("is_running_from_widget",False), status_dict.get("current_task_id"))

    def toggle_main_app_window(self): # Unchanged
        if main_app_window_instance:
            if main_app_window_instance.isVisible(): main_app_window_instance.hide()
            else: main_app_window_instance.show(); main_app_window_instance.activateWindow(); main_app_window_instance.raise_()

    def event(self, event: QEvent): # Unchanged
        if event.type()==QEvent.HoverEnter:
            self.set_shrunken_state(False)
            return True
        elif event.type()==QEvent.HoverLeave:
            # Corrected way to get global cursor position
            global_cursor_pos = QCursor.pos() # QCursor provides the global position
            if not self.rect().contains(self.mapFromGlobal(global_cursor_pos)):
                 self.set_shrunken_state(True)
                 return True
        return super().event(event)

    def set_shrunken_state(self, shrink, animate=True): # Calls theme-aware style update
        target_is_expanded = not shrink
        if self.is_expanded == target_is_expanded and self.height_animation.state() == QPropertyAnimation.Running: return
        self.is_expanded = target_is_expanded; target_height = self.NORMAL_HEIGHT if self.is_expanded else self.SHRUNKEN_HEIGHT; target_opacity = self.NORMAL_OPACITY if self.is_expanded else self.SHRUNKEN_OPACITY
        self.state_label.setVisible(self.is_expanded)
        for i in range(self.button_layout.count()):
            item = self.button_layout.itemAt(i); 
            if item and item.widget(): item.widget().setVisible(self.is_expanded)
        if animate:
            self.height_animation.stop(); self.opacity_animation.stop()
            self.height_animation.setStartValue(self.height()); self.height_animation.setEndValue(target_height); self.height_animation.start()
            current_opacity_effect = self.graphicsEffect(); current_opacity = current_opacity_effect.opacity() if current_opacity_effect else 1.0
            self.opacity_animation.setStartValue(current_opacity); self.opacity_animation.setEndValue(target_opacity); self.opacity_animation.start()
        else:
            self.setMinimumHeight(target_height); self.adjustSize()
            opacity_effect = self.graphicsEffect(); 
            if not opacity_effect: opacity_effect = QGraphicsOpacityEffect(self); self.setGraphicsEffect(opacity_effect)
            opacity_effect.setOpacity(target_opacity)
        self.update_styles_based_on_theme_and_state()


    def on_play_pause_click(self): # Unchanged
        state=self._cached_backend_state
        if not state: print("MiniTimer: No backend state."); return
        is_running=state.get("is_running_from_widget",False); is_break=state.get("is_break",False); timeLeft=state.get("numeric_timeLeft",0); totalTime=state.get("numeric_totalTime",1)
        self._task_id_for_next_focus=state.get("current_task_id"); raw_title=state.get("task_title","No Task")
        if self._task_id_for_next_focus and raw_title not in ["On Break","Task Completed!","No Task","General Focus"]: self._task_title_for_next_focus=raw_title
        else: self._task_title_for_next_focus="General Focus"
        if is_running: self.request_backend_pause.emit()
        else:
            if timeLeft==0:
                if is_break: self.request_backend_start_focus.emit(self._task_id_for_next_focus,self._task_title_for_next_focus)
                else: self.request_backend_start_focus.emit(self._task_id_for_next_focus,self._task_title_for_next_focus) # Assume next is focus
            elif timeLeft>0 and timeLeft<totalTime: self.request_backend_resume.emit()
            elif timeLeft>0 and timeLeft==totalTime:
                if is_break: self.request_backend_start_break.emit()
                else: self.request_backend_start_focus.emit(self._task_id_for_next_focus,self._task_title_for_next_focus)
            else: print(f"MiniTimer: Unhandled play/pause state.")

    def update_play_pause_button_icon(self, is_running, is_break, timeLeft, totalTime): # Unchanged
        tooltip_task_title="General Focus"; cached_task_id=self._cached_backend_state.get("current_task_id"); cached_raw_title=self._cached_backend_state.get("task_title","No Task")
        if cached_task_id and cached_raw_title and cached_raw_title not in ["On Break","Task Completed!","No Task","General Focus"]: tooltip_task_title=cached_raw_title
        if is_running: self.play_pause_button.setText("❚❚"); self.play_pause_button.setToolTip("Pause")
        else:
            if timeLeft==0:
                if is_break: self.play_pause_button.setText("▶"); self.play_pause_button.setToolTip(f"Start Focus: {tooltip_task_title}")
                else: self.play_pause_button.setText("▶"); self.play_pause_button.setToolTip("Start Break Session")
            elif timeLeft>0 and timeLeft<totalTime: self.play_pause_button.setText("▶"); self.play_pause_button.setToolTip("Resume")
            elif timeLeft>0 and timeLeft==totalTime:
                if is_break: self.play_pause_button.setText("▶"); self.play_pause_button.setToolTip("Start Break")
                else: self.play_pause_button.setText("▶"); self.play_pause_button.setToolTip(f"Start Focus: {tooltip_task_title}")
            else: self.play_pause_button.setText("▶"); self.play_pause_button.setToolTip("Start")

    def determine_text_color_for_theme(self, bg_color_qcolor): # Theme aware
        if CURRENT_THEME == THEME_DARK:
            return "white" if bg_color_qcolor.lightnessF() < 0.4 else "#e0e0e0" # Lighter text on darker bg
        else: # Light theme
            return "black" if bg_color_qcolor.lightnessF() > 0.55 else "#333333" # Darker text on lighter bg
            
    def update_styles_based_on_theme_and_state(self): # NEW: Central style update method
        is_break = self._cached_backend_state.get("is_break", False)
        timeLeft = self._cached_backend_state.get("numeric_timeLeft", 0)
        totalTime = self._cached_backend_state.get("numeric_totalTime", 1)
        time_percentage = timeLeft / totalTime if totalTime > 0 else 1.0
        is_expanded = self.is_expanded # Use current expansion state
        self.update_styles(is_break, time_percentage, is_expanded)


    def update_styles(self, is_break_param, time_percentage_param, is_expanded_param): # MODIFIED for theme
        opacity = self.NORMAL_OPACITY if is_expanded_param else self.SHRUNKEN_OPACITY
        
        # Theme-dependent base colors
        if CURRENT_THEME == THEME_DARK:
            focus_content_bg_base = QColor(40, 55, 71)   # Darker blue/grey
            focus_handle_bg_base = QColor(25, 35, 45)    # Even darker
            break_content_bg_base = QColor(40, 71, 55)   # Darker green/grey
            break_handle_bg_base = QColor(25, 45, 35)    # Even darker
            idle_content_bg_base = QColor(50, 50, 50)    # Dark grey
            idle_handle_bg_base = QColor(35, 35, 35)     # Very dark grey
            default_text_color_base = QColor("#e0e0e0")
            progress_border_color = "rgba(100,100,100,0.7)"
            progress_bg_color = "rgba(255,255,255,0.1)"
            button_default_bg = "rgba(255,255,255,0.08)"
            button_hover_bg = "rgba(255,255,255,0.15)"
            button_pressed_bg = "rgba(255,255,255,0.05)"
            button_border_color = "rgba(100,100,100,0.5)"
        else: # Light Theme
            focus_content_bg_base = QColor(45, 90, 140)
            focus_handle_bg_base = QColor(20, 50, 80)
            break_content_bg_base = QColor(50, 120, 50)
            break_handle_bg_base = QColor(20, 70, 20)
            idle_content_bg_base = QColor(80, 80, 80)
            idle_handle_bg_base = QColor(60, 60, 60)
            default_text_color_base = QColor("#111111") # Base, will be adjusted
            progress_border_color = "rgba(150,150,150,0.7)"
            progress_bg_color = "rgba(0,0,0,0.2)"
            button_default_bg = "rgba(255,255,255,0.15)"
            button_hover_bg = "rgba(255,255,255,0.25)"
            button_pressed_bg = "rgba(255,255,255,0.1)"
            button_border_color = "rgba(200,200,200,0.3)"


        current_content_bg, current_handle_bg = idle_content_bg_base, idle_handle_bg_base
        
        is_timer_running = self._cached_backend_state.get("is_running_from_widget", False)
        is_break = self._cached_backend_state.get("is_break", False) # is_break_param
        timeLeft = self._cached_backend_state.get("numeric_timeLeft",0)
        totalTime = self._cached_backend_state.get("numeric_totalTime",1)

        is_paused = not is_timer_running and timeLeft > 0 and timeLeft < totalTime
        is_ready = not is_timer_running and timeLeft > 0 and timeLeft == totalTime
        session_ended = not is_timer_running and timeLeft == 0

        if is_timer_running or is_paused:
            current_content_bg = break_content_bg_base if is_break else focus_content_bg_base
            current_handle_bg = break_handle_bg_base if is_break else focus_handle_bg_base
        elif is_ready:
            current_content_bg = break_content_bg_base if is_break else focus_content_bg_base
            current_handle_bg = break_handle_bg_base if is_break else focus_handle_bg_base
        elif session_ended :
            current_content_bg = focus_content_bg_base if is_break else break_content_bg_base # Opposite for next state
            current_handle_bg = focus_handle_bg_base if is_break else break_handle_bg_base
        
        main_text_color_str = self.determine_text_color_for_theme(current_content_bg)
        time_text_color_str = main_text_color_str
        task_text_color_str = main_text_color_str
        
        if (is_timer_running or is_paused) and not is_break:
            current_percentage = timeLeft / totalTime if totalTime > 0 else 1.0
            # Warning colors can be theme-dependent too if needed
            if current_percentage < 0.01 : time_text_color_str = "rgba(250,80,80,1.0)"; task_text_color_str = time_text_color_str
            elif current_percentage < 0.20: time_text_color_str = "rgba(255,120,120,1.0)"; task_text_color_str = time_text_color_str
            elif current_percentage < 0.50: time_text_color_str = "rgba(255,200,100,1.0)"; task_text_color_str = time_text_color_str
        
        content_bg_rgba = f"rgba({current_content_bg.red()},{current_content_bg.green()},{current_content_bg.blue()},{opacity})"
        handle_bg_rgba = f"rgba({current_handle_bg.red()},{current_handle_bg.green()},{current_handle_bg.blue()},{opacity+0.03})"
        
        # Progress bar chunk color
        pb_chunk_color = time_text_color_str
        if time_text_color_str == main_text_color_str: # Not in warning state
            pb_chunk_color = 'rgba(200,200,200,0.8)' if CURRENT_THEME == THEME_LIGHT else 'rgba(100,180,255,0.7)' # Light blue for dark theme

        progress_style = f"QProgressBar{{border:1px solid {progress_border_color};border-radius:4px;background-color:{progress_bg_color};height:6px}} QProgressBar::chunk{{background-color:{pb_chunk_color};border-radius:3px;margin:0.5px;}}"
        
        button_text_color_final = self.determine_text_color_for_theme(QColor(button_default_bg)) # Text color based on button bg
        if CURRENT_THEME == THEME_DARK: button_text_color_final = "#e0e0e0" # Force light text on dark buttons

        self.setStyleSheet(f"""MiniTimerDisplayWindow{{background:transparent;}}
            #dragHandle{{background-color:{handle_bg_rgba};border-top-left-radius:10px;border-top-right-radius:10px;}}
            #contentWidget{{background-color:{content_bg_rgba};border-bottom-left-radius:10px;border-bottom-right-radius:10px;border:1px solid rgba(180,180,180,0.15);border-top:none;}}
            QLabel{{color:{main_text_color_str};background:transparent;}}
            #taskLabel{{color:{task_text_color_str};}} #timeLabel{{color:{time_text_color_str};}}
            #stateLabel{{color:{QColor(main_text_color_str).lighter(120).name() if CURRENT_THEME == THEME_LIGHT else QColor(main_text_color_str).darker(120).name()};}}
            #controlButton{{background-color:{button_default_bg};color:{button_text_color_final};border:1px solid {button_border_color};border-radius:16px;font-weight:bold;font-size:12px;padding:2px;}}
            #controlButton:hover{{background-color:{button_hover_bg};}} #controlButton:pressed{{background-color:{button_pressed_bg};}}
            {progress_style}""")

    def update_contents(self, task_title_from_state, time_str_from_state, state_str_from_state, numeric_timeLeft_from_state, numeric_totalTime_from_state, is_break_from_state, is_running_from_state, current_task_id_from_state): # Unchanged
        display_task_text = task_title_from_state
        if is_break_from_state : display_task_text = "On Break"
        elif not current_task_id_from_state and task_title_from_state in ["No Task","General Focus"]: display_task_text = "General Focus"
        elif task_title_from_state in ["Task Completed!"]: pass
        elif not task_title_from_state or task_title_from_state == "No Task": display_task_text = "General Focus"
        self.task_label.setText(display_task_text[:25] + ('...' if len(display_task_text)>25 else '')); self.time_label.setText(time_str_from_state); self.state_label.setText(state_str_from_state)
        self.update_play_pause_button_icon(is_running_from_state,is_break_from_state,numeric_timeLeft_from_state,numeric_totalTime_from_state)
        progress_val = math.ceil(((numeric_totalTime_from_state-numeric_timeLeft_from_state)/numeric_totalTime_from_state)*100) if numeric_totalTime_from_state>0 else 0
        self.progress_bar.setValue(max(0,min(100,progress_val)))
        self.update_styles_based_on_theme_and_state() # This will use cached values for styling

    # Other methods (initial_position, load_position, mouseEvents, closeEvent) are unchanged.
    def initial_position(self): # Unchanged
        try:
            primary_screen = QGuiApplication.primaryScreen(); available_geom = primary_screen.availableGeometry() if primary_screen else QApplication.desktop().availableGeometry()
            self.adjustSize()
            self.move(available_geom.right() - self.width() - 20, available_geom.bottom() - self.height() - 40) 
        except Exception: self.move(100,100)
    def load_position(self): # Unchanged
        settings = QSettings(); pos = settings.value("miniTimerPos", None)
        if isinstance(pos, QPoint):
            on_screen = False; screens = QGuiApplication.screens() # Use QGuiApplication
            if not screens: self.initial_position(); return
            for screen in screens:
                if screen.geometry().contains(QRect(pos, self.size())): on_screen = True; break 
            if on_screen: self.move(pos)
            else: self.initial_position()
        else: self.initial_position()
    def mousePressEvent(self,event): # Unchanged
        if self.drag_handle_widget.geometry().contains(self.mapFromGlobal(event.globalPos())) and event.button()==Qt.LeftButton: self.drag_position=event.globalPos()-self.frameGeometry().topLeft();event.accept()
        else: event.ignore()
    def mouseMoveEvent(self,event): # Unchanged
        if event.buttons()==Qt.LeftButton and not self.drag_position.isNull(): self.move(event.globalPos()-self.drag_position);event.accept()
    def mouseReleaseEvent(self,event): # Unchanged
        if event.button() == Qt.LeftButton and not self.drag_position.isNull(): self.drag_position = QPoint(); event.accept()
        else: event.ignore()
    def closeEvent(self, event): # Unchanged
        settings = QSettings(); settings.setValue("miniTimerPos", self.pos()); super().closeEvent(event)

# --- TaskDialog (Unchanged) ---
class TaskDialog(QDialog): # Unchanged code
    def __init__(self, task_data=None, parent=None):
        super().__init__(parent); self.task_data=task_data; self.setWindowTitle("Add Task" if task_data is None else "Edit Task"); self.setMinimumWidth(350)
        self.layout=QFormLayout(self); self.layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.title_edit=QLineEdit(task_data["title"] if task_data else ""); self.description_edit=QTextEdit(task_data["description"] if task_data else ""); self.description_edit.setPlaceholderText("Optional details..."); self.description_edit.setFixedHeight(80)
        self.due_date_edit=QDateEdit(QDate.fromString(task_data["due_date"],"yyyy-MM-dd") if task_data and task_data["due_date"] else QDate.currentDate()); self.due_date_edit.setCalendarPopup(True); self.due_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.pomodoros_est_spin=QSpinBox(); self.pomodoros_est_spin.setMinimum(0); self.pomodoros_est_spin.setValue(task_data["pomodoros_estimated"] if task_data else 1)
        self.points_value_spin=QSpinBox(); self.points_value_spin.setMinimum(0); self.points_value_spin.setMaximum(100); self.points_value_spin.setValue(task_data["points_value"] if task_data else 10)
        self.status_combo=QComboBox(); self.status_combo.addItems(["todo","inprogress","done"]); 
        if task_data and task_data["status"]: self.status_combo.setCurrentText(task_data["status"])
        self.layout.addRow("Title:",self.title_edit); self.layout.addRow("Description:",self.description_edit)
        def add_hl(lbl,wdg): hl=QHBoxLayout(); hl.addWidget(QLabel(lbl)); hl.addWidget(wdg); hl.addStretch(); self.layout.addRow(hl)
        add_hl("Due Date:",self.due_date_edit); add_hl("Est. Pomodoros:",self.pomodoros_est_spin); add_hl("Points Value:",self.points_value_spin)
        if task_data: add_hl("Status:",self.status_combo)
        self.button_box=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel); self.button_box.accepted.connect(self.accept); self.button_box.rejected.connect(self.reject); self.layout.addRow(self.button_box)
        self.setStyleSheet(f"QDialog{{background:{'#3c3c3c' if CURRENT_THEME == THEME_DARK else '#f8f9fa'}; color: {'white' if CURRENT_THEME == THEME_DARK else 'black'};}} QLineEdit,QTextEdit,QSpinBox,QDateEdit,QComboBox{{padding:5px;border:1px solid {'#555' if CURRENT_THEME == THEME_DARK else '#ced4da'};border-radius:4px;background:{'#2c2c2c' if CURRENT_THEME == THEME_DARK else 'white'}; color: {'white' if CURRENT_THEME == THEME_DARK else 'black'};}} QLabel{{margin-top:3px;}} QPushButton{{padding:6px 12px;border-radius:4px;font-weight:bold;}}")
        ok_btn=self.button_box.button(QDialogButtonBox.Ok); cancel_btn=self.button_box.button(QDialogButtonBox.Cancel)
        if ok_btn: ok_btn.setStyleSheet(f"background-color:{'#30854a' if CURRENT_THEME == THEME_DARK else '#28a745'};color:white;") 
        if cancel_btn: cancel_btn.setStyleSheet(f"background-color:{'#5a6268' if CURRENT_THEME == THEME_DARK else '#6c757d'};color:white;")
    def get_data(self): return {"title":self.title_edit.text().strip(),"description":self.description_edit.toPlainText().strip(),"due_date":self.due_date_edit.date().toString("yyyy-MM-dd"),"pomodoros_estimated":self.pomodoros_est_spin.value(),"points_value":self.points_value_spin.value(),"status":self.status_combo.currentText() if self.task_data else "todo"}

# --- TaskItemWidget (Theme aware) ---
class TaskItemWidget(QWidget):
    task_action = pyqtSignal(str, int)
    def __init__(self, task: Dict, parent=None): # MODIFIED for theme
        super().__init__(parent); self.task_id = task['id']; self.task_status = task['status']; layout = QHBoxLayout(self); layout.setContentsMargins(8,5,8,5); layout.setSpacing(8) # Increased margins/spacing
        pomodoro_str = f"{task['pomodoros_completed']}/{task['pomodoros_estimated']}P"; due_date_str = ""
        if task['due_date']:
            due = QDate.fromString(task['due_date'],"yyyy-MM-dd"); today = QDate.currentDate()
            if task['status']!='done':
                if due<today: due_date_str=f" (Overdue: {due.toString('MMM d')})"
                elif due==today: due_date_str=f" (Due Today)"
                else: due_date_str=f" (Due: {due.toString('MMM d')})"
        
        self.info_label = QLabel(f"{task['title']} [{task['status'].capitalize()}] {pomodoro_str}{due_date_str}"); self.info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred); self.info_label.setWordWrap(True)
        font=QFont("Arial", 10 if CURRENT_THEME == THEME_LIGHT else 9); # Slightly smaller for dark potentially
        
        base_text_color = "#e0e0e0" if CURRENT_THEME == THEME_DARK else "#2c3e50"
        done_text_color = "#888" if CURRENT_THEME == THEME_DARK else "#95a5a6"
        inprogress_text_color = "#f39c12" if CURRENT_THEME == THEME_DARK else "#e67e22" # Orange for both
        overdue_text_color = "#e74c3c" # Red for both

        current_text_color = base_text_color
        if task['status']=='done': font.setStrikeOut(True); current_text_color = done_text_color
        elif task['status']=='inprogress': current_text_color = inprogress_text_color; font.setBold(True)
        if "Overdue" in due_date_str: current_text_color = overdue_text_color; font.setBold(True)
        
        self.info_label.setFont(font); self.info_label.setStyleSheet(f"color: {current_text_color};")
        layout.addWidget(self.info_label)

        btn_size=QSize(30,30); # Slightly larger buttons
        
        btn_bg_light = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fdfdfd,stop:1 #f0f0f0)"
        btn_bg_dark = "qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #4c4c4c,stop:1 #404040)"
        btn_border_light = "#c0c0c0"; btn_border_dark = "#5c5c5c"
        btn_hover_bg_light = "#e8f0f8"; btn_hover_bg_dark = "#5a5a5a"
        btn_pressed_bg_light = "#dce4ec"; btn_pressed_bg_dark = "#505050"
        btn_text_light = "#333"; btn_text_dark = "#e0e0e0"

        current_btn_bg = btn_bg_dark if CURRENT_THEME == THEME_DARK else btn_bg_light
        current_btn_border = btn_border_dark if CURRENT_THEME == THEME_DARK else btn_border_light
        current_btn_hover_bg = btn_hover_bg_dark if CURRENT_THEME == THEME_DARK else btn_hover_bg_light
        current_btn_pressed_bg = btn_pressed_bg_dark if CURRENT_THEME == THEME_DARK else btn_pressed_bg_light
        current_btn_text = btn_text_dark if CURRENT_THEME == THEME_DARK else btn_text_light

        btn_style_base = f"QPushButton{{border:1px solid {current_btn_border};border-radius:15px;background-color:{current_btn_bg};padding:0px;font-weight:bold;font-size:14px;color:{current_btn_text};}} QPushButton:hover{{background-color:{current_btn_hover_bg};}} QPushButton:pressed{{background-color:{current_btn_pressed_bg};}} QPushButton:disabled{{background-color:{'#3a3a3a' if CURRENT_THEME == THEME_DARK else '#f0f0f0'};color:{'#777' if CURRENT_THEME == THEME_DARK else '#aaa'};border-color:{'#4a4a4a' if CURRENT_THEME == THEME_DARK else '#ddd'};}}"
        
        def add_btn(txt, tip, action, icon_color_override=None):
            btn=QPushButton(txt); btn.setFixedSize(btn_size); btn.setToolTip(tip); btn.clicked.connect(lambda:self.task_action.emit(action,self.task_id))
            style_to_apply = btn_style_base
            if icon_color_override: # For specific icon colors if needed, less common with emojis
                 style_to_apply += f"QPushButton{{color:{icon_color_override};}}"
            btn.setStyleSheet(style_to_apply); layout.addWidget(btn); return btn

        self.focus_button = add_btn("▶️","Focus","#focus"); 
        if task['status']=='done': self.focus_button.setEnabled(False)
        self.done_button = add_btn("✓" if task['status']!='done' else "↩️", "Mark Done" if task['status']!='done' else "Mark To-Do", "#toggle_done")
        self.edit_button = add_btn("✎","Edit task","#edit"); self.delete_button = add_btn("🗑️","Delete task","#delete")
        self.setAutoFillBackground(True) # Important for QListWidget item background to show


# --- Main Application Window (Theme aware, auto-start focus) ---
class FocusHubApp(QMainWindow):
    def __init__(self): # Unchanged setup
        super().__init__(); self.setWindowTitle("Focus Hub"); self.setGeometry(150,150,780,620); self.central_widget=QWidget(); self.setCentralWidget(self.central_widget); self.layout=QVBoxLayout(self.central_widget)
        self.theme_toggle_checkbox = QCheckBox("🌙 Dark Mode"); self.theme_toggle_checkbox.setChecked(CURRENT_THEME == THEME_DARK); self.theme_toggle_checkbox.stateChanged.connect(self.toggle_theme)
        
        top_bar_layout = QHBoxLayout()
        self.points_label=QLabel("🏆 Points: 0"); self.points_label.setObjectName("pointsLabel")
        top_bar_layout.addWidget(self.points_label, 1, Qt.AlignLeft | Qt.AlignVCenter) # Stretch factor 1
        top_bar_layout.addWidget(self.theme_toggle_checkbox, 0, Qt.AlignRight | Qt.AlignVCenter) # No stretch
        self.layout.addLayout(top_bar_layout)

        tasks_area_label=QLabel("Your Tasks"); tasks_area_label.setObjectName("tasksAreaLabel"); self.layout.addWidget(tasks_area_label)
        self.task_list_widget=QListWidget(); self.task_list_widget.setSelectionMode(QAbstractItemView.NoSelection); self.task_list_widget.setObjectName("taskList"); self.layout.addWidget(self.task_list_widget)
        self.button_layout=QHBoxLayout(); self.button_layout.setSpacing(10) # Increased spacing
        self.add_task_button=QPushButton("✚ Add New Task"); self.add_task_button.setObjectName("addTaskButton"); self.add_task_button.clicked.connect(self.add_task)
        self.button_layout.addWidget(self.add_task_button); self.button_layout.addStretch(1); self.layout.addLayout(self.button_layout)
        self.apply_styles() # Apply initial styles

    def connect_backend_signals(self, backend: BackendPomodoroManager): # Unchanged
        backend.points_globally_updated.connect(self.on_points_globally_updated_slot)
        backend.request_ui_refresh.connect(self.refresh_ui_data)
        self.refresh_ui_data() 

    @pyqtSlot(int)
    def on_points_globally_updated_slot(self, new_total_points: int): # Unchanged
        self.points_label.setText(f"🏆 Points: {new_total_points}")

    def toggle_theme(self, state):
        new_theme = THEME_DARK if state == Qt.Checked else THEME_LIGHT
        set_current_theme(new_theme)
        # Styles are reapplied by set_current_theme via main_app_window_instance.apply_styles()

    def apply_styles(self): # MODIFIED for theme
        light_bg = "#f4f6f8"; dark_bg = "#2c3e50"
        light_text = "#2c3e50"; dark_text = "#ecf0f1"
        light_secondary_text = "#34495e"; dark_secondary_text = "#bdc3c7"
        light_border = "#d1d8e0"; dark_border = "#4a6572"
        light_item_bg = "#ffffff"; dark_item_bg = "#34495e"
        light_item_alt_bg = "#eef2f5"; dark_item_alt_bg = "#3a5064" # For alternating rows if used
        light_item_border = "#eef0f2"; dark_item_border = "#445c6d"
        light_add_btn_bg = "#2ecc71"; dark_add_btn_bg = "#27ae60"
        light_add_btn_hover = "#27ae60"; dark_add_btn_hover = "#1f8b4c"

        bg_color = dark_bg if CURRENT_THEME == THEME_DARK else light_bg
        text_color = dark_text if CURRENT_THEME == THEME_DARK else light_text
        secondary_text_color = dark_secondary_text if CURRENT_THEME == THEME_DARK else light_secondary_text
        border_color = dark_border if CURRENT_THEME == THEME_DARK else light_border
        item_bg = dark_item_bg if CURRENT_THEME == THEME_DARK else light_item_bg
        item_border = dark_item_border if CURRENT_THEME == THEME_DARK else light_item_border
        add_btn_bg = dark_add_btn_bg if CURRENT_THEME == THEME_DARK else light_add_btn_bg
        add_btn_hover = dark_add_btn_hover if CURRENT_THEME == THEME_DARK else light_add_btn_hover
        
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background-color: {bg_color}; color: {text_color}; font-family: Arial, sans-serif; }}
            #pointsLabel {{ font-size:16px; font-weight:bold; color:{secondary_text_color}; padding:8px; border-bottom:1px solid {border_color}; margin-bottom:10px; }}
            #tasksAreaLabel {{ font-size:18px; font-weight:bold; color:{text_color}; margin-bottom:8px; padding-left: 5px; }}
            QCheckBox {{ font-size: 12px; padding: 5px; }} /* Theme for checkbox */
            #taskList {{ background-color:{item_bg}; border:1px solid {border_color}; border-radius:8px; font-size:14px; outline:0; }}
            #taskList::item {{ border-bottom:1px solid {item_border}; padding:0px; background-color: transparent; }} /* Item itself is transparent, widget inside handles bg */
            #taskList::item:hover {{ background-color: {'#405568' if CURRENT_THEME == THEME_DARK else '#e8f0f8'}; }} /* Subtle hover on item if widget doesn't cover all */
            QPushButton {{ background-color:{'#4a6572' if CURRENT_THEME == THEME_DARK else '#5dade2'}; color:white; border:none; padding:10px 18px; text-align:center; font-size:14px; font-weight:500; border-radius:6px; margin:2px; min-width:90px; }}
            QPushButton:hover {{ background-color:{'#527183' if CURRENT_THEME == THEME_DARK else '#3498db'}; }}
            QPushButton:pressed {{ background-color:{'#3e5a6b' if CURRENT_THEME == THEME_DARK else '#2874a6'}; }}
            #addTaskButton {{ background-color:{add_btn_bg}; }} #addTaskButton:hover {{ background-color:{add_btn_hover}; }}
        """)
        self.update() # Force repaint

    @pyqtSlot()
    def refresh_ui_data(self): self.load_tasks(); self.update_points_display_from_db() # Unchanged

    def _execute_db_and_notify_backend(self, operation_func, *args, failure_title="DB Error"): # Unchanged
        def worker():
            new_total_pts=None; success=False
            try:
                with get_db() as db: result=operation_func(db,*args); 
                if isinstance(result,int): new_total_pts=result
                success=True
                if success and backend_pomodoro_instance:
                    if new_total_pts is not None: backend_pomodoro_instance.trigger_points_update_signal(new_total_pts)
                    backend_pomodoro_instance.trigger_ui_refresh_signal()
            except sqlite3.Error as e: print(f"{failure_title}: {e}")
            except Exception as e: print(f"Unexpected DB error: {e}")
        threading.Thread(target=worker,daemon=True).start()

    def load_tasks(self): # Unchanged (TaskItemWidget handles its own theme update)
        self.task_list_widget.clear()
        try:
            with get_db() as db: cursor=db.cursor(); cursor.execute("SELECT * FROM tasks ORDER BY CASE status WHEN 'inprogress' THEN 1 WHEN 'todo' THEN 2 WHEN 'done' THEN 3 ELSE 4 END,due_date ASC,created_at DESC"); tasks_raw=cursor.fetchall()
            for task_raw in tasks_raw:
                task=dict(task_raw); item_widget=TaskItemWidget(task); item_widget.task_action.connect(self.handle_task_item_action)
                list_item=QListWidgetItem(self.task_list_widget); list_item.setSizeHint(item_widget.sizeHint()); list_item.setData(Qt.UserRole,task['id'])
                self.task_list_widget.addItem(list_item); self.task_list_widget.setItemWidget(list_item,item_widget)
        except sqlite3.Error as e: QMessageBox.critical(self,"DB Error",f"Could not load tasks: {e}")

    def update_points_display_from_db(self): # Unchanged
        try:
            with get_db() as db: cursor=db.cursor(); cursor.execute("SELECT total_points FROM user_stats WHERE id=1"); stats=cursor.fetchone()
            self.points_label.setText(f"🏆 Points: {stats['total_points'] if stats else 0}")
        except sqlite3.Error as e: self.points_label.setText("Points: Error"); print(f"Error fetching points: {e}")

    def add_task(self): # Unchanged
        dialog=TaskDialog(parent=self)
        if dialog.exec_()==QDialog.Accepted:
            data=dialog.get_data()
            if not data["title"]: QMessageBox.warning(self,"Input Error","Title empty."); return
            def do_add(db,d): db.execute("INSERT INTO tasks (title,description,due_date,pomodoros_estimated,points_value,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",(d["title"],d["description"],d["due_date"],d["pomodoros_estimated"],d["points_value"],d["status"],datetime.datetime.now(datetime.timezone.utc).isoformat(),datetime.datetime.now(datetime.timezone.utc).isoformat()))
            self._execute_db_and_notify_backend(do_add,data,failure_title="Add Task Error")

    def get_task_data_from_db(self, task_id: int): # Unchanged
        if not task_id: return None
        try:
            with get_db() as db: cursor=db.cursor(); cursor.execute("SELECT * FROM tasks WHERE id=?",(task_id,)); task=cursor.fetchone()
            return dict(task) if task else None
        except sqlite3.Error as e: QMessageBox.critical(self,"DB Error",f"Fetch task error: {e}"); return None

    @pyqtSlot(str, int)
    def handle_task_item_action(self, action_type: str, task_id: int): # MODIFIED for auto-start focus
        task_data = self.get_task_data_from_db(task_id)
        if not task_data: QMessageBox.warning(self,"Error",f"Task {task_id} not found."); return
        if action_type == "#edit": self._edit_task(task_data)
        elif action_type == "#delete": self._delete_task(task_id,task_data['title'])
        elif action_type == "#focus": self._focus_on_task_and_start(task_data) # New method
        elif action_type == "#toggle_done": self._toggle_task_done_status(task_data)

    def _edit_task(self, task_data_dict: Dict): # Unchanged logic
        dialog=TaskDialog(task_data=task_data_dict,parent=self)
        if dialog.exec_()==QDialog.Accepted:
            updated_data=dialog.get_data()
            if not updated_data["title"]: QMessageBox.warning(self,"Input Error","Title empty."); return
            def do_edit(db,tid,nd,os):
                cur=db.cursor(); now=datetime.datetime.now(datetime.timezone.utc).isoformat(); pts=0; ntp=None
                if nd["status"]=='done' and os!='done': pts=nd["points_value"]
                cur.execute("UPDATE tasks SET title=?,description=?,due_date=?,pomodoros_estimated=?,points_value=?,status=?,updated_at=? WHERE id=?",(nd["title"],nd["description"],nd["due_date"],nd["pomodoros_estimated"],nd["points_value"],nd["status"],now,tid))
                if pts>0: ntp=update_user_points_in_db(db,pts)
                return ntp
            self._execute_db_and_notify_backend(do_edit,task_data_dict['id'],updated_data,task_data_dict["status"],failure_title="Update Task Error")

    def _delete_task(self, task_id: int, task_title: str): # Unchanged
        if QMessageBox.question(self,"Confirm Delete",f"Delete '{task_title}'?",QMessageBox.Yes|QMessageBox.No,QMessageBox.No)==QMessageBox.Yes:
            def do_del(db,tid): db.execute("DELETE FROM tasks WHERE id=?",(tid,)); 
            if backend_pomodoro_instance and backend_pomodoro_instance.current_task_id==tid: backend_pomodoro_instance.reset()
            self._execute_db_and_notify_backend(do_del,task_id,failure_title="Delete Task Error")

    def _toggle_task_done_status(self, task_data: Dict): # Unchanged
        tid=task_data['id']; cs=task_data['status']; ns='todo' if cs=='done' else 'done'; pc=0
        if ns=='done': pc=task_data['points_value']
        def do_toggle(db,task_id,new_stat,pts_chg):
            cur=db.cursor(); now=datetime.datetime.now(datetime.timezone.utc).isoformat(); cur.execute("UPDATE tasks SET status=?,updated_at=? WHERE id=?",(new_stat,now,task_id)); ntp=None
            if pts_chg!=0: ntp=update_user_points_in_db(db,pts_chg)
            if new_stat=='done' and backend_pomodoro_instance and backend_pomodoro_instance.current_task_id==task_id: backend_pomodoro_instance.complete_current_task_early()
            return ntp
        self._execute_db_and_notify_backend(do_toggle,tid,ns,pc,failure_title="Update Task Status Error")
            
    def _focus_on_task_and_start(self, task_data: Dict): # NEW: Auto-start and hide
        if task_data["status"] == 'done':
            QMessageBox.information(self, "Task Done", "This task is already completed.")
            return

        if backend_pomodoro_instance:
            # Select the task in the backend
            backend_pomodoro_instance.select_task(task_data['id'], task_data["title"])
            
            # Programmatically trigger the start_focus on the mini timer (or backend directly)
            # This ensures the MiniTimer's internal logic for _task_id_for_next_focus is also aligned if it relies on it.
            if mini_timer_window_instance:
                # Ensure MiniTimer has the latest selected task info before "clicking" play
                mini_timer_window_instance._task_id_for_next_focus = task_data['id']
                mini_timer_window_instance._task_title_for_next_focus = task_data["title"]
                mini_timer_window_instance.request_backend_start_focus.emit(task_data['id'], task_data["title"])
            else: # Fallback if mini timer somehow not available
                backend_pomodoro_instance.start_focus(task_data['id'], task_data["title"])
        
        # Hide the main task window
        self.hide()
        if mini_timer_window_instance and not mini_timer_window_instance.isVisible():
            mini_timer_window_instance.show()
            mini_timer_window_instance.activateWindow()

    def closeEvent(self, event): # Unchanged
        if mini_timer_window_instance and mini_timer_window_instance.isVisible(): self.hide(); event.ignore()
        else:
            if mini_timer_window_instance: mini_timer_window_instance.close()
            if backend_pomodoro_instance: 
                with backend_pomodoro_instance.internal_lock: backend_pomodoro_instance._stop_timer_thread_unsafe()
            QApplication.instance().quit(); event.accept()


if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    app.setOrganizationName("ADHDFocusHubOrg"); app.setApplicationName("FocusHubApp")

    if getattr(sys,'frozen',False): script_dir_abs=os.path.dirname(sys.executable)
    else: script_dir_abs=os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(script_dir_abs)
    DATABASE_URL=os.path.join(script_dir_abs,"adhd_app.db")
    BELL_MP3_PATH_ABS=os.path.join(script_dir_abs,"bell.mp3")
    if not os.path.exists(BELL_MP3_PATH_ABS): print(f"WARN: bell.mp3 not found: {BELL_MP3_PATH_ABS}"); BELL_MP3_PATH_ABS=""

    load_current_theme() # Load theme before creating UI
    init_db()

    backend_pomodoro_instance = BackendPomodoroManager()
    main_app_window_instance = FocusHubApp() # Styles applied in its __init__ based on CURRENT_THEME
    mini_timer_window_instance = MiniTimerDisplayWindow() # Styles applied in its __init__

    mini_timer_window_instance.connect_backend_signals(backend_pomodoro_instance)
    main_app_window_instance.connect_backend_signals(backend_pomodoro_instance)
    
    mini_timer_window_instance.show()
    exit_code = app.exec_()
    if backend_pomodoro_instance:
        with backend_pomodoro_instance.internal_lock: backend_pomodoro_instance._stop_timer_thread_unsafe()
    sys.exit(exit_code)
