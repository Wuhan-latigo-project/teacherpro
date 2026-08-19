# quiz.py - Complete embeddable quiz module for teacher dashboard
# Usage (embedded): from quiz import QuizPage; page = QuizPage(config, parent)
# Usage (standalone): from quiz import launch_quiz; launch_quiz()

import sys
import asyncio
import websockets
import json
import time
import ssl
from threading import Thread
from cryptography.fernet import Fernet
import websockets.exceptions
import config
import logging
from datetime import datetime
import base64
import os
import re
import hashlib
import queue
import threading
import random

# ============================================================
# FlatBuffers imports (merged - no external Behavioral imports)
# ============================================================
import flatbuffers
from flatbuffers.compat import import_numpy
np = import_numpy()

# ---------- BehavioralMessage ----------
class BehavioralMessage(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = BehavioralMessage()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsBehavioralMessage(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def StudentName(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def RoomId(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def SessionId(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def EventType(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int8Flags, o + self._tab.Pos)
        return 0
    def DataType(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Uint8Flags, o + self._tab.Pos)
        return 0
    def Data(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(14))
        if o != 0:
            from flatbuffers.table import Table
            obj = Table(bytearray(), 0)
            self._tab.Union(obj, o)
            return obj
        return None
    def ClientTimestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(16))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def BehavioralMessageStart(builder): builder.StartObject(7)
def Start(builder): BehavioralMessageStart(builder)
def BehavioralMessageAddStudentName(builder, studentName): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(studentName), 0)
def AddStudentName(builder, studentName): BehavioralMessageAddStudentName(builder, studentName)
def BehavioralMessageAddRoomId(builder, roomId): builder.PrependUOffsetTRelativeSlot(1, flatbuffers.number_types.UOffsetTFlags.py_type(roomId), 0)
def AddRoomId(builder, roomId): BehavioralMessageAddRoomId(builder, roomId)
def BehavioralMessageAddSessionId(builder, sessionId): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(sessionId), 0)
def AddSessionId(builder, sessionId): BehavioralMessageAddSessionId(builder, sessionId)
def BehavioralMessageAddEventType(builder, eventType): builder.PrependInt8Slot(3, eventType, 0)
def AddEventType(builder, eventType): BehavioralMessageAddEventType(builder, eventType)
def BehavioralMessageAddDataType(builder, dataType): builder.PrependUint8Slot(4, dataType, 0)
def AddDataType(builder, dataType): BehavioralMessageAddDataType(builder, dataType)
def BehavioralMessageAddData(builder, data): builder.PrependUOffsetTRelativeSlot(5, flatbuffers.number_types.UOffsetTFlags.py_type(data), 0)
def AddData(builder, data): BehavioralMessageAddData(builder, data)
def BehavioralMessageAddClientTimestamp(builder, clientTimestamp): builder.PrependUOffsetTRelativeSlot(6, flatbuffers.number_types.UOffsetTFlags.py_type(clientTimestamp), 0)
def AddClientTimestamp(builder, clientTimestamp): BehavioralMessageAddClientTimestamp(builder, clientTimestamp)
def BehavioralMessageEnd(builder): return builder.EndObject()
def End(builder): return BehavioralMessageEnd(builder)

# ---------- EventType ----------
class EventType(object):
    KeyPress = 0; MouseMove = 1; MouseClick = 2; CopyPaste = 3; WindowSwitch = 4
    Scroll = 5; ExamEvent = 6; MouseEnter = 7; MouseLeave = 8; FocusIn = 9; FocusOut = 10

# ---------- EventData ----------
class EventData(object):
    NONE = 0; KeyPressEvent = 1; MouseMoveEvent = 2; MouseClickEvent = 3
    MouseEnterEvent = 4; MouseLeaveEvent = 5; FocusInEvent = 6; FocusOutEvent = 7
    CopyPasteEvent = 8; WindowSwitchEvent = 9; ScrollEvent = 10; ExamEvent = 11

# ---------- KeyPressEvent ----------
class KeyPressEvent(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = KeyPressEvent()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsKeyPressEvent(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def Key(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def WidgetId(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def TextLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int32Flags, o + self._tab.Pos)
        return 0
    def Modifiers(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def Timestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def KeyPressEventStart(builder): builder.StartObject(5)
def Start(builder): KeyPressEventStart(builder)
def KeyPressEventAddKey(builder, key): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(key), 0)
def AddKey(builder, key): KeyPressEventAddKey(builder, key)
def KeyPressEventAddWidgetId(builder, widgetId): builder.PrependUOffsetTRelativeSlot(1, flatbuffers.number_types.UOffsetTFlags.py_type(widgetId), 0)
def AddWidgetId(builder, widgetId): KeyPressEventAddWidgetId(builder, widgetId)
def KeyPressEventAddTextLength(builder, textLength): builder.PrependInt32Slot(2, textLength, 0)
def AddTextLength(builder, textLength): KeyPressEventAddTextLength(builder, textLength)
def KeyPressEventAddModifiers(builder, modifiers): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(modifiers), 0)
def AddModifiers(builder, modifiers): KeyPressEventAddModifiers(builder, modifiers)
def KeyPressEventAddTimestamp(builder, timestamp): builder.PrependUOffsetTRelativeSlot(4, flatbuffers.number_types.UOffsetTFlags.py_type(timestamp), 0)
def AddTimestamp(builder, timestamp): KeyPressEventAddTimestamp(builder, timestamp)
def KeyPressEventEnd(builder): return builder.EndObject()
def End(builder): return KeyPressEventEnd(builder)

# ---------- MouseMoveEvent ----------
class MouseMoveEvent(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = MouseMoveEvent()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsMouseMoveEvent(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def WidgetId(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def HoverDurationMs(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int32Flags, o + self._tab.Pos)
        return 0
    def CurrentValue(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def Timestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def MouseMoveEventStart(builder): builder.StartObject(4)
def Start(builder): MouseMoveEventStart(builder)
def MouseMoveEventAddWidgetId(builder, widgetId): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(widgetId), 0)
def AddWidgetId(builder, widgetId): MouseMoveEventAddWidgetId(builder, widgetId)
def MouseMoveEventAddHoverDurationMs(builder, hoverDurationMs): builder.PrependInt32Slot(1, hoverDurationMs, 0)
def AddHoverDurationMs(builder, hoverDurationMs): MouseMoveEventAddHoverDurationMs(builder, hoverDurationMs)
def MouseMoveEventAddCurrentValue(builder, currentValue): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(currentValue), 0)
def AddCurrentValue(builder, currentValue): MouseMoveEventAddCurrentValue(builder, currentValue)
def MouseMoveEventAddTimestamp(builder, timestamp): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(timestamp), 0)
def AddTimestamp(builder, timestamp): MouseMoveEventAddTimestamp(builder, timestamp)
def MouseMoveEventEnd(builder): return builder.EndObject()
def End(builder): return MouseMoveEventEnd(builder)

# ---------- MouseClickEvent ----------
class MouseClickEvent(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = MouseClickEvent()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsMouseClickEvent(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def ButtonId(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def HoverDurationMs(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int32Flags, o + self._tab.Pos)
        return 0
    def ButtonText(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def Timestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def MouseClickEventStart(builder): builder.StartObject(4)
def Start(builder): MouseClickEventStart(builder)
def MouseClickEventAddButtonId(builder, buttonId): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(buttonId), 0)
def AddButtonId(builder, buttonId): MouseClickEventAddButtonId(builder, buttonId)
def MouseClickEventAddHoverDurationMs(builder, hoverDurationMs): builder.PrependInt32Slot(1, hoverDurationMs, 0)
def AddHoverDurationMs(builder, hoverDurationMs): MouseClickEventAddHoverDurationMs(builder, hoverDurationMs)
def MouseClickEventAddButtonText(builder, buttonText): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(buttonText), 0)
def AddButtonText(builder, buttonText): MouseClickEventAddButtonText(builder, buttonText)
def MouseClickEventAddTimestamp(builder, timestamp): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(timestamp), 0)
def AddTimestamp(builder, timestamp): MouseClickEventAddTimestamp(builder, timestamp)
def MouseClickEventEnd(builder): return builder.EndObject()
def End(builder): return MouseClickEventEnd(builder)

# ---------- MouseEnterEvent ----------
class MouseEnterEvent(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = MouseEnterEvent()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsMouseEnterEvent(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def WidgetId(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def CurrentValue(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def Timestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def MouseEnterEventStart(builder): builder.StartObject(3)
def Start(builder): MouseEnterEventStart(builder)
def MouseEnterEventAddWidgetId(builder, widgetId): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(widgetId), 0)
def AddWidgetId(builder, widgetId): MouseEnterEventAddWidgetId(builder, widgetId)
def MouseEnterEventAddCurrentValue(builder, currentValue): builder.PrependUOffsetTRelativeSlot(1, flatbuffers.number_types.UOffsetTFlags.py_type(currentValue), 0)
def AddCurrentValue(builder, currentValue): MouseEnterEventAddCurrentValue(builder, currentValue)
def MouseEnterEventAddTimestamp(builder, timestamp): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(timestamp), 0)
def AddTimestamp(builder, timestamp): MouseEnterEventAddTimestamp(builder, timestamp)
def MouseEnterEventEnd(builder): return builder.EndObject()
def End(builder): return MouseEnterEventEnd(builder)

# ---------- MouseLeaveEvent ----------
class MouseLeaveEvent(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = MouseLeaveEvent()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsMouseLeaveEvent(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def WidgetId(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def HoverDurationMs(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int32Flags, o + self._tab.Pos)
        return 0
    def CurrentValue(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def Timestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def MouseLeaveEventStart(builder): builder.StartObject(4)
def Start(builder): MouseLeaveEventStart(builder)
def MouseLeaveEventAddWidgetId(builder, widgetId): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(widgetId), 0)
def AddWidgetId(builder, widgetId): MouseLeaveEventAddWidgetId(builder, widgetId)
def MouseLeaveEventAddHoverDurationMs(builder, hoverDurationMs): builder.PrependInt32Slot(1, hoverDurationMs, 0)
def AddHoverDurationMs(builder, hoverDurationMs): MouseLeaveEventAddHoverDurationMs(builder, hoverDurationMs)
def MouseLeaveEventAddCurrentValue(builder, currentValue): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(currentValue), 0)
def AddCurrentValue(builder, currentValue): MouseLeaveEventAddCurrentValue(builder, currentValue)
def MouseLeaveEventAddTimestamp(builder, timestamp): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(timestamp), 0)
def AddTimestamp(builder, timestamp): MouseLeaveEventAddTimestamp(builder, timestamp)
def MouseLeaveEventEnd(builder): return builder.EndObject()
def End(builder): return MouseLeaveEventEnd(builder)

# ---------- FocusInEvent ----------
class FocusInEvent(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = FocusInEvent()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsFocusInEvent(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def WidgetId(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def HoverDurationMs(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int32Flags, o + self._tab.Pos)
        return 0
    def CurrentValue(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def Timestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def FocusInEventStart(builder): builder.StartObject(4)
def Start(builder): FocusInEventStart(builder)
def FocusInEventAddWidgetId(builder, widgetId): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(widgetId), 0)
def AddWidgetId(builder, widgetId): FocusInEventAddWidgetId(builder, widgetId)
def FocusInEventAddHoverDurationMs(builder, hoverDurationMs): builder.PrependInt32Slot(1, hoverDurationMs, 0)
def AddHoverDurationMs(builder, hoverDurationMs): FocusInEventAddHoverDurationMs(builder, hoverDurationMs)
def FocusInEventAddCurrentValue(builder, currentValue): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(currentValue), 0)
def AddCurrentValue(builder, currentValue): FocusInEventAddCurrentValue(builder, currentValue)
def FocusInEventAddTimestamp(builder, timestamp): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(timestamp), 0)
def AddTimestamp(builder, timestamp): FocusInEventAddTimestamp(builder, timestamp)
def FocusInEventEnd(builder): return builder.EndObject()
def End(builder): return FocusInEventEnd(builder)

# ---------- FocusOutEvent ----------
class FocusOutEvent(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = FocusOutEvent()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsFocusOutEvent(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def WidgetId(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def CurrentValue(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def Timestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def FocusOutEventStart(builder): builder.StartObject(3)
def Start(builder): FocusOutEventStart(builder)
def FocusOutEventAddWidgetId(builder, widgetId): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(widgetId), 0)
def AddWidgetId(builder, widgetId): FocusOutEventAddWidgetId(builder, widgetId)
def FocusOutEventAddCurrentValue(builder, currentValue): builder.PrependUOffsetTRelativeSlot(1, flatbuffers.number_types.UOffsetTFlags.py_type(currentValue), 0)
def AddCurrentValue(builder, currentValue): FocusOutEventAddCurrentValue(builder, currentValue)
def FocusOutEventAddTimestamp(builder, timestamp): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(timestamp), 0)
def AddTimestamp(builder, timestamp): FocusOutEventAddTimestamp(builder, timestamp)
def FocusOutEventEnd(builder): return builder.EndObject()
def End(builder): return FocusOutEventEnd(builder)

# ---------- CopyPasteEvent ----------
class CopyPasteEvent(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = CopyPasteEvent()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsCopyPasteEvent(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def Action(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def ContentLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int32Flags, o + self._tab.Pos)
        return 0
    def ContentPreview(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def WidgetId(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def Timestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def CopyPasteEventStart(builder): builder.StartObject(5)
def Start(builder): CopyPasteEventStart(builder)
def CopyPasteEventAddAction(builder, action): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(action), 0)
def AddAction(builder, action): CopyPasteEventAddAction(builder, action)
def CopyPasteEventAddContentLength(builder, contentLength): builder.PrependInt32Slot(1, contentLength, 0)
def AddContentLength(builder, contentLength): CopyPasteEventAddContentLength(builder, contentLength)
def CopyPasteEventAddContentPreview(builder, contentPreview): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(contentPreview), 0)
def AddContentPreview(builder, contentPreview): CopyPasteEventAddContentPreview(builder, contentPreview)
def CopyPasteEventAddWidgetId(builder, widgetId): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(widgetId), 0)
def AddWidgetId(builder, widgetId): CopyPasteEventAddWidgetId(builder, widgetId)
def CopyPasteEventAddTimestamp(builder, timestamp): builder.PrependUOffsetTRelativeSlot(4, flatbuffers.number_types.UOffsetTFlags.py_type(timestamp), 0)
def AddTimestamp(builder, timestamp): CopyPasteEventAddTimestamp(builder, timestamp)
def CopyPasteEventEnd(builder): return builder.EndObject()
def End(builder): return CopyPasteEventEnd(builder)

# ---------- WindowSwitchEvent ----------
class WindowSwitchEvent(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = WindowSwitchEvent()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsWindowSwitchEvent(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def PreviousWindow(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def CurrentWindow(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def Timestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def WindowSwitchEventStart(builder): builder.StartObject(3)
def Start(builder): WindowSwitchEventStart(builder)
def WindowSwitchEventAddPreviousWindow(builder, previousWindow): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(previousWindow), 0)
def AddPreviousWindow(builder, previousWindow): WindowSwitchEventAddPreviousWindow(builder, previousWindow)
def WindowSwitchEventAddCurrentWindow(builder, currentWindow): builder.PrependUOffsetTRelativeSlot(1, flatbuffers.number_types.UOffsetTFlags.py_type(currentWindow), 0)
def AddCurrentWindow(builder, currentWindow): WindowSwitchEventAddCurrentWindow(builder, currentWindow)
def WindowSwitchEventAddTimestamp(builder, timestamp): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(timestamp), 0)
def AddTimestamp(builder, timestamp): WindowSwitchEventAddTimestamp(builder, timestamp)
def WindowSwitchEventEnd(builder): return builder.EndObject()
def End(builder): return WindowSwitchEventEnd(builder)

# ---------- ScrollEvent ----------
class ScrollEvent(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = ScrollEvent()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsScrollEvent(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def AreaId(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def ScrollValue(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int32Flags, o + self._tab.Pos)
        return 0
    def SpeedPxS(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Float32Flags, o + self._tab.Pos)
        return 0.0
    def Timestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def ScrollEventStart(builder): builder.StartObject(4)
def Start(builder): ScrollEventStart(builder)
def ScrollEventAddAreaId(builder, areaId): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(areaId), 0)
def AddAreaId(builder, areaId): ScrollEventAddAreaId(builder, areaId)
def ScrollEventAddScrollValue(builder, scrollValue): builder.PrependInt32Slot(1, scrollValue, 0)
def AddScrollValue(builder, scrollValue): ScrollEventAddScrollValue(builder, scrollValue)
def ScrollEventAddSpeedPxS(builder, speedPxS): builder.PrependFloat32Slot(2, speedPxS, 0.0)
def AddSpeedPxS(builder, speedPxS): ScrollEventAddSpeedPxS(builder, speedPxS)
def ScrollEventAddTimestamp(builder, timestamp): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(timestamp), 0)
def AddTimestamp(builder, timestamp): ScrollEventAddTimestamp(builder, timestamp)
def ScrollEventEnd(builder): return builder.EndObject()
def End(builder): return ScrollEventEnd(builder)

# ---------- ExamEvent ----------
class ExamEvent(object):
    __slots__ = ['_tab']
    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = ExamEvent()
        x.Init(buf, n + offset)
        return x
    @classmethod
    def GetRootAsExamEvent(cls, buf, offset=0):
        return cls.GetRootAs(buf, offset)
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)
    def EventType(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def Details(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            a = self._tab.Vector(o)
            return self._tab.String(a + flatbuffers.number_types.UOffsetTFlags.py_type(j * 4))
        return ""
    def DetailsLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0
    def DetailsIsNone(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        return o == 0
    def Subject(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None
    def Timestamp(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

def ExamEventStart(builder): builder.StartObject(4)
def Start(builder): ExamEventStart(builder)
def ExamEventAddEventType(builder, eventType): builder.PrependUOffsetTRelativeSlot(0, flatbuffers.number_types.UOffsetTFlags.py_type(eventType), 0)
def AddEventType(builder, eventType): ExamEventAddEventType(builder, eventType)
def ExamEventAddDetails(builder, details): builder.PrependUOffsetTRelativeSlot(1, flatbuffers.number_types.UOffsetTFlags.py_type(details), 0)
def AddDetails(builder, details): ExamEventAddDetails(builder, details)
def ExamEventStartDetailsVector(builder, numElems): return builder.StartVector(4, numElems, 4)
def StartDetailsVector(builder, numElems): return ExamEventStartDetailsVector(builder, numElems)
def ExamEventCreateDetailsVector(builder, data): return builder.CreateVectorOfTables(data)
def CreateDetailsVector(builder, data): ExamEventCreateDetailsVector(builder, data)
def ExamEventAddSubject(builder, subject): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(subject), 0)
def AddSubject(builder, subject): ExamEventAddSubject(builder, subject)
def ExamEventAddTimestamp(builder, timestamp): builder.PrependUOffsetTRelativeSlot(3, flatbuffers.number_types.UOffsetTFlags.py_type(timestamp), 0)
def AddTimestamp(builder, timestamp): ExamEventAddTimestamp(builder, timestamp)
def ExamEventEnd(builder): return builder.EndObject()
def End(builder): return ExamEventEnd(builder)

# ============================================================
# End of FlatBuffers merged code
# ============================================================

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
parent_dir = os.path.dirname(SCRIPT_DIR)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import from token_manager
from token_manager import get_current_room, get_token, is_authenticated, get_user_data, get_username, get_auth_headers

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QMessageBox, QScrollArea,
    QRadioButton, QButtonGroup, QCheckBox, QGroupBox, QLineEdit,
    QProgressBar, QDialog, QDialogButtonBox, QSlider, QSizePolicy, QFrame,
    QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QObject, QEvent, QDateTime, QRectF
from PySide6.QtGui import QFont, QPixmap, QColor, QMovie, QPainter, QLinearGradient, QBrush, QPainterPath, QPalette
import config

# Security Configuration
MAX_MESSAGE_SIZE = 10 * 1024 * 1024
MAX_RECONNECT_ATTEMPTS = 5
ALLOWED_HOSTS = config.ALLOWED_HOSTS if hasattr(config, 'ALLOWED_HOSTS') else ['localhost', '127.0.0.1']
port = config.MAIN_SERVER_PORT if hasattr(config, 'MAIN_SERVER_PORT') else 5002
ROOM_ID = 'room1'
PASSWORD = ''

# ============================================================
# UI Components (Styled widgets)
# ============================================================
class QualityGifLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.movie = None
        self.current_pixmap = None
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background: white; border-radius: 15px;")

    def setMovie(self, movie):
        if self.movie:
            try:
                self.movie.frameChanged.disconnect(self.update_frame)
            except:
                pass
        super().setMovie(movie)
        self.movie = movie
        if self.movie:
            self.movie.frameChanged.connect(self.update_frame)
            self.movie.start()
            self.update_frame()

    def update_frame(self):
        if self.movie:
            self.current_pixmap = self.movie.currentPixmap()
            self.update()

    def paintEvent(self, event):
        if self.current_pixmap and not self.current_pixmap.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            scaled_pixmap = self.current_pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            super().paintEvent(event)

class StyledLabel(QLabel):
    def __init__(self, text="", color="#2d3748", font_size=14, bold=False, parent=None):
        super().__init__(text, parent)
        weight = "bold" if bold else "normal"
        self.setStyleSheet(f"QLabel {{ color: {color}; font-size: {font_size}px; font-weight: {weight}; background: transparent; }}")

class StyledTitleLabel(QLabel):
    def __init__(self, text="", font_size=48, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"QLabel {{ font-size: {font_size}px; font-weight: 800; color: white; background: transparent; }}")

class StyledGroupBox(QGroupBox):
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox { border: 1px solid #e0e0e0; border-radius: 15px; margin-top: 16px; padding: 20px; background: white; color: #2d3748; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #667eea; font-weight: 600; font-size: 16px; padding: 0 10px; }
        """)

class StyledRadioButton(QRadioButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QRadioButton { spacing: 8px; color: #2d3748; font-size: 14px; padding: 5px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; margin-bottom: 4px; }
            QRadioButton:hover { background: #e2e8f0; }
            QRadioButton::indicator { width: 16px; height: 16px; }
            QRadioButton::indicator:checked { background: #667eea; border-radius: 8px; }
        """)

class StyledCheckBox(QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QCheckBox { spacing: 8px; color: #2d3748; font-size: 14px; padding: 5px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; margin-bottom: 4px; }
            QCheckBox:hover { background: #e2e8f0; }
            QCheckBox::indicator { width: 16px; height: 16px; }
            QCheckBox::indicator:checked { background: #667eea; border-radius: 4px; }
        """)

class StyledTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit { border: 1px solid #e0e0e0; border-radius: 10px; padding: 12px; font-size: 14px; background: white; color: #1f2937; }
            QTextEdit:focus { border: 2px solid #667eea; }
        """)

class StyledPushButton(QPushButton):
    def __init__(self, text="", parent=None, gradient_start="#667eea", gradient_end="#764ba2"):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {gradient_start}, stop:1 {gradient_end});
                color: white; border: none; border-radius: 25px; font-size: 16px; font-weight: bold; }}
            QPushButton:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {gradient_end}, stop:1 {gradient_start}); }}
            QPushButton:pressed {{ opacity: 0.85; }}
            QPushButton:disabled {{ background: #cbd5e1; color: #8e8e93; }}
        """)

class StyledExitButton(QPushButton):
    def __init__(self, text="Exit", parent=None):
        super().__init__(text, parent)
        self.setFixedSize(80, 35)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #ef4444, stop:1 #dc2626);
                color: white; border: none; border-radius: 18px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #dc2626, stop:1 #b91c1c); }
            QPushButton:pressed { opacity: 0.85; }
        """)

class StyledProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QProgressBar { border: none; border-radius: 6px; background-color: rgba(255,255,255,0.2); text-align: center; color: white; font-weight: bold; font-size: 11px; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #60b5ff, stop:1 #0a74d9); border-radius: 6px; }
        """)

class StyledScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QScrollArea { background: rgba(255,255,255,0.95); border-radius: 20px; border: none; }
            QScrollBar:vertical { border: none; background: #f0f0f0; width: 10px; border-radius: 5px; }
            QScrollBar::handle:vertical { background: #667eea; border-radius: 5px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #764ba2; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

class StyledLogoLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border-radius: 15px; background-color: transparent; margin: 0; padding: 0;")

# ============================================================
# Placeholder Page (for when quiz is not available)
# ============================================================
class PlaceholderPage(QWidget):
    def __init__(self, title, message="This module is not available yet.", icon="📄", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(24)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 80px; color: rgba(255,255,255,0.8); background: transparent;")
        layout.addWidget(icon_label)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 28px; font-weight: 600; color: white; letter-spacing: -0.5px; background: transparent;")
        layout.addWidget(title_label)
        message_label = QLabel(message)
        message_label.setStyleSheet("font-size: 15px; color: rgba(255,255,255,0.7); padding: 10px 30px; background: transparent;")
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)
        badge = QFrame()
        badge.setFixedSize(120, 32)
        badge.setStyleSheet("QFrame { background: rgba(255,255,255,0.2); border-radius: 16px; }")
        badge_layout = QHBoxLayout(badge)
        badge_label = QLabel("🚧 Coming Soon")
        badge_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 13px; font-weight: 500; background: transparent;")
        badge_layout.addWidget(badge_label)
        layout.addWidget(badge)

# ============================================================
# FlatBuffers Message Builder
# ============================================================
class FlatBuffersMessageBuilder:
    def __init__(self, student_name, room_id, session_id):
        self.student_name = student_name
        self.room_id = room_id
        self.session_id = session_id
        self.event_queue = None

    def set_event_queue(self, event_queue):
        self.event_queue = event_queue

    def _build_message(self, event_type, build_event_func):
        builder = flatbuffers.Builder(1024)
        event_offset = build_event_func(builder)
        student_name_str = builder.CreateString(self.student_name)
        room_id_str = builder.CreateString(self.room_id)
        session_id_str = builder.CreateString(self.session_id or "")
        client_ts = builder.CreateString(datetime.now().isoformat())
        BehavioralMessageStart(builder)
        BehavioralMessageAddStudentName(builder, student_name_str)
        BehavioralMessageAddRoomId(builder, room_id_str)
        BehavioralMessageAddSessionId(builder, session_id_str)
        BehavioralMessageAddEventType(builder, event_type)
        BehavioralMessageAddDataType(builder, event_type)
        BehavioralMessageAddData(builder, event_offset)
        BehavioralMessageAddClientTimestamp(builder, client_ts)
        root = BehavioralMessageEnd(builder)
        builder.Finish(root)
        return bytes(builder.Output())

    def send_key_press(self, key, widget_id, text_length, modifiers):
        if not self.event_queue: return
        def build_event(builder):
            key_str = builder.CreateString(key)
            widget_str = builder.CreateString(widget_id)
            modifiers_str = builder.CreateString(modifiers)
            timestamp_str = builder.CreateString(datetime.now().isoformat())
            KeyPressEventStart(builder)
            KeyPressEventAddKey(builder, key_str)
            KeyPressEventAddWidgetId(builder, widget_str)
            KeyPressEventAddTextLength(builder, text_length)
            KeyPressEventAddModifiers(builder, modifiers_str)
            KeyPressEventAddTimestamp(builder, timestamp_str)
            return KeyPressEventEnd(builder)
        try:
            message = self._build_message(EventType.KeyPress, build_event)
            self.event_queue.put(message)
        except Exception as e:
            print(f"Error creating FlatBuffers keypress: {e}")

    def send_mouse_move(self, widget_id, hover_duration_ms, current_value):
        if not self.event_queue: return
        def build_event(builder):
            widget_str = builder.CreateString(widget_id)
            value_str = builder.CreateString(current_value[:100])
            ts_str = builder.CreateString(datetime.now().isoformat())
            MouseMoveEventStart(builder)
            MouseMoveEventAddWidgetId(builder, widget_str)
            MouseMoveEventAddHoverDurationMs(builder, hover_duration_ms)
            MouseMoveEventAddCurrentValue(builder, value_str)
            MouseMoveEventAddTimestamp(builder, ts_str)
            return MouseMoveEventEnd(builder)
        try:
            message = self._build_message(EventType.MouseMove, build_event)
            self.event_queue.put(message)
        except Exception as e:
            print(f"Error creating FlatBuffers mousemove: {e}")

    def send_mouse_click(self, button_id, hover_duration_ms, button_text):
        if not self.event_queue: return
        def build_event(builder):
            button_id_str = builder.CreateString(button_id)
            button_text_str = builder.CreateString(button_text)
            ts_str = builder.CreateString(datetime.now().isoformat())
            MouseClickEventStart(builder)
            MouseClickEventAddButtonId(builder, button_id_str)
            MouseClickEventAddHoverDurationMs(builder, hover_duration_ms)
            MouseClickEventAddButtonText(builder, button_text_str)
            MouseClickEventAddTimestamp(builder, ts_str)
            return MouseClickEventEnd(builder)
        try:
            message = self._build_message(EventType.MouseClick, build_event)
            self.event_queue.put(message)
        except Exception as e:
            print(f"Error creating FlatBuffers click: {e}")

    def send_copy_paste(self, action, content_length, content_preview, widget_id):
        if not self.event_queue: return
        def build_event(builder):
            action_str = builder.CreateString(action)
            preview_str = builder.CreateString(content_preview[:100])
            widget_str = builder.CreateString(widget_id)
            ts_str = builder.CreateString(datetime.now().isoformat())
            CopyPasteEventStart(builder)
            CopyPasteEventAddAction(builder, action_str)
            CopyPasteEventAddContentLength(builder, content_length)
            CopyPasteEventAddContentPreview(builder, preview_str)
            CopyPasteEventAddWidgetId(builder, widget_str)
            CopyPasteEventAddTimestamp(builder, ts_str)
            return CopyPasteEventEnd(builder)
        try:
            message = self._build_message(EventType.CopyPaste, build_event)
            self.event_queue.put(message)
        except Exception as e:
            print(f"Error creating FlatBuffers copypaste: {e}")

    def send_window_switch(self, previous_window, current_window):
        if not self.event_queue: return
        def build_event(builder):
            prev_str = builder.CreateString(previous_window[:100])
            curr_str = builder.CreateString(current_window[:100])
            ts_str = builder.CreateString(datetime.now().isoformat())
            WindowSwitchEventStart(builder)
            WindowSwitchEventAddPreviousWindow(builder, prev_str)
            WindowSwitchEventAddCurrentWindow(builder, curr_str)
            WindowSwitchEventAddTimestamp(builder, ts_str)
            return WindowSwitchEventEnd(builder)
        try:
            message = self._build_message(EventType.WindowSwitch, build_event)
            self.event_queue.put(message)
        except Exception as e:
            print(f"Error creating FlatBuffers windowswitch: {e}")

    def send_scroll(self, area_id, scroll_value, speed_px_s):
        if not self.event_queue: return
        def build_event(builder):
            area_str = builder.CreateString(area_id)
            ts_str = builder.CreateString(datetime.now().isoformat())
            ScrollEventStart(builder)
            ScrollEventAddAreaId(builder, area_str)
            ScrollEventAddScrollValue(builder, scroll_value)
            ScrollEventAddSpeedPxS(builder, speed_px_s)
            ScrollEventAddTimestamp(builder, ts_str)
            return ScrollEventEnd(builder)
        try:
            message = self._build_message(EventType.Scroll, build_event)
            self.event_queue.put(message)
        except Exception as e:
            print(f"Error creating FlatBuffers scroll: {e}")

    def send_mouse_enter(self, widget_id, current_value):
        if not self.event_queue: return
        def build_event(builder):
            widget_str = builder.CreateString(widget_id)
            value_str = builder.CreateString(current_value[:100])
            ts_str = builder.CreateString(datetime.now().isoformat())
            MouseEnterEventStart(builder)
            MouseEnterEventAddWidgetId(builder, widget_str)
            MouseEnterEventAddCurrentValue(builder, value_str)
            MouseEnterEventAddTimestamp(builder, ts_str)
            return MouseEnterEventEnd(builder)
        try:
            message = self._build_message(EventType.MouseEnter, build_event)
            self.event_queue.put(message)
        except Exception as e:
            print(f"Error sending mouse enter: {e}")

    def send_mouse_leave(self, widget_id, hover_duration_ms, current_value):
        if not self.event_queue: return
        def build_event(builder):
            widget_str = builder.CreateString(widget_id)
            value_str = builder.CreateString(current_value[:100])
            ts_str = builder.CreateString(datetime.now().isoformat())
            MouseLeaveEventStart(builder)
            MouseLeaveEventAddWidgetId(builder, widget_str)
            MouseLeaveEventAddHoverDurationMs(builder, hover_duration_ms)
            MouseLeaveEventAddCurrentValue(builder, value_str)
            MouseLeaveEventAddTimestamp(builder, ts_str)
            return MouseLeaveEventEnd(builder)
        try:
            message = self._build_message(EventType.MouseLeave, build_event)
            self.event_queue.put(message)
        except Exception as e:
            print(f"Error sending mouse leave: {e}")

    def send_focus_in(self, widget_id, hover_duration_ms, current_value):
        if not self.event_queue: return
        def build_event(builder):
            widget_str = builder.CreateString(widget_id)
            value_str = builder.CreateString(current_value[:100])
            ts_str = builder.CreateString(datetime.now().isoformat())
            FocusInEventStart(builder)
            FocusInEventAddWidgetId(builder, widget_str)
            FocusInEventAddHoverDurationMs(builder, hover_duration_ms)
            FocusInEventAddCurrentValue(builder, value_str)
            FocusInEventAddTimestamp(builder, ts_str)
            return FocusInEventEnd(builder)
        try:
            message = self._build_message(EventType.FocusIn, build_event)
            self.event_queue.put(message)
        except Exception as e:
            print(f"Error sending focus in: {e}")

    def send_focus_out(self, widget_id, current_value):
        if not self.event_queue: return
        def build_event(builder):
            widget_str = builder.CreateString(widget_id)
            value_str = builder.CreateString(current_value[:100])
            ts_str = builder.CreateString(datetime.now().isoformat())
            FocusOutEventStart(builder)
            FocusOutEventAddWidgetId(builder, widget_str)
            FocusOutEventAddCurrentValue(builder, value_str)
            FocusOutEventAddTimestamp(builder, ts_str)
            return FocusOutEventEnd(builder)
        try:
            message = self._build_message(EventType.FocusOut, build_event)
            self.event_queue.put(message)
        except Exception as e:
            print(f"Error sending focus out: {e}")

    def send_exam_event(self, event_type_str, details_list, subject):
        if not self.event_queue: return
        def build_event(builder):
            event_type_str_obj = builder.CreateString(event_type_str)
            detail_offsets = []
            for detail in details_list:
                detail_str = builder.CreateString(detail)
                detail_offsets.append(detail_str)
            ExamEventStartDetailsVector(builder, len(detail_offsets))
            for offset in reversed(detail_offsets):
                builder.PrependUOffsetTRelative(offset)
            details_vector = builder.EndVector(len(detail_offsets))
            ExamEventStart(builder)
            ExamEventAddEventType(builder, event_type_str_obj)
            ExamEventAddDetails(builder, details_vector)
            return ExamEventEnd(builder)
        try:
            message = self._build_message(EventType.ExamEvent, build_event)
            self.event_queue.put(message)
        except Exception as e:
            print(f"Error creating FlatBuffers exam event: {e}")

# ============================================================
# FlatBuffers WebSocket Client
# ============================================================
class FlatBuffersBehavioralClient:
    def __init__(self, token, room_id, student_name):
        self.token = token
        self.room_id = room_id
        self.student_name = student_name
        self.websocket = None
        self.event_queue = queue.Queue()
        self.running = False
        self.thread = None
        self.loop = None
        self.session_id = None
        self._closing = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.ssl_context = None
        self.message_builder = FlatBuffersMessageBuilder(student_name, room_id, self.session_id)
        self.message_builder.set_event_queue(self.event_queue)

    def start(self):
        if self.running: return
        self.running = True
        self._closing = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("✅ FlatBuffers Behavioral Client started")

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._connect_and_process())

    async def _connect_and_process(self):
        while self.running and not self._closing:
            try:
                await self._connect()
                if self.websocket:
                    await self._process_queue()
            except Exception as e:
                print(f"FlatBuffers WS error: {e}")
                if self.reconnect_attempts < self.max_reconnect_attempts and not self._closing:
                    self.reconnect_attempts += 1
                    wait_time = 2 ** self.reconnect_attempts
                    print(f"FlatBuffers WS: Reconnecting in {wait_time}s (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
                    await asyncio.sleep(wait_time)
                else:
                    if not self._closing:
                        print("FlatBuffers WS: Max reconnection attempts reached. Stopping.")
                    self.running = False
                    break

    async def _connect(self):
        server_host = config.BEHAVIORAL_SERVER_IP if hasattr(config, 'BEHAVIORAL_SERVER_IP') else config.SERVER_IP
        server_port = config.BEHAVIORAL_SERVER_PORT if hasattr(config, 'BEHAVIORAL_SERVER_PORT') else 5023
        uri = f"wss://{server_host}:{server_port}/ws"
        try:
            print(f"FlatBuffers WS: Connecting to {uri}...")
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
            self.websocket = await websockets.connect(
                uri, ssl=self.ssl_context, ping_interval=20, ping_timeout=10,
                max_size=10 * 1024 * 1024, close_timeout=5
            )
            print(f"FlatBuffers WS: Connected! Sending authentication...")
            auth_msg = {
                "type": "student", "token": self.token,
                "room_id": self.room_id, "student_name": self.student_name
            }
            await self.websocket.send(json.dumps(auth_msg))
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            resp_data = json.loads(response)
            if resp_data.get("status") == "connected":
                self.session_id = resp_data.get("session_id")
                self.message_builder.session_id = self.session_id
                print(f"✅ FlatBuffers WS: Authenticated! Session ID: {self.session_id}")
                self.reconnect_attempts = 0
                return True
            else:
                raise Exception(f"Auth failed: {resp_data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ FlatBuffers WS connection failed: {e}")
            if self.websocket:
                try: await self.websocket.close()
                except: pass
                self.websocket = None
            raise

    async def _process_queue(self):
        while self.running and self.websocket and not self._closing:
            try:
                item = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: self.event_queue.get(timeout=1.0)
                )
                if item is None: continue
                if isinstance(item, bytes):
                    await self.websocket.send(item)
                else:
                    await self.websocket.send(item)
            except queue.Empty:
                continue
            except websockets.exceptions.ConnectionClosed as e:
                print(f"FlatBuffers WS connection closed: {e}")
                break
            except Exception as e:
                print(f"FlatBuffers WS send error: {e}")
                break

    def send_key_press(self, key, widget_id, text_length, modifiers):
        self.message_builder.send_key_press(key, widget_id, text_length, modifiers)

    def send_mouse_move(self, widget_id, hover_duration_ms, current_value):
        self.message_builder.send_mouse_move(widget_id, hover_duration_ms, current_value)

    def send_mouse_click(self, button_id, hover_duration_ms, button_text):
        self.message_builder.send_mouse_click(button_id, hover_duration_ms, button_text)

    def send_copy_paste(self, action, content_length, content_preview, widget_id):
        self.message_builder.send_copy_paste(action, content_length, content_preview, widget_id)

    def send_window_switch(self, previous_window, current_window):
        self.message_builder.send_window_switch(previous_window, current_window)

    def send_scroll(self, area_id, scroll_value, speed_px_s):
        self.message_builder.send_scroll(area_id, scroll_value, speed_px_s)

    def send_mouse_enter(self, widget_id, current_value):
        self.message_builder.send_mouse_enter(widget_id, current_value)

    def send_mouse_leave(self, widget_id, hover_duration_ms, current_value):
        self.message_builder.send_mouse_leave(widget_id, hover_duration_ms, current_value)

    def send_focus_in(self, widget_id, hover_duration_ms, current_value):
        self.message_builder.send_focus_in(widget_id, hover_duration_ms, current_value)

    def send_focus_out(self, widget_id, current_value):
        self.message_builder.send_focus_out(widget_id, current_value)

    def send_typing_speed(self, kps, widget_id):
        if not self.running or self._closing: return
        details = [f"kps:{kps:.2f}", f"widget:{widget_id}", f"window:2.0s"]
        self.send_exam_event("typing_speed", details, "typing")

    def send_flight_time(self, flight_ms, widget_id):
        if not self.running or self._closing: return
        details = [f"flight_ms:{flight_ms:.1f}", f"widget:{widget_id}"]
        self.send_exam_event("flight_time", details, "timing")

    def send_hold_duration(self, hold_ms, key, widget_id):
        if not self.running or self._closing: return
        details = [f"hold_ms:{hold_ms:.1f}", f"key:{key}", f"widget:{widget_id}"]
        self.send_exam_event("hold_duration", details, "timing")

    def send_answer_final(self, widget_id, answer_text, question_num):
        if not self.running or self._closing: return
        preview = answer_text[:100] + "..." if len(answer_text) > 100 else answer_text
        details = [f"widget:{widget_id}", f"question:{question_num}", f"value:{preview}", f"length:{len(answer_text)}"]
        self.send_exam_event("answer_final", details, "answers")

    def send_text_cleared(self, widget_id, previous_length, question_num):
        if not self.running or self._closing: return
        details = [f"widget:{widget_id}", f"question:{question_num}", f"previous_length:{previous_length}"]
        self.send_exam_event("text_cleared", details, "answers")

    def send_answer_changed(self, question_num, option_idx, answer_type, old_value, new_value):
        if not self.running or self._closing: return
        details = [f"question:{question_num}", f"option:{option_idx}", f"type:{answer_type}",
                   f"old:{old_value}", f"new:{new_value}"]
        self.send_exam_event("answer_changed", details, "answers")

    def send_idle_detected(self, idle_seconds, widget_id):
        if not self.running or self._closing: return
        details = [f"idle_seconds:{idle_seconds:.1f}", f"widget:{widget_id}"]
        self.send_exam_event("idle_detected", details, "activity")

    def send_quiz_end(self, reason, time_taken_seconds):
        if not self.running or self._closing: return
        minutes = int(time_taken_seconds // 60)
        seconds = int(time_taken_seconds % 60)
        details = [f"reason:{reason}", f"time_taken:{minutes:02d}:{seconds:02d}", f"seconds:{time_taken_seconds:.1f}"]
        self.send_exam_event("quiz_end", details, "exam")

    def send_exam_event(self, event_type_str, details_list, subject):
        self.message_builder.send_exam_event(event_type_str, details_list, subject)

    def close_connection(self):
        print("FlatBuffers WS: Closing connection securely...")
        self._closing = True
        self.running = False
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self._close_websocket(), self.loop).result(timeout=2)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
        print("FlatBuffers WS: Connection closed securely.")

    async def _close_websocket(self):
        if self.websocket:
            try: await self.websocket.close()
            except: pass
            self.websocket = None

    def stop(self):
        self.close_connection()

# ============================================================
# Copy-Paste Detector
# ============================================================
class CopyPasteDetector(QObject):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.last_copy_time = 0
        self.last_paste_time = 0
        self.last_window_change_time = 0
        self.last_active_window = ""
        self.clipboard_history = []
        self.max_clipboard_history = 10
        self.detection_active = True
        self.setup_detection()

    def setup_detection(self):
        print("🔍 Copy-Paste detection activated")
        self.clipboard_timer = QTimer(self)
        self.clipboard_timer.timeout.connect(self.check_clipboard)
        self.clipboard_timer.start(1000)
        self.window_check_timer = QTimer(self)
        self.window_check_timer.timeout.connect(self.check_active_window)
        self.window_check_timer.start(2000)

    def check_clipboard(self):
        if not self.detection_active: return
        try:
            try:
                import pyperclip
                current_content = pyperclip.paste()
            except ImportError:
                return
            if current_content:
                if self.clipboard_history and current_content != self.clipboard_history[-1]:
                    self.detect_copy_action(current_content)
                self.clipboard_history.append(current_content)
                if len(self.clipboard_history) > self.max_clipboard_history:
                    self.clipboard_history.pop(0)
        except:
            pass

    def detect_copy_action(self, content):
        now = time.time()
        if now - self.last_copy_time < 3: return
        self.last_copy_time = now
        content_length = len(content)
        content_preview = content[:50] + "..." if len(content) > 50 else content
        content_preview_clean = content_preview.replace('\n', ' ').replace('\r', ' ').strip()
        if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
            self.tracker.behavioral_client.send_copy_paste("copy", content_length, content_preview_clean, "clipboard")

    def detect_paste_action(self, widget_id, pasted_text):
        now = time.time()
        if now - self.last_paste_time < 3: return
        self.last_paste_time = now
        text_length = len(pasted_text)
        text_preview = pasted_text[:30] + "..." if len(pasted_text) > 30 else pasted_text
        text_preview_clean = text_preview.replace('\n', ' ').replace('\r', ' ').strip()
        if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
            self.tracker.behavioral_client.send_copy_paste("paste", text_length, text_preview_clean, widget_id)

    def check_active_window(self):
        if not self.detection_active: return
        try:
            try:
                import pyautogui
                active_window = pyautogui.getActiveWindow()
                if active_window:
                    current_title = active_window.title
                    if current_title != self.last_active_window:
                        now = time.time()
                        if now - self.last_window_change_time > 5:
                            self.last_window_change_time = now
                            if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                                self.tracker.behavioral_client.send_window_switch(self.last_active_window, current_title)
                        self.last_active_window = current_title
            except ImportError:
                pass
        except:
            pass

    def detect_keyboard_shortcut(self, keys):
        keys_lower = keys.lower()
        if keys_lower in ['ctrl+c', 'ctrl+insert', 'cmd+c']:
            return "copy"
        elif keys_lower in ['ctrl+v', 'shift+insert', 'cmd+v']:
            return "paste"
        elif keys_lower in ['ctrl+x', 'shift+delete', 'cmd+x']:
            return "cut"
        return None

    def stop_detection(self):
        self.detection_active = False
        if hasattr(self, 'clipboard_timer'):
            self.clipboard_timer.stop()
        if hasattr(self, 'window_check_timer'):
            self.window_check_timer.stop()

# ============================================================
# Exam Event Tracker
# ============================================================
class ExamEventTracker(QObject):
    def __init__(self, student_name, exam_id):
        super().__init__()
        self.student_name = student_name
        self.exam_id = exam_id
        self.exam_start_time = None
        self.events = []
        self.last_event_type = None
        self.last_event_subject = None
        self.last_event_time = 0
        self.copy_paste_detector = None
        self.last_activity_time = time.time()
        self.idle_timer = None
        self.idle_check_interval = 5000
        self.last_key_press_time = None
        self.last_key_release_time = None
        self.current_pressed_key = None
        self.key_hold_timer = None

        token = get_token() or ""
        room_id = get_current_room() or ROOM_ID
        self.behavioral_client = FlatBuffersBehavioralClient(token, room_id, student_name)
        self.behavioral_client.start()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.sent_events_log = f"sent_events_{student_name}_{timestamp}.log"
        self.sent_log_file = open(self.sent_events_log, 'w', encoding='utf-8')
        self.sent_log_file.write(f"# Sent behavioral events log for {student_name}\n")
        self.sent_log_file.write(f"# Exam ID: {exam_id}\n")
        self.sent_log_file.write(f"# Started at: {datetime.now().isoformat()}\n")
        self.sent_log_file.write("#" + "="*60 + "\n")
        self.sent_log_file.flush()
        print(f"📝 Sent events log: {self.sent_events_log}")
        self.setup_logging()

    def setup_logging(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = f"exam_events_{self.student_name}_{timestamp}.log"
        print(f"📝 Event logging: {self.log_filename}")
        try:
            self.copy_paste_detector = CopyPasteDetector(self)
            print("🔍 Copy-paste detection activated")
        except Exception as e:
            print(f"⚠️ Failed to activate copy-paste detection: {e}")

    def log_event(self, event_type, details_list, subject=None, extra=None):
        try:
            ts = datetime.now()
            ts_str = ts.isoformat()
            ts_ms = int(ts.timestamp() * 1000)
            if (event_type == self.last_event_type and subject == self.last_event_subject and
                ts_ms - self.last_event_time < 100):
                return
            self.last_event_type = event_type
            self.last_event_subject = subject
            self.last_event_time = ts_ms
            event = {"timestamp": ts_str, "event_type": event_type, "details": details_list,
                     "student": self.student_name, "exam_id": self.exam_id}
            if subject:
                event["subject"] = subject
            if extra and isinstance(extra, dict):
                event.update(extra)
            self.events.append(event)
            log_line = f'["{ts_str}", ["{event_type}"], {details_list}]'
            print(log_line)
            with open(self.log_filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"⚠️ Error logging event: {e}")

    def start_idle_monitoring(self):
        self.last_activity_time = time.time()
        if self.idle_timer:
            self.idle_timer.stop()
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self.check_idle)
        self.idle_timer.start(self.idle_check_interval)

    def check_idle(self):
        now = time.time()
        idle_seconds = now - self.last_activity_time
        if idle_seconds > 30:
            if self.behavioral_client:
                self.behavioral_client.send_idle_detected(idle_seconds, "global")
            self.log_event("idle_detected", [f"idle_seconds:{idle_seconds:.1f}"], subject="activity")
        self.last_activity_time = now

    def update_activity(self):
        self.last_activity_time = time.time()

    def stop(self):
        if self.behavioral_client:
            self.behavioral_client.stop()
        if hasattr(self, 'sent_log_file') and not self.sent_log_file.closed:
            self.sent_log_file.write(f"\n# Stopped at: {datetime.now().isoformat()}\n")
            self.sent_log_file.close()
            print(f"📝 Sent events log saved: {self.sent_events_log}")

# ============================================================
# Event Filters (Mouse, Input, Button, Scroll)
# ============================================================
class MouseAreaFilter(QObject):
    def __init__(self, widget_id, tracker, area_name="area", widget_ref=None):
        super().__init__()
        self.widget_id = widget_id
        self.tracker = tracker
        self.area_name = area_name
        self.widget_ref = widget_ref
        self.hover_start = None
        self.last_mouse_move_time = 0

    def eventFilter(self, obj, event):
        try:
            now_ms = QDateTime.currentDateTime().toMSecsSinceEpoch()
            if event.type() == QEvent.Enter:
                if hasattr(self.tracker, "update_activity"):
                    self.tracker.update_activity()
                self.hover_start = now_ms
                self.last_mouse_move_time = now_ms
                current_value = self.get_current_value(obj)
                if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                    self.tracker.behavioral_client.send_mouse_enter(self.widget_id, current_value[:100])
                self.tracker.log_event("area_enter", [f"Entered {self.area_name} {self.widget_id}", f"current_value:{current_value}"],
                                       subject=self.widget_id, extra={"value": current_value})
            elif event.type() == QEvent.MouseMove:
                if not self.hover_start:
                    self.hover_start = now_ms
                if now_ms - self.last_mouse_move_time > 200:
                    self.last_mouse_move_time = now_ms
                    duration_s = (now_ms - self.hover_start) / 1000.0
                    current_value = self.get_current_value(obj)
                    if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                        self.tracker.behavioral_client.send_mouse_move(self.widget_id, int(duration_s * 1000), current_value[:100])
            elif event.type() == QEvent.Leave:
                if self.hover_start:
                    duration_s = (now_ms - self.hover_start) / 1000.0
                    current_value = self.get_current_value(obj)
                    if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                        self.tracker.behavioral_client.send_mouse_leave(self.widget_id, int(duration_s * 1000), current_value[:100])
                self.hover_start = None
                self.last_mouse_move_time = 0
        except Exception as e:
            pass
        return False

    def get_current_value(self, obj):
        try:
            if self.area_name == "time":
                return obj.text() if hasattr(obj, 'text') else ""
            elif self.area_name == "question":
                text = obj.text() if hasattr(obj, 'text') else ""
                return text[:100] + "..." if len(text) > 100 else text
            elif self.area_name == "progress":
                return f"{obj.value()}%" if hasattr(obj, 'value') else (obj.text() if hasattr(obj, 'text') else "")
            elif self.area_name == "slider":
                return str(obj.value()) if hasattr(obj, 'value') else ""
            elif self.area_name == "radio":
                return "checked" if obj.isChecked() else "unchecked" if hasattr(obj, 'isChecked') else ""
            elif self.area_name == "checkbox":
                return "checked" if obj.isChecked() else "unchecked" if hasattr(obj, 'isChecked') else ""
            elif self.area_name == "text":
                text = obj.toPlainText() if hasattr(obj, 'toPlainText') else (obj.text() if hasattr(obj, 'text') else "")
                return f"length:{len(text)} chars"
            elif self.area_name == "image":
                pixmap = obj.pixmap() if hasattr(obj, 'pixmap') else None
                if pixmap and not pixmap.isNull():
                    return f"image_size:{pixmap.width()}x{pixmap.height()}"
                return ""
            elif self.area_name == "button":
                return obj.text() if hasattr(obj, 'text') else ""
        except Exception as e:
            return f"error_getting_value:{str(e)}"
        return ""

class InputEventFilter(QObject):
    def __init__(self, widget_id, tracker, widget_type="input", widget_ref=None):
        super().__init__()
        self.widget_id = widget_id
        self.tracker = tracker
        self.widget_type = widget_type
        self.widget_ref = widget_ref
        self.hover_start = None
        self.last_click_time = 0
        self.keystrokes = []
        self.last_typing_notify = 0
        self.last_mouse_move_time = 0
        self.last_text_length = 0
        self.last_text_before_paste = ""
        self.last_key_press_time = None
        self.last_key_release_time = None
        self.key_hold_timer = None
        self.key_press_times = []
        self.last_kps_send = 0
        self.typing_speed_timer = 0
        self.key_press_timestamps_for_speed = []
        self.last_text_value = ""

    def eventFilter(self, obj, event):
        try:
            now_ms = QDateTime.currentDateTime().toMSecsSinceEpoch()
            now_s = now_ms / 1000.0
            if event.type() == QEvent.FocusIn:
                if now_s - self.last_click_time < 0.35:
                    return False
                self.last_click_time = now_s
                hover_duration = (now_ms - self.hover_start) / 1000.0 if self.hover_start else None
                current_value = self.get_current_value(obj)
                if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                    self.tracker.behavioral_client.send_focus_in(self.widget_id, int((hover_duration or 0) * 1000), current_value[:100])
                self.tracker.log_event("input_selected", [f"Input {self.widget_id} selected", f"current_value:{current_value}"],
                                       subject=self.widget_id, extra={"hover_s": hover_duration, "value": current_value})
            elif event.type() == QEvent.Enter:
                if hasattr(self.tracker, "update_activity"):
                    self.tracker.update_activity()
                self.hover_start = now_ms
                self.last_mouse_move_time = now_ms
                current_value = self.get_current_value(obj)
                if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                    self.tracker.behavioral_client.send_mouse_enter(self.widget_id, current_value[:100])
            elif event.type() == QEvent.MouseMove:
                if not self.hover_start:
                    self.hover_start = now_ms
                if now_ms - self.last_mouse_move_time > 200:
                    self.last_mouse_move_time = now_ms
                    duration_s = (now_ms - self.hover_start) / 1000.0
                    current_value = self.get_current_value(obj)
                    if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                        self.tracker.behavioral_client.send_mouse_move(self.widget_id, int(duration_s * 1000), current_value[:100])
            elif event.type() == QEvent.Leave:
                if self.hover_start:
                    duration_s = (now_ms - self.hover_start) / 1000.0
                    if duration_s > 0.1:
                        current_value = self.get_current_value(obj)
                        if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                            self.tracker.behavioral_client.send_mouse_leave(self.widget_id, int(duration_s * 1000), current_value[:100])
                self.hover_start = None
                self.last_mouse_move_time = 0
            elif event.type() == QEvent.KeyPress:
                if hasattr(event, 'isAutoRepeat') and event.isAutoRepeat():
                    return False
                current_text = obj.toPlainText() if hasattr(obj, 'toPlainText') else obj.text()
                self.last_text_before_paste = current_text
                key = event.key()
                modifiers = event.modifiers()
                key_press_time = time.time()

                # Typing speed calculation
                self.key_press_timestamps_for_speed.append(key_press_time)
                cutoff = key_press_time - 3.0
                self.key_press_timestamps_for_speed = [ts for ts in self.key_press_timestamps_for_speed if ts > cutoff]
                if len(self.key_press_timestamps_for_speed) >= 2:
                    duration = self.key_press_timestamps_for_speed[-1] - self.key_press_timestamps_for_speed[0]
                    if duration > 0:
                        kps = (len(self.key_press_timestamps_for_speed) - 1) / duration
                        kps = min(20.0, kps)
                        now_ms = int(time.time() * 1000)
                        if now_ms - self.typing_speed_timer > 1000:
                            self.typing_speed_timer = now_ms
                            if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                                self.tracker.behavioral_client.send_typing_speed(kps, self.widget_id)

                # Flight time
                if hasattr(self.tracker, 'last_key_release_time') and self.tracker.last_key_release_time:
                    flight_ms = (key_press_time - self.tracker.last_key_release_time) * 1000.0
                    if 10 < flight_ms < 5000:
                        if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                            self.tracker.behavioral_client.send_flight_time(flight_ms, self.widget_id)

                self.key_press_times.append(key_press_time)
                self.key_press_times = [t for t in self.key_press_times if t > key_press_time - 2.0]
                key_name = self.get_key_name(key)
                if not key_name:
                    key_text = event.text()
                    key_name = key_text if key_text and key_text.isprintable() else f"key_{key}"
                shortcut_parts = []
                if modifiers & Qt.ControlModifier:
                    shortcut_parts.append('ctrl')
                if modifiers & Qt.ShiftModifier:
                    shortcut_parts.append('shift')
                if modifiers & Qt.AltModifier:
                    shortcut_parts.append('alt')
                if modifiers & Qt.MetaModifier:
                    shortcut_parts.append('cmd')
                modifiers_str = '+'.join(shortcut_parts) if shortcut_parts else "none"
                current_text_length = len(current_text) if current_text else 0
                if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                    self.tracker.behavioral_client.send_key_press(key_name, self.widget_id, current_text_length, modifiers_str)
                if key_name and hasattr(self.tracker, 'copy_paste_detector'):
                    shortcut = '+'.join(shortcut_parts + [key_name.lower()]) if shortcut_parts else key_name.lower()
                    action = self.tracker.copy_paste_detector.detect_keyboard_shortcut(shortcut)
                    if action == "paste":
                        QTimer.singleShot(100, lambda: self.check_for_paste(obj))
                self.tracker.current_pressed_key = key_name
                if self.key_hold_timer:
                    self.key_hold_timer.stop()
                self.key_hold_timer = QTimer(self)
                self.key_hold_timer.setSingleShot(True)
                self.key_hold_timer.timeout.connect(lambda: self._send_hold_duration(key_press_time, key_name))
                self.key_hold_timer.start(50)
                self.keystrokes.append(now_ms)
                self.keystrokes = [ts for ts in self.keystrokes if ts > now_ms - 2000]
                if len(self.keystrokes) >= 2:
                    time_span = (self.keystrokes[-1] - self.keystrokes[0]) / 1000.0
                    if time_span > 0:
                        speed = len(self.keystrokes) / time_span
                        if now_ms - self.last_typing_notify > 500:
                            current_value = self.get_current_value(obj)
                            self.tracker.log_event("input_typing", [f"Typing {self.widget_id}", f"speed:{speed:.2f}keys/s", f"current_value:{current_value}"],
                                                   subject=self.widget_id, extra={"speed_kps": speed, "value": current_value})
                            self.last_typing_notify = now_ms
                        if speed > 20:
                            self.tracker.log_event("unnatural_typing_speed", [f"Unnatural typing speed: {speed:.1f} keys/s"],
                                                   subject=self.widget_id, extra={"warning": "possible_paste", "speed": speed})
            elif event.type() == QEvent.FocusOut:
                current_value = self.get_current_value(obj)
                question_num = 0
                match = re.search(r'question_([0-9]+)_text', self.widget_id)
                if match:
                    question_num = int(match.group(1))
                    if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                        full_text = obj.toPlainText() if hasattr(obj, 'toPlainText') else obj.text()
                        self.tracker.behavioral_client.send_answer_final(self.widget_id, full_text, question_num)
                self.last_text_value = current_value
                if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                    self.tracker.behavioral_client.send_focus_out(self.widget_id, current_value[:100])
                self.tracker.log_event("input_deselected", [f"Input {self.widget_id} deselected", f"current_value:{current_value}"],
                                       subject=self.widget_id, extra={"value": current_value})
        except Exception as e:
            pass
        return False

    def _send_hold_duration(self, press_time, key_name):
        release_time = time.time()
        hold_ms = (release_time - press_time) * 1000.0
        if 10 < hold_ms < 3000:
            self.tracker.last_key_release_time = release_time
            if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                self.tracker.behavioral_client.send_hold_duration(hold_ms, key_name, self.widget_id)

    def get_key_name(self, key):
        mapping = {
            Qt.Key_C: 'c', Qt.Key_V: 'v', Qt.Key_X: 'x', Qt.Key_A: 'a', Qt.Key_Z: 'z', Qt.Key_Y: 'y',
            Qt.Key_Insert: 'insert', Qt.Key_Delete: 'delete', Qt.Key_Backspace: 'backspace',
            Qt.Key_Return: 'enter', Qt.Key_Enter: 'enter', Qt.Key_Space: 'space', Qt.Key_Tab: 'tab',
            Qt.Key_Escape: 'escape', Qt.Key_Home: 'home', Qt.Key_End: 'end', Qt.Key_PageUp: 'pageup',
            Qt.Key_PageDown: 'pagedown', Qt.Key_Up: 'up', Qt.Key_Down: 'down', Qt.Key_Left: 'left', Qt.Key_Right: 'right'
        }
        return mapping.get(key, '')

    def get_current_value(self, obj):
        try:
            if self.widget_type == "radio" and hasattr(obj, 'isChecked'):
                text = obj.text() if hasattr(obj, 'text') else ""
                return f"text:{text}, checked:{obj.isChecked()}"
            elif self.widget_type == "checkbox" and hasattr(obj, 'isChecked'):
                text = obj.text() if hasattr(obj, 'text') else ""
                return f"text:{text}, checked:{obj.isChecked()}"
            elif self.widget_type == "text":
                text = obj.toPlainText() if hasattr(obj, 'toPlainText') else (obj.text() if hasattr(obj, 'text') else "")
                return f"length:{len(text)}, preview:{text[:30]}"
        except Exception as e:
            return f"error:{str(e)}"
        return ""

    def check_for_paste(self, obj):
        try:
            text = obj.toPlainText() if hasattr(obj, 'toPlainText') else obj.text()
            if self.last_text_before_paste is not None:
                pasted_text = text[len(self.last_text_before_paste):] if len(text) > len(self.last_text_before_paste) else ""
                if pasted_text and len(pasted_text) > 5 and hasattr(self.tracker, 'copy_paste_detector'):
                    self.tracker.copy_paste_detector.detect_paste_action(self.widget_id, pasted_text)
        except:
            pass

class ButtonEventFilter(QObject):
    def __init__(self, button_id, tracker, button_ref=None):
        super().__init__()
        self.button_id = button_id
        self.tracker = tracker
        self.button_ref = button_ref
        self.hover_start = None
        self.last_click_time = 0
        self.last_mouse_move_time = 0

    def eventFilter(self, obj, event):
        try:
            now_ms = QDateTime.currentDateTime().toMSecsSinceEpoch()
            if event.type() == QEvent.Enter:
                if hasattr(self.tracker, "update_activity"):
                    self.tracker.update_activity()
                self.hover_start = now_ms
                self.last_mouse_move_time = now_ms
                current_value = self.get_current_value(obj)
                if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                    self.tracker.behavioral_client.send_mouse_enter(self.button_id, current_value[:100])
            elif event.type() == QEvent.MouseMove:
                if not self.hover_start:
                    self.hover_start = now_ms
                if now_ms - self.last_mouse_move_time > 200:
                    self.last_mouse_move_time = now_ms
                    duration_s = (now_ms - self.hover_start) / 1000.0
                    current_value = self.get_current_value(obj)
                    if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                        self.tracker.behavioral_client.send_mouse_move(self.button_id, int(duration_s * 1000), current_value[:100])
            elif event.type() == QEvent.Leave:
                if self.hover_start:
                    duration_s = (now_ms - self.hover_start) / 1000.0
                    current_value = self.get_current_value(obj)
                    if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                        self.tracker.behavioral_client.send_mouse_leave(self.button_id, int(duration_s * 1000), current_value[:100])
                self.hover_start = None
                self.last_mouse_move_time = 0
            elif event.type() == QEvent.MouseButtonPress:
                now_s = now_ms / 1000.0
                if now_s - self.last_click_time < 0.35:
                    return False
                self.last_click_time = now_s
                duration_s = (now_ms - self.hover_start) / 1000.0 if self.hover_start else None
                current_value = self.get_current_value(obj)
                if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                    self.tracker.behavioral_client.send_mouse_click(self.button_id, int((duration_s or 0) * 1000), current_value)
        except Exception as e:
            pass
        return False

    def get_current_value(self, obj):
        try:
            return obj.text() if hasattr(obj, 'text') else ""
        except:
            return ""

class ScrollEventFilter(QObject):
    def __init__(self, area_id, tracker):
        super().__init__()
        self.area_id = area_id
        self.tracker = tracker
        self.last_scroll_time = None
        self.last_scroll_value = None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            now_ms = QDateTime.currentDateTime().toMSecsSinceEpoch()
            scroll_value = obj.verticalScrollBar().value() if hasattr(obj, 'verticalScrollBar') else 0
            speed = None
            if self.last_scroll_value is not None and self.last_scroll_time is not None:
                dt_ms = now_ms - self.last_scroll_time
                if dt_ms > 0:
                    dv = scroll_value - self.last_scroll_value
                    speed = dv / (dt_ms / 1000.0)
            if hasattr(self.tracker, 'behavioral_client') and self.tracker.behavioral_client:
                self.tracker.behavioral_client.send_scroll(self.area_id, scroll_value, speed if speed else 0.0)
            self.last_scroll_value = scroll_value
            self.last_scroll_time = now_ms
        return False

# ============================================================
# WebSocket Client for File Upload
# ============================================================
class WebSocketClientUpload:
    def __init__(self):
        self.websocket = None
        self.chunk_size = 64 * 1024
        self._closing = False

    async def connect_to_server(self, token="token123", folder="room1"):
        try:
            ssl_context = ssl._create_unverified_context()
            self.websocket = await websockets.connect(config.UPLOAD_WEBSOCKET_URL, ssl=ssl_context, max_size=50 * 1024 * 1024)
            auth_data = {"token": token, "folder": folder}
            ConnectionManager.log_connection_status("auth_sending", "Sending authentication to upload server")
            await self.websocket.send(json.dumps(auth_data))
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                ConnectionManager.log_connection_status("auth_received", "Received response from upload server")
                try:
                    data = json.loads(response)
                    if data.get("status") == "error":
                        ConnectionManager.log_connection_status("auth_error", f"Server error: {data.get('error')}")
                        return False
                except:
                    pass
                ConnectionManager.log_connection_status("connected", "Connected to upload server")
                return True
            except asyncio.TimeoutError:
                ConnectionManager.log_connection_status("auth_warning", "No auth response (may be normal)")
                ConnectionManager.log_connection_status("connected", "Connected to upload server")
                return True
        except Exception as e:
            ConnectionManager.log_connection_status("error", f"Upload connection error: {str(e)}")
            return False

    async def upload_file(self, folder, file_path, description=""):
        if not self.websocket:
            ConnectionManager.log_connection_status("error", "Not connected to upload server")
            return False
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        try:
            file_hash = self._calculate_file_hash(file_path)
            start_message = {"action": "start_upload", "name": file_name, "size": file_size,
                             "hash": file_hash, "description": description, "resume_point": 0}
            ConnectionManager.log_connection_status("upload_start", f"Starting upload: {file_name} ({file_size:,} bytes)")
            await self.websocket.send(json.dumps(start_message))
            try:
                start_response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
                try:
                    start_data = json.loads(start_response)
                    if start_data.get("action") == "auth_response" and start_data.get("status") == "success":
                        upload_response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
                        start_data = json.loads(upload_response)
                    if start_data.get("status") != "ready":
                        error_msg = start_data.get("error", "Server not ready")
                        ConnectionManager.log_connection_status("upload_error", f"Server not ready: {error_msg}")
                        return False
                except json.JSONDecodeError as e:
                    ConnectionManager.log_connection_status("upload_error", f"Invalid JSON response: {e}")
                    return False
            except asyncio.TimeoutError:
                ConnectionManager.log_connection_status("upload_error", "Timeout waiting for server ready response")
                return False
            uploaded = 0
            chunk_number = 0
            with open(file_path, 'rb') as f:
                while uploaded < file_size:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    chunk_number += 1
                    chunk_message = {"action": "upload_chunk", "name": file_name,
                                     "chunk": base64.b64encode(chunk).decode('utf-8'), "offset": uploaded}
                    await self.websocket.send(json.dumps(chunk_message))
                    uploaded += len(chunk)
                    try:
                        chunk_response = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
                        chunk_data = json.loads(chunk_response)
                        if chunk_data.get("status") != "received":
                            ConnectionManager.log_connection_status("upload_error", f"Chunk rejected: {chunk_data}")
                            return False
                        progress = (uploaded / file_size) * 100
                        if int(progress) % 25 == 0 or uploaded == file_size:
                            ConnectionManager.log_connection_status("upload_progress", f"Progress: {progress:.1f}%")
                    except asyncio.TimeoutError:
                        ConnectionManager.log_connection_status("upload_error", f"Timeout waiting for chunk {chunk_number}")
                        return False
                    await asyncio.sleep(0.01)
            finish_message = {"action": "finish_upload", "name": file_name, "hash": file_hash}
            await self.websocket.send(json.dumps(finish_message))
            try:
                finish_response = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
                finish_data = json.loads(finish_response)
                if finish_data.get("status") == "success":
                    ConnectionManager.log_connection_status("upload_success", f"✅ File uploaded: {file_name}")
                    return True
                else:
                    ConnectionManager.log_connection_status("upload_error", f"❌ Upload failed: {finish_data.get('error')}")
                    return False
            except asyncio.TimeoutError:
                ConnectionManager.log_connection_status("upload_error", "Timeout waiting for final confirmation")
                return False
        except Exception as e:
            ConnectionManager.log_connection_status("upload_error", f"Upload error: {str(e)}")
            return False

    def _calculate_file_hash(self, file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def close(self):
        self._closing = True
        try:
            if self.websocket:
                await self.websocket.close()
                ConnectionManager.log_connection_status("closed", "Upload connection closed securely")
        except:
            pass

# ============================================================
# Connection Manager
# ============================================================
class ConnectionManager:
    @staticmethod
    def log_connection_status(status, details=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        emoji = {"connected": "✅", "connecting": "🔄", "disconnected": "❌", "error": "🚨",
                 "reconnecting": "🔄", "timeout": "⏰", "security_error": "🔒",
                 "message_sent": "📤", "message_received": "📥", "upload_success": "📁",
                 "upload_error": "❌", "upload_start": "🚀", "upload_progress": "📊",
                 "closed": "🔒"}.get(status, "ℹ️")
        print(f"{emoji} [{timestamp}] {status.capitalize()}: {details}")

# ============================================================
# WebSocket Client (Exam Connection)
# ============================================================
class WebSocketClient(QObject):
    message_received = Signal(dict)
    connection_status = Signal(str, str)
    submission_result = Signal(bool, str)
    connection_error = Signal(str)

    def __init__(self):
        super().__init__()
        self.websocket = None
        self.encryption_key = None
        self.cipher = None
        self.connection_secure = False
        self.session_id = None
        self.last_activity = time.time()
        self._closing = False
        self.student_name = get_username() or "Student"
        self.room_id = get_current_room() or ROOM_ID
        self.token = get_token() or ""
        print(f"🔑 WebSocketClient initialized - room: {self.room_id}")
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = MAX_RECONNECT_ATTEMPTS
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                           handlers=[logging.FileHandler('student_client.log'), logging.StreamHandler()])
        self.logger = logging.getLogger('student_client')

    def mark_for_closing(self):
        self._closing = True

    async def establish_connection(self):
        max_retries = self.max_reconnect_attempts
        retry_count = 0
        ConnectionManager.log_connection_status("connecting", f"Connecting to server as student for room '{self.room_id}'")
        while retry_count < max_retries and not self.running and not self._closing:
            try:
                server_host = config.SERVER_IP
                if server_host not in ALLOWED_HOSTS:
                    raise Exception(f"Server {server_host} not allowed")
                ConnectionManager.log_connection_status("connecting", f"Connecting to wss://{server_host}:{port}")
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                self.websocket = await asyncio.wait_for(
                    websockets.connect(f"wss://{server_host}:{port}", ssl=ssl_context,
                                       ping_interval=20, ping_timeout=10, max_size=MAX_MESSAGE_SIZE,
                                       origin=f"https://{server_host}"), timeout=15.0)
                ConnectionManager.log_connection_status("connected", "WebSocket connection established")
                self.connection_status.emit("connected", "Connected to server")
                connection_data = {"type": "student", "room_id": self.room_id, "password": PASSWORD,
                                   "student_name": self.student_name, "token": self.token, "auth_token": self.token}
                connection_message = json.dumps(connection_data).encode('utf-8')
                await self.websocket.send(connection_message)
                ConnectionManager.log_connection_status("message_sent", "Connection message sent")
                encrypted_key = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
                try:
                    self.encryption_key = encrypted_key
                    self.cipher = Fernet(self.encryption_key)
                    self.connection_secure = True
                    ConnectionManager.log_connection_status("connected", "Secure encryption established")
                except Exception as e:
                    raise Exception(f"Key exchange failed: {e}")
                confirmation = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
                decrypted_confirmation = self.cipher.decrypt(confirmation).decode('utf-8')
                confirm_data = json.loads(decrypted_confirmation)
                if confirm_data.get('status') == 'connected':
                    self.session_id = confirm_data.get('session_id')
                    self.last_activity = time.time()
                    ConnectionManager.log_connection_status("connected", f"Connected with session: {self.session_id}")
                    self.connection_status.emit("connected", "Connected - waiting for exam...")
                    self.running = True
                    self.reconnect_attempts = 0
                    break
                else:
                    raise Exception(f"Server connection failed: {confirm_data}")
            except asyncio.TimeoutError:
                if self._closing: break
                retry_count += 1
                error_msg = f"Connection timeout (attempt {retry_count}/{max_retries})"
                ConnectionManager.log_connection_status("timeout", error_msg)
                self.connection_status.emit("timeout", error_msg)
                if retry_count >= max_retries:
                    raise Exception("Failed to connect after multiple attempts")
                await asyncio.sleep(2 ** retry_count)
            except Exception as e:
                if self._closing: break
                retry_count += 1
                error_msg = f"Connection error (attempt {retry_count}/{max_retries}): {str(e)}"
                ConnectionManager.log_connection_status("error", error_msg)
                self.connection_status.emit("error", error_msg)
                if retry_count >= max_retries:
                    raise Exception("Failed to establish secure connection")
                await asyncio.sleep(2 ** retry_count)

    async def listen(self):
        try:
            ConnectionManager.log_connection_status("connected", "Listening for messages")
            async for message in self.websocket:
                if self._closing: break
                try:
                    self.last_activity = time.time()
                    decrypted = self.cipher.decrypt(message).decode('utf-8')
                    response = json.loads(decrypted)
                    ConnectionManager.log_connection_status("message_received", f"Received: {response.get('action', 'unknown')}")
                    if not isinstance(response, dict):
                        continue
                    self.message_received.emit(response)
                except Exception as e:
                    error_msg = f"Message processing error: {e}"
                    ConnectionManager.log_connection_status("error", error_msg)
                    self.connection_status.emit("error", error_msg)
        except websockets.exceptions.ConnectionClosed as e:
            if not self._closing:
                error_msg = f"Connection closed: {e}"
                ConnectionManager.log_connection_status("disconnected", error_msg)
                self.connection_secure = False
                self.connection_status.emit("disconnected", "Disconnected from server")
                self.connection_error.emit(error_msg)
                await self.attempt_reconnect()
        except Exception as e:
            if not self._closing:
                error_msg = f"WebSocket error: {e}"
                ConnectionManager.log_connection_status("error", error_msg)
                self.connection_secure = False
                self.connection_status.emit("error", "Connection error")
                self.connection_error.emit(error_msg)

    async def send_message(self, message):
        try:
            if not self.connection_secure or not self.cipher or self._closing:
                raise Exception("Connection not secure or closing")
            message_json = json.dumps(message).encode('utf-8')
            encrypted_data = self.cipher.encrypt(message_json)
            await self.websocket.send(encrypted_data)
            ConnectionManager.log_connection_status("message_sent", f"Sent: {message.get('action', 'unknown')}")
            return True
        except Exception as e:
            error_msg = f"Error sending message: {e}"
            ConnectionManager.log_connection_status("error", error_msg)
            self.connection_error.emit(error_msg)
            return False

    async def attempt_reconnect(self):
        if self._closing: return
        self.reconnect_attempts += 1
        if self.reconnect_attempts > self.max_reconnect_attempts:
            error_msg = f"Max reconnection attempts ({self.max_reconnect_attempts}) exceeded"
            ConnectionManager.log_connection_status("error", error_msg)
            self.connection_error.emit(error_msg)
            return
        ConnectionManager.log_connection_status("reconnecting", f"Reconnection attempt ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
        await asyncio.sleep(3)
        try:
            await self.establish_connection()
            if self.running and not self._closing:
                await self.listen()
        except Exception as e:
            error_msg = f"Reconnection failed: {e}"
            ConnectionManager.log_connection_status("error", error_msg)
            self.connection_error.emit(error_msg)

    async def close(self):
        self._closing = True
        self.running = False
        try:
            if self.websocket:
                try:
                    disconnect_msg = json.dumps({"action": "disconnect", "reason": "user_exit"})
                    if self.cipher:
                        encrypted_disconnect = self.cipher.encrypt(disconnect_msg.encode('utf-8'))
                        await self.websocket.send(encrypted_disconnect)
                except:
                    pass
                await self.websocket.close()
                ConnectionManager.log_connection_status("closed", "WebSocket connection closed securely")
        except Exception as e:
            ConnectionManager.log_connection_status("error", f"Error closing: {e}")
        finally:
            self.connection_secure = False
            self.cipher = None
            self.websocket = None

# ============================================================
# QUIZ WIDGET (Core - Pure QWidget, No Popups)
# ============================================================
class QuizWidget(QWidget):
    """
    Pure QWidget that contains all quiz logic.
    No popup windows - everything is embedded.
    """


    def __init__(self, student_name=None, room_id=None, token=None, exam_data=None, parent=None):
        super().__init__(parent)
        self.student_name = student_name or get_username() or "Student"
        self.room_id = room_id or get_current_room() or ROOM_ID
        self.token = token or get_token() or ""
        self.exam_data = exam_data
        self.time_left = 0
        self.answers = []
        self.total_duration = 0
        self.in_exam = False
        self._exiting = False
        self.last_text_lengths = {}
        self.event_tracker = None
        self.event_filters = []
        self.timer = None
        self.exam_start_time = 0
        self.selected_difficulty = 3  # <-- ADD THIS LINE

        # WebSocket client
        self.ws_client = WebSocketClient()
        self.ws_client.student_name = self.student_name
        self.ws_client.room_id = self.room_id
        self.ws_client.token = self.token
        self.ws_client.message_received.connect(self.handle_server_response)
        self.ws_client.connection_status.connect(self.handle_connection_status)
        self.ws_client.submission_result.connect(self.handle_submission_result)
        self.ws_client.connection_error.connect(self.handle_connection_error)

        # Setup UI
        self.setup_ui()

        # Start connection
        if exam_data:
            self.start_exam(exam_data)
        else:
            self.waiting_label.show()
            self.gif_container.hide()
            self.auto_connect()

    def setup_ui(self):
        """Setup the UI - pure widget, no window."""
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # ===== REMOVED: Header with logo and exit button =====
        # No header anymore - exam area takes full space

        # Timer
        self.time_label = QLabel("Time remaining: --:--")
        self.time_label.setStyleSheet("font-size: 18px; font-weight: 600; color: white; padding: 10px 20px; background: rgba(30,144,255,0.28); border-radius: 15px;")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.hide()
        layout.addWidget(self.time_label)

        # Progress
        self.progress_bar = StyledProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Scroll area for questions (takes maximum space)
        self.scroll_area = StyledScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.hide()
        self.exam_content = QWidget()
        self.exam_content.setStyleSheet("background: transparent;")
        self.exam_content_layout = QVBoxLayout()
        self.exam_content_layout.setSpacing(20)
        self.exam_content_layout.setContentsMargins(20, 20, 20, 20)
        self.exam_content.setLayout(self.exam_content_layout)
        self.scroll_area.setWidget(self.exam_content)
        layout.addWidget(self.scroll_area, 1)  # <-- stretch factor 1 to take all available space

        # Submit button
        self.submit_btn = StyledPushButton("Submit Exam")
        self.submit_btn.setFixedHeight(50)
        self.submit_btn.clicked.connect(self.submit_exam)
        self.submit_btn.hide()
        layout.addWidget(self.submit_btn)

        # Waiting label
        self.waiting_label = QLabel("Waiting for exam to start...")
        self.waiting_label.setAlignment(Qt.AlignCenter)
        self.waiting_label.setStyleSheet("font-size: 24px; color: white; padding: 60px; background: rgba(255,255,255,0.1); border-radius: 20px;")
        layout.addWidget(self.waiting_label, 1)  # <-- stretch factor 1

        # GIF container
        self.gif_container = QWidget()
        self.gif_container.setStyleSheet("background: white; border-radius: 20px;")
        self.gif_layout = QVBoxLayout(self.gif_container)
        self.gif_layout.setAlignment(Qt.AlignCenter)
        self.gif_layout.setContentsMargins(20, 20, 20, 20)
        self.gif_label = QualityGifLabel()
        self.gif_label.setFixedSize(300, 300)
        self.gif_layout.addWidget(self.gif_label)
        self.gif_message = QLabel("Exam submitted successfully!")
        self.gif_message.setAlignment(Qt.AlignCenter)
        self.gif_message.setStyleSheet("font-size: 20px; font-weight: bold; color: #48BB78; margin-top: 20px; background: transparent;")
        self.gif_layout.addWidget(self.gif_message)
        self.gif_container.hide()
        layout.addWidget(self.gif_container, 1)  # <-- stretch factor 1

    def show_difficulty_slider_dialog(self):
        """Show difficulty selection dialog with slider (1-5) - clean version."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Rate Exam Difficulty")
        dialog.setModal(True)
        dialog.setFixedSize(380, 280)
        dialog.setStyleSheet("""
            QDialog {
                background: #ffffff;
                border-radius: 32px;
            }
            QLabel {
                color: #1a202c;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QSlider {
                height: 30px;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #e2e8f0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #667eea, stop:1 #764ba2);
                border: 2px solid white;
                width: 26px;
                height: 26px;
                margin: -9px 0;
                border-radius: 13px;
            }
            QSlider::handle:horizontal:hover {
                transform: scale(1.08);
            }
            QSlider::sub-page:horizontal {
                background: #e2e8f0;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(28, 28, 28, 28)
        
        # Question (only text)
        question_label = QLabel("How difficult was this exam?")
        question_label.setAlignment(Qt.AlignCenter)
        question_label.setStyleSheet("font-size: 22px; font-weight: 600; color: #1a202c; background: transparent;")
        layout.addWidget(question_label)
        
        # Value display
        value_label = QLabel("3")
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("""
            font-size: 52px;
            font-weight: 700;
            color: #667eea;
            background: transparent;
            padding: 4px 0;
        """)
        layout.addWidget(value_label)
        
        # Slider (1-5 range)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(1, 5)
        slider.setValue(3)
        slider.setTickPosition(QSlider.NoTicks)
        slider.setPageStep(1)
        slider.setFixedHeight(40)
        layout.addWidget(slider)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setFixedHeight(44)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #e2e8f0;
                color: #4a5568;
                border: none;
                border-radius: 25px;
                padding: 12px 28px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #cbd5e1;
            }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        
        submit_btn = QPushButton("Submit Exam")
        submit_btn.setFixedHeight(44)
        submit_btn.setMinimumWidth(120)
        submit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 25px;
                padding: 12px 28px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #764ba2, stop:1 #667eea);
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        submit_btn.clicked.connect(dialog.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(submit_btn)
        layout.addLayout(btn_layout)
        
        # Connect slider to value label
        def update_value(value):
            value_label.setText(str(value))
            # Color based on value
            if value <= 2:
                value_label.setStyleSheet("font-size: 52px; font-weight: 700; color: #48BB78; background: transparent; padding: 4px 0;")
            elif value == 3:
                value_label.setStyleSheet("font-size: 52px; font-weight: 700; color: #F6AD55; background: transparent; padding: 4px 0;")
            else:
                value_label.setStyleSheet("font-size: 52px; font-weight: 700; color: #FC8181; background: transparent; padding: 4px 0;")
        
        slider.valueChanged.connect(update_value)
        
        result = dialog.exec()
        if result == QDialog.Accepted:
            return slider.value()
        return None

    def start_exam(self, exam_data):
        if self._exiting: return
        self.exam_data = exam_data
        self.answers = []
        self.last_text_lengths = {}
        self.exam_start_time = time.time()
        self.in_exam = True

        self.event_tracker = ExamEventTracker(self.student_name, exam_data.get('exam_id', 'unknown'))
        self.event_tracker.start_idle_monitoring()
        if hasattr(self.event_tracker, 'copy_paste_detector'):
            self.event_tracker.copy_paste_detector.detection_active = True

        self.event_tracker.log_event("exam_started",
            [f"Exam started with {len(exam_data.get('questions', []))} questions"],
            subject="exam", extra={"question_count": len(exam_data.get('questions', [])),
            "duration_minutes": exam_data.get('duration', 30), "security_monitoring": "active"})

        self.total_duration = exam_data.get('duration', 30) * 60
        self.time_left = self.total_duration

        # Clear and rebuild questions
        for i in reversed(range(self.exam_content_layout.count())):
            widget = self.exam_content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for idx, question in enumerate(exam_data.get('questions', []), 1):
            self.add_question_widget(idx, question)

        self.submit_btn.setEnabled(True)
        self.install_event_filters()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        self.waiting_label.hide()
        self.time_label.show()
        self.progress_bar.show()
        self.scroll_area.show()
        self.submit_btn.show()
        self.gif_container.hide()
        self.update_timer()

    def add_question_widget(self, q_num, question):
        """Add a question widget."""
        group = StyledGroupBox(f"Question {q_num}")
        layout = QVBoxLayout()
        layout.setSpacing(10)

        q_label = QLabel(question.get('question', ''))
        q_label.setWordWrap(True)
        q_label.setStyleSheet("font-size: 16px; font-weight: 500; color: #2d3748; background: transparent;")
        layout.addWidget(q_label)

        # Add image if present
        if 'image' in question and question['image']:
            try:
                image_data = base64.b64decode(question['image'])
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                if not pixmap.isNull():
                    img_label = QLabel()
                    scaled = pixmap.scaledToWidth(400, Qt.SmoothTransformation)
                    img_label.setPixmap(scaled)
                    img_label.setStyleSheet("border-radius: 10px; background: transparent;")
                    layout.addWidget(img_label)
            except Exception as e:
                print(f"Error loading image: {e}")

        answer_type = question.get('answer_type', 'Text Answer')
        if answer_type in ['Multiple Choice', 'اختيار متعدد']:
            options = question.get('answers', [])
            if not options:
                return
            correct_count = sum(1 for opt in options if opt.get('correct', False))
            if correct_count == 1:
                btn_group = QButtonGroup()
                for opt_idx, option in enumerate(options):
                    radio = StyledRadioButton(option.get('option', ''))
                    radio.setMouseTracking(True)
                    radio_id = f"question_{q_num}_radio_{opt_idx}"
                    radio.setObjectName(radio_id)
                    radio_filter = InputEventFilter(radio_id, self.event_tracker, "radio", radio)
                    radio.installEventFilter(radio_filter)
                    self.event_filters.append(radio_filter)
                    radio.toggled.connect(lambda checked, q=q_num, o=opt_idx: self.on_answer_selected(q, o, "radio", checked))
                    btn_group.addButton(radio, opt_idx)
                    layout.addWidget(radio)
                self.answers.append({'question_idx': q_num - 1, 'type': 'multiple_choice_single',
                                     'button_group': btn_group, 'points': question.get('points', 1)})
            else:
                for opt_idx, option in enumerate(options):
                    cb = StyledCheckBox(option.get('option', ''))
                    cb.setMouseTracking(True)
                    cb_id = f"question_{q_num}_checkbox_{opt_idx}"
                    cb.setObjectName(cb_id)
                    cb_filter = InputEventFilter(cb_id, self.event_tracker, "checkbox", cb)
                    cb.installEventFilter(cb_filter)
                    self.event_filters.append(cb_filter)
                    cb.stateChanged.connect(lambda state, q=q_num, o=opt_idx: self.on_answer_selected(q, o, "checkbox", state == Qt.Checked))
                    layout.addWidget(cb)
                    self.answers.append({'question_idx': q_num - 1, 'type': 'multiple_choice_multi',
                                         'checkbox_idx': opt_idx, 'checkbox': cb,
                                         'correct': option.get('correct', False), 'points': question.get('points', 1)})
        else:
            text_area = StyledTextEdit()
            text_area.setPlaceholderText("Write your answer here...")
            text_area.setMinimumHeight(100)
            text_area.setMouseTracking(True)
            text_id = f"question_{q_num}_text"
            text_area.setObjectName(text_id)
            text_filter = InputEventFilter(text_id, self.event_tracker, "text", text_area)
            text_area.installEventFilter(text_filter)
            self.event_filters.append(text_filter)
            text_area.textChanged.connect(lambda: self.on_text_changed(q_num, text_area.toPlainText()))
            layout.addWidget(text_area)
            self.answers.append({'question_idx': q_num - 1, 'type': 'text_answer', 'text_area': text_area,
                                 'points': question.get('points', 1)})

        group.setLayout(layout)
        self.exam_content_layout.addWidget(group)
        if self.event_tracker:
            self.event_tracker.log_event("question_added", [f"Question {q_num} added", f"type:{answer_type}"],
                                         subject=f"question_{q_num}")

    def install_event_filters(self):
        """Install event filters for tracking."""
        self.time_label.setMouseTracking(True)
        self.time_label.installEventFilter(MouseAreaFilter("time_label", self.event_tracker, "time"))
        self.progress_bar.setMouseTracking(True)
        self.progress_bar.installEventFilter(MouseAreaFilter("progress_bar", self.event_tracker, "progress"))
        self.scroll_area.setMouseTracking(True)
        self.scroll_area.viewport().installEventFilter(ScrollEventFilter("exam_scroll_area", self.event_tracker))
        self.submit_btn.setMouseTracking(True)
        self.submit_btn.installEventFilter(ButtonEventFilter("submit_button", self.event_tracker))

    def on_answer_selected(self, question_num, option_idx, answer_type, is_selected):
        """Handle answer selection."""
        if self.event_tracker:
            option_text = ""
            for answer in self.answers:
                if answer['type'] == 'multiple_choice_single' and answer['question_idx'] == question_num - 1:
                    button = answer['button_group'].button(option_idx)
                    if button:
                        option_text = button.text()
                elif answer['type'] == 'multiple_choice_multi' and answer['question_idx'] == question_num - 1:
                    if answer['checkbox_idx'] == option_idx:
                        option_text = answer['checkbox'].text()
            if hasattr(self.event_tracker, 'behavioral_client') and self.event_tracker.behavioral_client:
                old_value = "unselected" if is_selected else "selected"
                new_value = "selected" if is_selected else "deselected"
                if answer_type in ["radio", "checkbox"]:
                    self.event_tracker.behavioral_client.send_answer_changed(
                        question_num, option_idx, answer_type, old_value, new_value
                    )
            self.event_tracker.log_event("answer_selected", [f"Question {question_num} - {answer_type} {option_idx}",
                                         f"selected:{is_selected}", f"option_text:{option_text}"],
                                         subject=f"question_{question_num}", extra={"question": question_num, "option": option_idx,
                                         "option_text": option_text, "type": answer_type, "selected": is_selected})

    def on_text_changed(self, question_num, text):
        """Handle text change."""
        if hasattr(self, 'event_tracker') and self.event_tracker:
            old_length = self.last_text_lengths.get(question_num, 0)
            new_length = len(text)
            if old_length > 0 and new_length == 0:
                if hasattr(self.event_tracker, 'behavioral_client') and self.event_tracker.behavioral_client:
                    self.event_tracker.behavioral_client.send_text_cleared(
                        f"question_{question_num}_text", old_length, question_num
                    )
            self.event_tracker.log_event("text_answer_changed", [f"Question {question_num} text changed", f"length:{new_length}", f"preview:{text[:50]}"],
                                         subject=f"question_{question_num}_text", extra={"question": question_num, "text_length": new_length,
                                         "text_preview": text[:50], "has_content": len(text.strip()) > 0})
            self.last_text_lengths[question_num] = new_length

    def update_timer(self):
        """Update the timer display."""
        if self._exiting: return
        self.time_left -= 1
        if self.time_left % 30 == 0 and self.event_tracker:
            minutes = self.time_left // 60
            seconds = self.time_left % 60
            self.event_tracker.log_event("timer_update", [f"Time remaining: {minutes:02d}:{seconds:02d}"], subject="timer")
        if self.time_left == 300 and self.event_tracker:
            self.event_tracker.log_event("time_warning", ["5 minutes remaining!"], subject="timer")
        if self.time_left <= 0:
            self.timer.stop()
            self.time_label.setText("Time's up!")
            if self.event_tracker:
                self.event_tracker.log_event("time_expired", ["Exam time has expired"], subject="timer")
            self.submit_exam()
            return
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.time_label.setText(f"Time remaining: {minutes:02d}:{seconds:02d}")
        progress = int((self.time_left / self.total_duration) * 100)
        self.progress_bar.setValue(100 - progress)
        if self.time_left < 300:
            self.time_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #f5576c; padding: 10px 20px; background: rgba(255,255,255,0.2); border-radius: 15px;")


    def submit_exam(self):
        """Submit the exam."""
        # Prevent double submission
        if self._exiting or not self.submit_btn.isEnabled():
            return
        
        # ===== SHOW DIFFICULTY SLIDER POPUP =====
        difficulty = self.show_difficulty_slider_dialog()
        if difficulty is None:
            # User cancelled - don't submit
            if self.event_tracker:
                self.event_tracker.log_event("submission_cancelled", ["User cancelled submission"], subject="submission")
            return
        
        # Store the selected difficulty
        self.selected_difficulty = difficulty
        
        if self.event_tracker:
            self.event_tracker.log_event("difficulty_selected", 
                [f"Selected difficulty: {difficulty}/5"], 
                subject="submission")
        
        # Disable submit button to prevent double submission
        self.submit_btn.setEnabled(False)
        
        if self.event_tracker and hasattr(self.event_tracker, 'behavioral_client'):
            time_taken = time.time() - self.exam_start_time
            self.event_tracker.behavioral_client.send_quiz_end("submitted", time_taken)
        if self._exiting: return
        if self.event_tracker:
            self.event_tracker.log_event("submission_started", ["Starting exam submission"], subject="submission")
        try:
            if hasattr(self.event_tracker, 'copy_paste_detector') and self.event_tracker.copy_paste_detector:
                self.event_tracker.copy_paste_detector.stop_detection()
        except Exception as e:
            print(f"⚠️ Error stopping copy-paste detection: {e}")

        if not self.ws_client.connection_secure:
            if self.event_tracker:
                self.event_tracker.log_event("connection_error", ["Connection not secure - cannot submit"], subject="submission")
            QMessageBox.warning(self, "Connection Error", "Connection not secure - cannot submit")
            self.submit_btn.setEnabled(True)
            return

        if not self.exam_data:
            if self.event_tracker:
                self.event_tracker.log_event("submission_error", ["No exam data to submit"], subject="submission")
            QMessageBox.warning(self, "No Exam", "No exam to submit")
            self.submit_btn.setEnabled(True)
            return

        actual_time_taken = time.time() - self.exam_start_time
        if actual_time_taken < 0:
            actual_time_taken = 0
        if self.event_tracker:
            self.event_tracker.log_event("time_summary", [f"Time taken for exam: {actual_time_taken:.1f} seconds"], subject="timer",
                                         extra={"time_taken_seconds": actual_time_taken, "time_taken_formatted": self.format_time_taken(actual_time_taken)})

        # ===== ADD difficulty_rating to answer_data =====
        answer_data = {
            "student_name": self.student_name, 
            "answers": [], 
            "time_taken": self.format_time_taken(actual_time_taken), 
            "time_taken_seconds": actual_time_taken,
            "difficulty_rating": difficulty  # <-- ADD THIS LINE
        }
        
        for answer in self.answers:
            question_idx = answer['question_idx']
            question = self.exam_data['questions'][question_idx]
            if answer['type'] == 'multiple_choice_single':
                selected_id = answer['button_group'].checkedId()
                if selected_id == -1:
                    answer_data['answers'].append({"question": question['question'], "answer_type": question['answer_type'],
                                                   "student_answer": [], "points": answer['points']})
                else:
                    options = question['answers']
                    answer_data['answers'].append({"question": question['question'], "answer_type": question['answer_type'],
                                                   "student_answer": [{"option": options[selected_id]['option'], "checked": True}], "points": answer['points']})
            elif answer['type'] == 'multiple_choice_multi':
                question_checkboxes = [a for a in self.answers if a['type'] == 'multiple_choice_multi' and a['question_idx'] == question_idx]
                selected_options = []
                for cb_answer in question_checkboxes:
                    if cb_answer['checkbox'].isChecked():
                        selected_options.append({"option": question['answers'][cb_answer['checkbox_idx']]['option'], "checked": True})
                answer_data['answers'].append({"question": question['question'], "answer_type": question['answer_type'],
                                               "student_answer": selected_options, "points": answer['points']})
            elif answer['type'] == 'text_answer':
                answer_data['answers'].append({"question": question['question'], "answer_type": question['answer_type'],
                                               "student_answer": answer['text_area'].toPlainText(), "points": answer['points']})

        # Show submission animation
        self.show_submission_gif()

        # Send answers asynchronously
        self.submit_thread = Thread(target=self.submit_answers_async, args=(answer_data,), daemon=True)
        self.submit_thread.start()


    def show_submission_gif(self):
        """Show submission animation."""
        if self._exiting: return
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
        self.time_label.hide()
        self.progress_bar.hide()
        self.scroll_area.hide()
        self.submit_btn.hide()
        self.waiting_label.hide()
        for i in reversed(range(self.exam_content_layout.count())):
            widget = self.exam_content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        gif_path = os.path.join(SCRIPT_DIR, "senddone.gif")
        if os.path.exists(gif_path):
            movie = QMovie(gif_path)
            if movie.isValid():
                self.gif_label.setMovie(movie)
        self.gif_container.show()
        self.in_exam = False
        QTimer.singleShot(2500, self.reset_to_waiting)

    def reset_to_waiting(self):
        """Reset to waiting state."""
        if self._exiting: return
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
        for i in reversed(range(self.exam_content_layout.count())):
            widget = self.exam_content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.event_filters.clear()
        self.in_exam = False
        self.exam_data = None
        self.answers.clear()
        self.last_text_lengths.clear()
        if self.event_tracker:
            self.event_tracker.stop()
            self.event_tracker = None
        self.waiting_label.setText("Waiting for exam to start...")
        self.waiting_label.show()
        self.time_label.hide()
        self.progress_bar.hide()
        self.scroll_area.hide()
        self.submit_btn.hide()
        self.gif_container.hide()
        self.exit_btn.setEnabled(True)
        self.exit_btn.setText("Exit")

    # ---------- WebSocket Handlers ----------
    def auto_connect(self):
        """Auto-connect to server."""
        self.waiting_label.setText("Connecting to exam server...")
        self.ws_client.student_name = self.student_name
        self.ws_client.room_id = self.room_id
        self.ws_client.token = self.token
        try:
            self.ws_thread = Thread(target=self.run_websocket_client, daemon=True)
            self.ws_thread.start()
        except Exception as e:
            QMessageBox.warning(self, "Connection Error", str(e))

    def run_websocket_client(self):
        """Run WebSocket client in thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.ws_client.establish_connection())
            if self.ws_client.running and not self._exiting:
                loop.run_until_complete(self.ws_client.listen())
        except Exception as e:
            if not self._exiting:
                self.show_connection_message("Connection Error", str(e), "error")
        finally:
            loop.close()

    def handle_server_response(self, response):
        """Handle server response."""
        if self._exiting: return
        try:
            action = response.get('action')
            if self.event_tracker:
                self.event_tracker.log_event("server_response", [f"Received from server: {action}"], subject="server")
            if action == 'exam_start':
                self.start_exam(response.get('quiz_data'))
            elif action == 'exam_end':
                if self.event_tracker:
                    self.event_tracker.log_event("exam_ended_by_server", ["Exam ended by server"], subject="exam")
                self.reset_to_waiting()
            elif response.get('error'):
                self.show_connection_message("Server Error", response.get('error'), "error")
        except Exception as e:
            self.show_connection_message("Error", f"Error processing response: {e}", "error")

    def handle_connection_status(self, status, message):
        """Handle connection status."""
        if status == "disconnected" and not self._exiting:
            self.show_connection_message("Disconnected", "Lost connection to server", "error")
            if self.event_tracker:
                self.event_tracker.log_event("connection_disconnected", ["Connection disconnected"], subject="connection")

    def handle_connection_error(self, error_message):
        """Handle connection error."""
        if not self._exiting:
            self.show_connection_message("Connection Error", error_message, "error")
            if self.event_tracker:
                self.event_tracker.log_event("connection_error", [f"Connection error: {error_message}"], subject="connection")

    def handle_submission_result(self, success, message):
        """Handle submission result."""
        if success:
            if self.event_tracker:
                self.event_tracker.log_event("submission_success", ["Exam submitted successfully"], subject="submission")
        else:
            if self.event_tracker:
                self.event_tracker.log_event("submission_failed", [f"Submission failed: {message}"], subject="submission")
            self.show_connection_message("Submission Error", "Failed to submit exam", "error")

    def submit_answers_async(self, answer_data):
        """Submit answers asynchronously."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            log_upload_success = False
            log_upload_message = ""
            if hasattr(self, 'event_tracker') and self.event_tracker and hasattr(self.event_tracker, 'log_filename'):
                log_file_path = self.event_tracker.log_filename
                if os.path.exists(log_file_path):
                    upload_client = WebSocketClientUpload()
                    try:
                        connect_result = loop.run_until_complete(upload_client.connect_to_server())
                        if connect_result:
                            file_name = os.path.basename(log_file_path)
                            file_size = os.path.getsize(log_file_path)
                            if self.event_tracker:
                                self.event_tracker.log_event("log_upload_start", [f"Starting upload: {file_name} ({file_size} bytes)"], subject="upload")
                            upload_result = loop.run_until_complete(upload_client.upload_file("room1", log_file_path, f"Behavioral log for {self.student_name}"))
                            if upload_result:
                                log_upload_success = True
                                log_upload_message = f"Behavioral log uploaded: {file_name}"
                                if self.event_tracker:
                                    self.event_tracker.log_event("log_upload_success", [f"Uploaded: {file_name}"], subject="upload")
                            loop.run_until_complete(upload_client.close())
                        else:
                            log_upload_message = "Failed to connect to upload server"
                    except Exception as e:
                        log_upload_message = f"Upload error: {str(e)}"
                    finally:
                        try:
                            if hasattr(upload_client, 'websocket') and upload_client.websocket:
                                loop.run_until_complete(upload_client.websocket.close())
                        except:
                            pass
            answer_data['log_upload'] = {'success': log_upload_success, 'message': log_upload_message,
                                         'log_file': self.event_tracker.log_filename if self.event_tracker and hasattr(self.event_tracker, 'log_filename') else None}
            success = loop.run_until_complete(self.ws_client.send_message({"action": "submit_answers", "answers": answer_data,
                                           "student_name": self.student_name, "timestamp": datetime.now().isoformat()}))
            if success:
                self.ws_client.submission_result.emit(True, "Success")
            else:
                self.ws_client.submission_result.emit(False, "Failed")
        except Exception as e:
            self.ws_client.submission_result.emit(False, str(e))
        finally:
            loop.close()

    def format_time_taken(self, seconds):
        """Format time taken."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def show_connection_message(self, title, message, message_type):
        """Show connection message."""
        if self._exiting: return
        if self.isVisible():
            if message_type == "error":
                QMessageBox.critical(self, title, message)
            elif message_type == "warning":
                QMessageBox.warning(self, title, message)
            else:
                QMessageBox.information(self, title, message)

    def safe_exit(self):
        """Safe exit - stops all threads and timers."""
        if self._exiting: return
        self._exiting = True
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
            self.timer = None
        self.close_websocket_sync()
        if self.event_tracker:
            self.event_tracker.stop()
            self.event_tracker = None
        print("✅ QuizWidget shut down cleanly")

    def close_websocket_sync(self):
        """Close WebSocket synchronously."""
        if hasattr(self, 'ws_client') and self.ws_client:
            print("🔒 Closing WebSocket connection securely...")
            self.ws_client.mark_for_closing()
            close_thread = Thread(target=self._close_ws_in_thread, daemon=True)
            close_thread.start()
            close_thread.join(timeout=3.0)

    def _close_ws_in_thread(self):
        """Close WebSocket in thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.ws_client.close())
            print("✅ WebSocket connection closed successfully")
        except Exception as e:
            print(f"⚠️ Error closing WebSocket: {e}")
        finally:
            loop.close()

    def closeEvent(self, event):
        """Handle close event."""
        self.safe_exit()
        event.accept()

# ============================================================
# QUIZ PAGE (Main entry for teacher dashboard)
# ============================================================
# ============================================================
# QUIZ PAGE (Main entry for teacher dashboard)
# ============================================================
class QuizPage(QWidget):
    """
    Main quiz page for the teacher dashboard.
    Follows the same pattern as ClassroomPage, PollPage, etc.
    """
    def __init__(self, config=None, parent=None, embedded=False):
        super().__init__(parent)
        self.config = config or {}
        self.quiz_widget = None
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Check if quiz module is available
        if self.config.get('QUIZ_AVAILABLE', False):
            try:
                # Get credentials from token_manager
                student_name = get_username() or "Student"
                room_id = get_current_room() or ROOM_ID
                token = get_token() or ""
                
                # Try to get QuizWidget from various sources
                QuizWidgetClass = None
                
                # First, try to get it from the current module's global scope
                import sys
                current_module = sys.modules.get(__name__)
                if current_module and hasattr(current_module, 'QuizWidget'):
                    QuizWidgetClass = current_module.QuizWidget
                    print("✅ QuizWidget found in current module")
                else:
                    # Try to get it from the global scope
                    if 'QuizWidget' in globals():
                        QuizWidgetClass = globals()['QuizWidget']
                        print("✅ QuizWidget found in globals")
                    else:
                        # Try to import it from the module
                        import importlib
                        try:
                            # Reload the module to ensure it's fresh
                            if __name__ in sys.modules:
                                module = importlib.reload(sys.modules[__name__])
                                if hasattr(module, 'QuizWidget'):
                                    QuizWidgetClass = module.QuizWidget
                                    print("✅ QuizWidget found after reload")
                        except Exception as reload_error:
                            print(f"⚠️ Could not reload module: {reload_error}")
                
                if QuizWidgetClass is None:
                    # Last resort: try to import from quiz module
                    try:
                        import quiz
                        if hasattr(quiz, 'QuizWidget'):
                            QuizWidgetClass = quiz.QuizWidget
                            print("✅ QuizWidget found in quiz module import")
                    except ImportError:
                        pass
                
                if QuizWidgetClass is None:
                    raise NameError("QuizWidget class could not be found")
                
                # Create the quiz widget
                self.quiz_widget = QuizWidgetClass(
                    student_name=student_name,
                    room_id=room_id,
                    token=token,
                    exam_data=None,
                    parent=self
                )
                self.quiz_widget.setStyleSheet("background: transparent;")
                layout.addWidget(self.quiz_widget)
                print("✅ QuizPage loaded successfully")
                
            except NameError as ne:
                print(f"❌ QuizWidget not found: {ne}")
                # Show a fallback message
                fallback = QLabel("Quiz module is not available.\nPlease check the installation.")
                fallback.setAlignment(Qt.AlignCenter)
                fallback.setStyleSheet("color: #ff6b6b; font-size: 16px; padding: 40px;")
                layout.addWidget(fallback)
            except Exception as e:
                print(f"❌ Failed to load quiz: {e}")
                import traceback
                traceback.print_exc()
                layout.addWidget(QLabel(f"Quiz error: {e}"))
        else:
            layout.addWidget(PlaceholderPage("Quiz", "Create and manage quizzes.", "📝"))
    
    def get_embedded_widget(self):
        """Return the embedded widget for compatibility with main3.py."""
        return self.quiz_widget
    
    def shutdown(self):
        """Clean shutdown - called by parent dashboard."""
        if self.quiz_widget:
            try:
                if hasattr(self.quiz_widget, 'safe_exit'):
                    self.quiz_widget.safe_exit()
                elif hasattr(self.quiz_widget, 'close'):
                    self.quiz_widget.close()
                self.quiz_widget = None
                print("✅ QuizPage shut down successfully")
            except Exception as e:
                print(f"⚠️ Error shutting down quiz: {e}")
    
    def closeEvent(self, event):
        """Handle close event."""
        self.shutdown()
        event.accept()
# ============================================================
# Backward Compatibility - For standalone mode and main2.py
# ============================================================
class QuizApp(QWidget):
    """
    Wrapper for backward compatibility with main2.py.
    For embedding, use QuizPage or QuizWidget directly.
    """
    def __init__(self, student_name=None, room_id=None, token=None, exam_data=None, parent=None, embedded=False):
        super().__init__(parent)
        self.embedded = embedded
        
        if embedded:
            # Embedded mode - use QuizWidget directly
            self.quiz_widget = QuizWidget(student_name, room_id, token, exam_data, self)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.quiz_widget)
        else:
            # Standalone mode - run as window
            self._run_standalone(student_name, room_id, token, exam_data)
    
    def _run_standalone(self, student_name, room_id, token, exam_data):
        """Run in standalone mode."""
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        self.window = QMainWindow()
        self.window.setWindowTitle("Latigo Test")
        self.window.setGeometry(100, 100, 900, 700)
        
        # Create quiz widget as central widget
        self.quiz_widget = QuizWidget(student_name, room_id, token, exam_data, self.window)
        self.window.setCentralWidget(self.quiz_widget)
        self.window.show()
    
    def get_embedded_widget(self):
        """Return the embedded widget for main2.py compatibility."""
        if hasattr(self, 'quiz_widget'):
            return self.quiz_widget
        return None
    
    def shutdown(self):
        """Clean shutdown."""
        if hasattr(self, 'quiz_widget') and self.quiz_widget:
            self.quiz_widget.safe_exit()
            self.quiz_widget = None
        if hasattr(self, 'window') and self.window:
            self.window.close()
            self.window = None
    
    def closeEvent(self, event):
        self.shutdown()
        event.accept()

def launch_quiz(student_name=None, room_id=None, token=None, exam_data=None, embedded=False):
    """
    Public entry point to start the quiz/exam.
    
    Parameters:
        student_name (str, optional): Student's name.
        room_id (str, optional): Room ID.
        token (str, optional): Authentication token.
        exam_data (dict, optional): Exam data to start immediately.
        embedded (bool): If True, returns a widget for embedding.
    
    Returns:
        int or QWidget: Exit code if standalone, QWidget if embedded.
    """
    if embedded:
        return QuizWidget(student_name, room_id, token, exam_data)
    
    # Standalone mode - create app and run
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    window = QMainWindow()
    window.setWindowTitle("Latigo Test")
    window.setGeometry(100, 100, 900, 700)
    
    quiz_widget = QuizWidget(student_name, room_id, token, exam_data, window)
    window.setCentralWidget(quiz_widget)
    window.show()
    
    return app.exec()

# ============================================================
# MAIN (when run directly)
# ============================================================
if __name__ == "__main__":
    sys.exit(launch_quiz())