import ctypes
from ctypes import wintypes
import time

# Simulates genuine multitouch (e.g. a two-finger pinch) via the same
# InjectTouchInput API a real touchscreen feeds into Windows. pyautogui only
# has one cursor to move/click — it can't represent two independent contact
# points moving at once, which is what a pinch gesture actually is.

PT_TOUCH = 0x00000002

POINTER_FLAG_NONE = 0x00000000
POINTER_FLAG_NEW = 0x00000001
POINTER_FLAG_INRANGE = 0x00000002
POINTER_FLAG_INCONTACT = 0x00000004
POINTER_FLAG_DOWN = 0x00010000
POINTER_FLAG_UPDATE = 0x00020000
POINTER_FLAG_UP = 0x00040000

TOUCH_MASK_NONE = 0x00000000
TOUCH_MASK_CONTACTAREA = 0x00000001

TOUCH_FEEDBACK_DEFAULT = 0x1


class POINTER_INFO(ctypes.Structure):
    _fields_ = [
        ('pointerType', ctypes.c_uint32),
        ('pointerId', ctypes.c_uint32),
        ('frameId', ctypes.c_uint32),
        ('pointerFlags', ctypes.c_int),
        ('sourceDevice', wintypes.HANDLE),
        ('hwndTarget', wintypes.HWND),
        ('ptPixelLocation', wintypes.POINT),
        ('ptHimetricLocation', wintypes.POINT),
        ('ptPixelLocationRaw', wintypes.POINT),
        ('ptHimetricLocationRaw', wintypes.POINT),
        ('dwTime', wintypes.DWORD),
        ('historyCount', ctypes.c_uint32),
        ('InputData', ctypes.c_int32),
        ('dwKeyStates', wintypes.DWORD),
        ('PerformanceCount', ctypes.c_uint64),
        ('ButtonChangeType', ctypes.c_int),
    ]


class POINTER_TOUCH_INFO(ctypes.Structure):
    _fields_ = [
        ('pointerInfo', POINTER_INFO),
        ('touchFlags', ctypes.c_int),
        ('touchMask', ctypes.c_int),
        ('rcContact', wintypes.RECT),
        ('rcContactRaw', wintypes.RECT),
        ('orientation', ctypes.c_uint32),
        ('pressure', ctypes.c_uint32),
    ]


_user32 = ctypes.windll.user32
_initialized = False


def _ensure_initialized():
    global _initialized
    if not _initialized:
        # maxCount=2 — only ever need two simultaneous contact points (one
        # pinch gesture's worth).
        if not _user32.InitializeTouchInjection(2, TOUCH_FEEDBACK_DEFAULT):
            raise ctypes.WinError()
        _initialized = True


def _touch_point(pointer_id, x, y, flags, contact_radius=5):
    info = POINTER_TOUCH_INFO()
    ctypes.memset(ctypes.byref(info), 0, ctypes.sizeof(info))
    info.pointerInfo.pointerType = PT_TOUCH
    info.pointerInfo.pointerId = pointer_id
    info.pointerInfo.pointerFlags = flags
    info.pointerInfo.ptPixelLocation.x = int(x)
    info.pointerInfo.ptPixelLocation.y = int(y)
    info.touchMask = TOUCH_MASK_CONTACTAREA
    info.rcContact.left = int(x) - contact_radius
    info.rcContact.top = int(y) - contact_radius
    info.rcContact.right = int(x) + contact_radius
    info.rcContact.bottom = int(y) + contact_radius
    return info


def _inject(points):
    array = (POINTER_TOUCH_INFO * len(points))(*points)
    if not _user32.InjectTouchInput(len(points), array):
        raise ctypes.WinError()


def pinch(center, start_radius, end_radius, steps=20, delay=0.01):
    """Two-finger pinch centered on `center`, with each finger `start_radius`
    px from it at the start and `end_radius` px at the end (along a
    horizontal line through the center). Spreading apart (start < end) zooms
    in; pinching together (start > end) zooms out — same as on a real
    touchscreen.
    """
    _ensure_initialized()
    cx, cy = center

    down_flags = POINTER_FLAG_DOWN | POINTER_FLAG_INRANGE | POINTER_FLAG_INCONTACT
    _inject([
        _touch_point(0, cx - start_radius, cy, down_flags),
        _touch_point(1, cx + start_radius, cy, down_flags),
    ])
    time.sleep(delay)

    move_flags = POINTER_FLAG_UPDATE | POINTER_FLAG_INRANGE | POINTER_FLAG_INCONTACT
    for i in range(1, steps + 1):
        radius = start_radius + (end_radius - start_radius) * i / steps
        _inject([
            _touch_point(0, cx - radius, cy, move_flags),
            _touch_point(1, cx + radius, cy, move_flags),
        ])
        time.sleep(delay)

    _inject([
        _touch_point(0, cx - end_radius, cy, POINTER_FLAG_UP),
        _touch_point(1, cx + end_radius, cy, POINTER_FLAG_UP),
    ])
