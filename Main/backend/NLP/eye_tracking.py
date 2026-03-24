# eye_tracking.py - Tobii Stream Engine eye tracking service (consumer devices)
import ctypes
from ctypes import (
    c_int, c_void_p, c_char_p, c_int64, c_float,
    POINTER, CFUNCTYPE, byref, Structure,
)
import os
import threading
from datetime import datetime

# 64-bit Stream Engine DLL from tobii_native NuGet package
_DLL_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'tobii_native',
    'extracted', 'build', 'x64', 'tobii_stream_engine.dll',
)

_dll = None


def _load_dll():
    global _dll
    if _dll is not None:
        return _dll
    _dll = ctypes.CDLL(_DLL_PATH)
    return _dll


class _GazePoint(Structure):
    """tobii_gaze_point_t from the Stream Engine C API."""
    _fields_ = [
        ('timestamp_us', c_int64),
        ('validity', c_int),       # 0 = valid
        ('position_xy', c_float * 2),
    ]


_GAZE_CB = CFUNCTYPE(None, POINTER(_GazePoint), c_void_p)
_ENUM_CB = CFUNCTYPE(None, c_char_p, c_void_p)


class EyeTrackingService:
    """Manages a Tobii consumer eye tracker via the Stream Engine native API.

    Gaze data is buffered in memory while tracking is active,
    then returned as a batch when tracking stops.
    """

    def __init__(self):
        self.api = None
        self.device = None
        self.is_tracking = False
        self.gaze_data = []
        self.session_id = None
        self._lock = threading.Lock()
        self._poll_thread = None
        self._stop_event = threading.Event()
        self._gaze_cb_ref = None   # prevent GC of ctypes callback
        self._device_url = None

    # ── connection ──────────────────────────────────────────────

    def _init_api(self):
        if self.api:
            return
        dll = _load_dll()
        self.api = c_void_p()
        result = dll.tobii_api_create(byref(self.api), None, None)
        if result != 0:
            self.api = None
            raise RuntimeError(f"Failed to create Tobii API (error {result})")

    def find_tracker(self):
        """Discover and connect to the first available Tobii eye tracker."""
        self._init_api()
        dll = _load_dll()

        urls = []
        def _enum(url, _):
            urls.append(url)
        cb = _ENUM_CB(_enum)
        dll.tobii_enumerate_local_device_urls(self.api, cb, None)

        if not urls:
            raise RuntimeError(
                "No Tobii eye tracker found. "
                "Ensure the device is connected and Tobii software is running."
            )

        self._device_url = urls[0]
        self.device = c_void_p()
        result = dll.tobii_device_create(
            self.api, self._device_url, byref(self.device),
        )
        if result != 0:
            self.device = None
            raise RuntimeError(
                f"Failed to connect to tracker at "
                f"{self._device_url.decode()} (error {result})"
            )
        print(f"[EyeTracking] Connected to device at: {self._device_url.decode()}")

    # ── tracking ────────────────────────────────────────────────

    def start(self, session_id: str):
        """Start collecting gaze data for the given session."""
        if not self.device:
            self.find_tracker()

        with self._lock:
            self.gaze_data = []
            self.session_id = session_id
            self.is_tracking = True
            self._stop_event.clear()

        dll = _load_dll()

        def _gaze_callback(gaze_ptr, _):
            if not self.is_tracking:
                return
            gp = gaze_ptr.contents
            valid = gp.validity == 1
            sample = {
                "timestamp": datetime.now().isoformat(),
                "device_ts": gp.timestamp_us,
                "gaze_x": float(gp.position_xy[0]) if valid else None,
                "gaze_y": float(gp.position_xy[1]) if valid else None,
                "gaze_valid": valid,
            }
            with self._lock:
                self.gaze_data.append(sample)

        self._gaze_cb_ref = _GAZE_CB(_gaze_callback)
        result = dll.tobii_gaze_point_subscribe(self.device, self._gaze_cb_ref, None)
        if result != 0:
            raise RuntimeError(f"Failed to subscribe to gaze data (error {result})")

        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
        print(f"[EyeTracking] Started tracking for session: {session_id}")

    def _poll_loop(self):
        """Background thread that pumps the Stream Engine callback queue."""
        dll = _load_dll()
        device_arr = (c_void_p * 1)(self.device)
        while not self._stop_event.is_set():
            dll.tobii_wait_for_callbacks(None, c_int(1), device_arr)
            dll.tobii_device_process_callbacks(self.device)

    def stop(self) -> list:
        """Stop tracking and return the buffered gaze samples."""
        self._stop_event.set()
        if self._poll_thread:
            self._poll_thread.join(timeout=2.0)
            self._poll_thread = None

        dll = _load_dll()
        if self.device and self.is_tracking:
            dll.tobii_gaze_point_unsubscribe(self.device)

        with self._lock:
            self.is_tracking = False
            data = self.gaze_data.copy()
            self.gaze_data = []

        print(f"[EyeTracking] Stopped tracking. Collected {len(data)} gaze samples.")
        return data

    @property
    def is_connected(self) -> bool:
        return self.device is not None
