######################################################################
#  This file should be kept compatible with Python 2.3, see PEP 291. #
######################################################################
"""create and manipulate C data types in Python"""

import os as _os, sys as _sys

# special developer support to use ctypes from the CVS sandbox,
# without installing it
# XXX Remove this for the python core version
_magicfile = _os.path.join(_os.path.dirname(__file__), ".CTYPES_DEVEL")
if _os.path.isfile(_magicfile):
    execfile(_magicfile)
del _magicfile

__version__ = "1.0.0"


#----------------------------------------------------------------------
# import "_ctypes" with different dll-file names
#----------------------------------------------------------------------
try: import _ctypes
except:
	name = 'ctypes' + ''.join(_sys.version.split('.')[:2])
	exec "import %s as _ctypes"%name in _sys.modules[__name__].__dict__
	_sys.modules['_ctypes'] = _sys.modules[name]
	del _sys.modules[name]


#----------------------------------------------------------------------
# import other objects
#----------------------------------------------------------------------
from _ctypes import Union, Structure, Array
from _ctypes import _Pointer
from _ctypes import CFuncPtr as _CFuncPtr
from _ctypes import __version__ as _ctypes_version
from _ctypes import RTLD_LOCAL, RTLD_GLOBAL
from _ctypes import ArgumentError

from struct import calcsize as _calcsize

if __version__ != _ctypes_version:
    if not _ctypes_version in ('1.0.0', '1.0.1'):
       raise Exception, ("Version number mismatch", __version__, _ctypes_version)
    pass

if _os.name in ("nt", "ce"):
    from _ctypes import FormatError

DEFAULT_MODE = RTLD_LOCAL
if _os.name == "posix" and _sys.platform == "darwin":
    import gestalt

    # gestalt.gestalt("sysv") returns the version number of the
    # currently active system file as BCD.
    # On OS X 10.4.6 -> 0x1046
    # On OS X 10.2.8 -> 0x1028
    # See also http://www.rgaros.nl/gestalt/
    #
    # On OS X 10.3, we use RTLD_GLOBAL as default mode
    # because RTLD_LOCAL does not work at least on some
    # libraries.

    if gestalt.gestalt("sysv") < 0x1040:
        DEFAULT_MODE = RTLD_GLOBAL

from _ctypes import FUNCFLAG_CDECL as _FUNCFLAG_CDECL, \
     FUNCFLAG_PYTHONAPI as _FUNCFLAG_PYTHONAPI

"""
WINOLEAPI -> HRESULT
WINOLEAPI_(type)

STDMETHODCALLTYPE

STDMETHOD(name)
STDMETHOD_(type, name)

STDAPICALLTYPE
"""

def create_string_buffer(init, size=None):
    """create_string_buffer(aString) -> character array
    create_string_buffer(anInteger) -> character array
    create_string_buffer(aString, anInteger) -> character array
    """
    if isinstance(init, (str, unicode)):
        if size is None:
            size = len(init)+1
        buftype = c_char * size
        buf = buftype()
        buf.value = init
        return buf
    elif isinstance(init, (int, long)):
        buftype = c_char * init
        buf = buftype()
        return buf
    raise TypeError, init

def c_buffer(init, size=None):
##    "deprecated, use create_string_buffer instead"
##    import warnings
##    warnings.warn("c_buffer is deprecated, use create_string_buffer instead",
##                  DeprecationWarning, stacklevel=2)
    return create_string_buffer(init, size)

_c_functype_cache = {}
def CFUNCTYPE(restype, *argtypes):
    """CFUNCTYPE(restype, *argtypes) -> function prototype.

    restype: the result type
    argtypes: a sequence specifying the argument types

    The function prototype can be called in different ways to create a
    callable object:

    prototype(integer address) -> foreign function
    prototype(callable) -> create and return a C callable function from callable
    prototype(integer index, method name[, paramflags]) -> foreign function calling a COM method
    prototype((ordinal number, dll object)[, paramflags]) -> foreign function exported by ordinal
    prototype((function name, dll object)[, paramflags]) -> foreign function exported by name
    """
    try:
        return _c_functype_cache[(restype, argtypes)]
    except KeyError:
        class CFunctionType(_CFuncPtr):
            _argtypes_ = argtypes
            _restype_ = restype
            _flags_ = _FUNCFLAG_CDECL
        _c_functype_cache[(restype, argtypes)] = CFunctionType
        return CFunctionType

if _os.name in ("nt", "ce"):
    from _ctypes import LoadLibrary as _dlopen
    from _ctypes import FUNCFLAG_STDCALL as _FUNCFLAG_STDCALL
    if _os.name == "ce":
        # 'ce' doesn't have the stdcall calling convention
        _FUNCFLAG_STDCALL = _FUNCFLAG_CDECL

    _win_functype_cache = {}
    def WINFUNCTYPE(restype, *argtypes):
        # docstring set later (very similar to CFUNCTYPE.__doc__)
        try:
            return _win_functype_cache[(restype, argtypes)]
        except KeyError:
            class WinFunctionType(_CFuncPtr):
                _argtypes_ = argtypes
                _restype_ = restype
                _flags_ = _FUNCFLAG_STDCALL
            _win_functype_cache[(restype, argtypes)] = WinFunctionType
            return WinFunctionType
    if WINFUNCTYPE.__doc__:
        WINFUNCTYPE.__doc__ = CFUNCTYPE.__doc__.replace("CFUNCTYPE", "WINFUNCTYPE")

elif _os.name == "posix":
    from _ctypes import dlopen as _dlopen

from _ctypes import sizeof, byref, addressof, alignment, resize
from _ctypes import _SimpleCData

class py_object(_SimpleCData):
    _type_ = "O"

class c_short(_SimpleCData):
    _type_ = "h"

class c_ushort(_SimpleCData):
    _type_ = "H"

class c_long(_SimpleCData):
    _type_ = "l"

class c_ulong(_SimpleCData):
    _type_ = "L"

if _calcsize("i") == _calcsize("l"):
    # if int and long have the same size, make c_int an alias for c_long
    c_int = c_long
    c_uint = c_ulong
else:
    class c_int(_SimpleCData):
        _type_ = "i"

    class c_uint(_SimpleCData):
        _type_ = "I"

class c_float(_SimpleCData):
    _type_ = "f"

class c_double(_SimpleCData):
    _type_ = "d"

if _calcsize("l") == _calcsize("q"):
    # if long and long long have the same size, make c_longlong an alias for c_long
    c_longlong = c_long
    c_ulonglong = c_ulong
else:
    class c_longlong(_SimpleCData):
        _type_ = "q"

    class c_ulonglong(_SimpleCData):
        _type_ = "Q"
    ##    def from_param(cls, val):
    ##        return ('d', float(val), val)
    ##    from_param = classmethod(from_param)

class c_ubyte(_SimpleCData):
    _type_ = "B"
c_ubyte.__ctype_le__ = c_ubyte.__ctype_be__ = c_ubyte
# backward compatibility:
##c_uchar = c_ubyte

class c_byte(_SimpleCData):
    _type_ = "b"
c_byte.__ctype_le__ = c_byte.__ctype_be__ = c_byte

class c_char(_SimpleCData):
    _type_ = "c"
c_char.__ctype_le__ = c_char.__ctype_be__ = c_char

class c_char_p(_SimpleCData):
    _type_ = "z"

class c_void_p(_SimpleCData):
    _type_ = "P"
c_voidp = c_void_p # backwards compatibility (to a bug)

# This cache maps types to pointers to them.
_pointer_type_cache = {}

def POINTER(cls):
    try:
        return _pointer_type_cache[cls]
    except KeyError:
        pass
    if type(cls) is str:
        klass = type(_Pointer)("LP_%s" % cls,
                               (_Pointer,),
                               {})
        _pointer_type_cache[id(klass)] = klass
        return klass
    else:
        name = "LP_%s" % cls.__name__
        klass = type(_Pointer)(name,
                               (_Pointer,),
                               {'_type_': cls})
        _pointer_type_cache[cls] = klass
    return klass

try:
    from _ctypes import set_conversion_mode
except ImportError:
    pass
else:
    if _os.name in ("nt", "ce"):
        set_conversion_mode("mbcs", "ignore")
    else:
        set_conversion_mode("ascii", "strict")

    class c_wchar_p(_SimpleCData):
        _type_ = "Z"

    class c_wchar(_SimpleCData):
        _type_ = "u"

    POINTER(c_wchar).from_param = c_wchar_p.from_param #_SimpleCData.c_wchar_p_from_param

    def create_unicode_buffer(init, size=None):
        """create_unicode_buffer(aString) -> character array
        create_unicode_buffer(anInteger) -> character array
        create_unicode_buffer(aString, anInteger) -> character array
        """
        if isinstance(init, (str, unicode)):
            if size is None:
                size = len(init)+1
            buftype = c_wchar * size
            buf = buftype()
            buf.value = init
            return buf
        elif isinstance(init, (int, long)):
            buftype = c_wchar * init
            buf = buftype()
            return buf
        raise TypeError, init

POINTER(c_char).from_param = c_char_p.from_param #_SimpleCData.c_char_p_from_param

# XXX Deprecated
def SetPointerType(pointer, cls):
    if _pointer_type_cache.get(cls, None) is not None:
        raise RuntimeError, \
              "This type already exists in the cache"
    if not _pointer_type_cache.has_key(id(pointer)):
        raise RuntimeError, \
              "What's this???"
    pointer.set_type(cls)
    _pointer_type_cache[cls] = pointer
    del _pointer_type_cache[id(pointer)]


def pointer(inst):
    return POINTER(type(inst))(inst)

# XXX Deprecated
def ARRAY(typ, len):
    return typ * len

################################################################


class CDLL(object):
    """An instance of this class represents a loaded dll/shared
    library, exporting functions using the standard C calling
    convention (named 'cdecl' on Windows).

    The exported functions can be accessed as attributes, or by
    indexing with the function name.  Examples:

    <obj>.qsort -> callable object
    <obj>['qsort'] -> callable object

    Calling the functions releases the Python GIL during the call and
    reaquires it afterwards.
    """
    class _FuncPtr(_CFuncPtr):
        _flags_ = _FUNCFLAG_CDECL
        _restype_ = c_int # default, can be overridden in instances

    def __init__(self, name, mode=DEFAULT_MODE, handle=None):
        self._name = name
        if handle is None:
            self._handle = _dlopen(self._name, mode)
        else:
            self._handle = handle

    def __repr__(self):
        return "<%s '%s', handle %x at %x>" % \
               (self.__class__.__name__, self._name,
                (self._handle & (_sys.maxint*2 + 1)),
                id(self) & (_sys.maxint*2 + 1))

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError, name
        func = self.__getitem__(name)
        setattr(self, name, func)
        return func

    def __getitem__(self, name_or_ordinal):
        func = self._FuncPtr((name_or_ordinal, self))
        if not isinstance(name_or_ordinal, (int, long)):
            func.__name__ = name_or_ordinal
        return func

class PyDLL(CDLL):
    """This class represents the Python library itself.  It allows to
    access Python API functions.  The GIL is not released, and
    Python exceptions are handled correctly.
    """
    class _FuncPtr(_CFuncPtr):
        _flags_ = _FUNCFLAG_CDECL | _FUNCFLAG_PYTHONAPI
        _restype_ = c_int # default, can be overridden in instances

if _os.name in ("nt", "ce"):

    class WinDLL(CDLL):
        """This class represents a dll exporting functions using the
        Windows stdcall calling convention.
        """
        class _FuncPtr(_CFuncPtr):
            _flags_ = _FUNCFLAG_STDCALL
            _restype_ = c_int # default, can be overridden in instances

    # XXX Hm, what about HRESULT as normal parameter?
    # Mustn't it derive from c_long then?
    from _ctypes import _check_HRESULT, _SimpleCData
    class HRESULT(_SimpleCData):
        _type_ = "l"
        # _check_retval_ is called with the function's result when it
        # is used as restype.  It checks for the FAILED bit, and
        # raises a WindowsError if it is set.
        #
        # The _check_retval_ method is implemented in C, so that the
        # method definition itself is not included in the traceback
        # when it raises an error - that is what we want (and Python
        # doesn't have a way to raise an exception in the caller's
        # frame).
        _check_retval_ = _check_HRESULT

    class OleDLL(CDLL):
        """This class represents a dll exporting functions using the
        Windows stdcall calling convention, and returning HRESULT.
        HRESULT error values are automatically raised as WindowsError
        exceptions.
        """
        class _FuncPtr(_CFuncPtr):
            _flags_ = _FUNCFLAG_STDCALL
            _restype_ = HRESULT

class LibraryLoader(object):
    def __init__(self, dlltype):
        self._dlltype = dlltype

    def __getattr__(self, name):
        if name[0] == '_':
            raise AttributeError(name)
        dll = self._dlltype(name)
        setattr(self, name, dll)
        return dll

    def __getitem__(self, name):
        return getattr(self, name)

    def LoadLibrary(self, name):
        return self._dlltype(name)

cdll = LibraryLoader(CDLL)
pydll = LibraryLoader(PyDLL)

if _os.name in ("nt", "ce"):
    pythonapi = PyDLL("python dll", None, _sys.dllhandle)
elif _sys.platform == "cygwin":
    pythonapi = PyDLL("libpython%d.%d.dll" % _sys.version_info[:2])
else:
    pythonapi = PyDLL(None)


if _os.name in ("nt", "ce"):
    windll = LibraryLoader(WinDLL)
    oledll = LibraryLoader(OleDLL)

    if _os.name == "nt":
        GetLastError = windll.kernel32.GetLastError
    else:
        GetLastError = windll.coredll.GetLastError

    def WinError(code=None, descr=None):
        if code is None:
            code = GetLastError()
        if descr is None:
            descr = FormatError(code).strip()
        return WindowsError(code, descr)

_pointer_type_cache[None] = c_void_p

if sizeof(c_uint) == sizeof(c_void_p):
    c_size_t = c_uint
elif sizeof(c_ulong) == sizeof(c_void_p):
    c_size_t = c_ulong

# functions

from _ctypes import _memmove_addr, _memset_addr, _string_at_addr, _cast_addr

## void *memmove(void *, const void *, size_t);
memmove = CFUNCTYPE(c_void_p, c_void_p, c_void_p, c_size_t)(_memmove_addr)

## void *memset(void *, int, size_t)
memset = CFUNCTYPE(c_void_p, c_void_p, c_int, c_size_t)(_memset_addr)

def PYFUNCTYPE(restype, *argtypes):
    class CFunctionType(_CFuncPtr):
        _argtypes_ = argtypes
        _restype_ = restype
        _flags_ = _FUNCFLAG_CDECL | _FUNCFLAG_PYTHONAPI
    return CFunctionType

_cast = PYFUNCTYPE(py_object, c_void_p, py_object, py_object)(_cast_addr)
def cast(obj, typ):
    return _cast(obj, obj, typ)

_string_at = CFUNCTYPE(py_object, c_void_p, c_int)(_string_at_addr)
def string_at(ptr, size=0):
    """string_at(addr[, size]) -> string

    Return the string at addr."""
    return _string_at(ptr, size)

try:
    from _ctypes import _wstring_at_addr
except ImportError:
    pass
else:
    _wstring_at = CFUNCTYPE(py_object, c_void_p, c_int)(_wstring_at_addr)
    def wstring_at(ptr, size=0):
        """wstring_at(addr[, size]) -> string

        Return the string at addr."""
        return _wstring_at(ptr, size)


if _os.name in ("nt", "ce"): # COM stuff
    def DllGetClassObject(rclsid, riid, ppv):
        try:
            ccom = __import__("comtypes.server.inprocserver", globals(), locals(), ['*'])
        except ImportError:
            return -2147221231 # CLASS_E_CLASSNOTAVAILABLE
        else:
            return ccom.DllGetClassObject(rclsid, riid, ppv)

    def DllCanUnloadNow():
        try:
            ccom = __import__("comtypes.server.inprocserver", globals(), locals(), ['*'])
        except ImportError:
            return 0 # S_OK
        return ccom.DllCanUnloadNow()

#----------------------------------------------------------------------
# install new sub module
#----------------------------------------------------------------------
def install_package(name, code):
	import imp
	packname = '%s.%s'%(__name__, name)
	if packname in _sys.modules:
		return False
	module = imp.new_module(name)
	_sys.modules[packname] = module
	exec code in module.__dict__
	_sys.modules[__name__].__dict__[name] = module
	return True

#----------------------------------------------------------------------
# port from _endian.py in ctypes
#----------------------------------------------------------------------
package_endian = \
'''
import sys
from ctypes import *

_array_type = type(c_int * 3)
def _other_endian(typ):
    try:
        return getattr(typ, _OTHER_ENDIAN)
    except AttributeError:
        if type(typ) == _array_type:
            return _other_endian(typ._type_) * typ._length_
        raise TypeError("This type does not support other endian: %s" % typ)

class _swapped_meta(type(Structure)):
    def __setattr__(self, attrname, value):
        if attrname == "_fields_":
            fields = []
            for desc in value:
                name = desc[0]
                typ = desc[1]
                rest = desc[2:]
                fields.append((name, _other_endian(typ)) + rest)
            value = fields
        super(_swapped_meta, self).__setattr__(attrname, value)

if sys.byteorder == "little":
    _OTHER_ENDIAN = "__ctype_be__"
    LittleEndianStructure = Structure
    class BigEndianStructure(Structure):
        __metaclass__ = _swapped_meta
        _swappedbytes_ = None
elif sys.byteorder == "big":
    _OTHER_ENDIAN = "__ctype_le__"
    BigEndianStructure = Structure
    class LittleEndianStructure(Structure):
        __metaclass__ = _swapped_meta
        _swappedbytes_ = None
else:
    raise RuntimeError("Invalid byteorder")
'''

install_package('_endian', package_endian)


from ctypes._endian import BigEndianStructure, LittleEndianStructure

# Fill in specifically-sized types
c_int8 = c_byte
c_uint8 = c_ubyte
for kind in [c_short, c_int, c_long, c_longlong]:
    if sizeof(kind) == 2: c_int16 = kind
    elif sizeof(kind) == 4: c_int32 = kind
    elif sizeof(kind) == 8: c_int64 = kind
for kind in [c_ushort, c_uint, c_ulong, c_ulonglong]:
    if sizeof(kind) == 2: c_uint16 = kind
    elif sizeof(kind) == 4: c_uint32 = kind
    elif sizeof(kind) == 8: c_uint64 = kind
del(kind)


#----------------------------------------------------------------------
# port from wintypes.py in ctypes
#----------------------------------------------------------------------
package_wintypes = \
'''
######################################################################
#  This file should be kept compatible with Python 2.3, see PEP 291. #
######################################################################

# The most useful windows datatypes
from ctypes import *

BYTE = c_byte
WORD = c_ushort
DWORD = c_ulong

WCHAR = c_wchar
UINT = c_uint

DOUBLE = c_double

BOOLEAN = BYTE
BOOL = c_long

from ctypes import _SimpleCData
class VARIANT_BOOL(_SimpleCData):
    _type_ = "v"
    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.value)

ULONG = c_ulong
LONG = c_long

# in the windows header files, these are structures.
_LARGE_INTEGER = LARGE_INTEGER = c_longlong
_ULARGE_INTEGER = ULARGE_INTEGER = c_ulonglong

LPCOLESTR = LPOLESTR = OLESTR = c_wchar_p
LPCWSTR = LPWSTR = c_wchar_p
LPCSTR = LPSTR = c_char_p

WPARAM = c_uint
LPARAM = c_long

ATOM = WORD
LANGID = WORD

COLORREF = DWORD
LGRPID = DWORD
LCTYPE = DWORD

LCID = DWORD

################################################################
# HANDLE types
HANDLE = c_ulong # in the header files: void *

HACCEL = HANDLE
HBITMAP = HANDLE
HBRUSH = HANDLE
HCOLORSPACE = HANDLE
HDC = HANDLE
HDESK = HANDLE
HDWP = HANDLE
HENHMETAFILE = HANDLE
HFONT = HANDLE
HGDIOBJ = HANDLE
HGLOBAL = HANDLE
HHOOK = HANDLE
HICON = HANDLE
HINSTANCE = HANDLE
HKEY = HANDLE
HKL = HANDLE
HLOCAL = HANDLE
HMENU = HANDLE
HMETAFILE = HANDLE
HMODULE = HANDLE
HMONITOR = HANDLE
HPALETTE = HANDLE
HPEN = HANDLE
HRGN = HANDLE
HRSRC = HANDLE
HSTR = HANDLE
HTASK = HANDLE
HWINSTA = HANDLE
HWND = HANDLE
SC_HANDLE = HANDLE
SERVICE_STATUS_HANDLE = HANDLE

################################################################
# Some important structure definitions

class RECT(Structure):
    _fields_ = [("left", c_long),
                ("top", c_long),
                ("right", c_long),
                ("bottom", c_long)]
tagRECT = _RECTL = RECTL = RECT

class _SMALL_RECT(Structure):
    _fields_ = [('Left', c_short),
                ('Top', c_short),
                ('Right', c_short),
                ('Bottom', c_short)]
SMALL_RECT = _SMALL_RECT

class _COORD(Structure):
    _fields_ = [('X', c_short),
                ('Y', c_short)]

class POINT(Structure):
    _fields_ = [("x", c_long),
                ("y", c_long)]
tagPOINT = _POINTL = POINTL = POINT

class SIZE(Structure):
    _fields_ = [("cx", c_long),
                ("cy", c_long)]
tagSIZE = SIZEL = SIZE

def RGB(red, green, blue):
    return red + (green << 8) + (blue << 16)

class FILETIME(Structure):
    _fields_ = [("dwLowDateTime", DWORD),
                ("dwHighDateTime", DWORD)]
_FILETIME = FILETIME

class MSG(Structure):
    _fields_ = [("hWnd", HWND),
                ("message", c_uint),
                ("wParam", WPARAM),
                ("lParam", LPARAM),
                ("time", DWORD),
                ("pt", POINT)]
tagMSG = MSG
MAX_PATH = 260

class WIN32_FIND_DATAA(Structure):
    _fields_ = [("dwFileAttributes", DWORD),
                ("ftCreationTime", FILETIME),
                ("ftLastAccessTime", FILETIME),
                ("ftLastWriteTime", FILETIME),
                ("nFileSizeHigh", DWORD),
                ("nFileSizeLow", DWORD),
                ("dwReserved0", DWORD),
                ("dwReserved1", DWORD),
                ("cFileName", c_char * MAX_PATH),
                ("cAlternameFileName", c_char * 14)]

class WIN32_FIND_DATAW(Structure):
    _fields_ = [("dwFileAttributes", DWORD),
                ("ftCreationTime", FILETIME),
                ("ftLastAccessTime", FILETIME),
                ("ftLastWriteTime", FILETIME),
                ("nFileSizeHigh", DWORD),
                ("nFileSizeLow", DWORD),
                ("dwReserved0", DWORD),
                ("dwReserved1", DWORD),
                ("cFileName", c_wchar * MAX_PATH),
                ("cAlternameFileName", c_wchar * 14)]

__all__ = ['ATOM', 'BOOL', 'BOOLEAN', 'BYTE', 'COLORREF', 'DOUBLE',
           'DWORD', 'FILETIME', 'HACCEL', 'HANDLE', 'HBITMAP', 'HBRUSH',
           'HCOLORSPACE', 'HDC', 'HDESK', 'HDWP', 'HENHMETAFILE', 'HFONT',
           'HGDIOBJ', 'HGLOBAL', 'HHOOK', 'HICON', 'HINSTANCE', 'HKEY',
           'HKL', 'HLOCAL', 'HMENU', 'HMETAFILE', 'HMODULE', 'HMONITOR',
           'HPALETTE', 'HPEN', 'HRGN', 'HRSRC', 'HSTR', 'HTASK', 'HWINSTA',
           'HWND', 'LANGID', 'LARGE_INTEGER', 'LCID', 'LCTYPE', 'LGRPID',
           'LONG', 'LPARAM', 'LPCOLESTR', 'LPCSTR', 'LPCWSTR', 'LPOLESTR',
           'LPSTR', 'LPWSTR', 'MAX_PATH', 'MSG', 'OLESTR', 'POINT',
           'POINTL', 'RECT', 'RECTL', 'RGB', 'SC_HANDLE',
           'SERVICE_STATUS_HANDLE', 'SIZE', 'SIZEL', 'SMALL_RECT', 'UINT',
           'ULARGE_INTEGER', 'ULONG', 'VARIANT_BOOL', 'WCHAR',
           'WIN32_FIND_DATAA', 'WIN32_FIND_DATAW', 'WORD', 'WPARAM', '_COORD',
           '_FILETIME', '_LARGE_INTEGER', '_POINTL', '_RECTL', '_SMALL_RECT',
           '_ULARGE_INTEGER', 'tagMSG', 'tagPOINT', 'tagRECT', 'tagSIZE']
'''

install_package('wintypes', package_wintypes)

#----------------------------------------------------------------------
# port from util.py in ctypes
#----------------------------------------------------------------------
package_util = \
'''
######################################################################
#  This file should be kept compatible with Python 2.3, see PEP 291. #
######################################################################
import sys, os

# find_library(name) returns the pathname of a library, or None.
if os.name == "nt":
    def find_library(name):
        # See MSDN for the REAL search order.
        for directory in os.environ['PATH'].split(os.pathsep):
            fname = os.path.join(directory, name)
            if os.path.exists(fname):
                return fname
            if fname.lower().endswith(".dll"):
                continue
            fname = fname + ".dll"
            if os.path.exists(fname):
                return fname
        return None

if os.name == "ce":
    # search path according to MSDN:
    # - absolute path specified by filename
    # - The .exe launch directory
    # - the Windows directory
    # - ROM dll files (where are they?)
    # - OEM specified search path: HKLM\Loader\SystemPath
    def find_library(name):
        # Does it make sense to implement this correctly?  For now we
        # fake.
        #
        # The proper solution (also for windows) would be to call
        # LoadLibraryEx(name, NULL, LOAD_LIBRARY_AS_DATAFILE), then
        # get the module name with GetModuleFileName and return that.
        #
        # OTOH, why use find_library on windows at all?
        if not "." in name:
            name += ".dll"
        return os.path.exists(name)

if os.name == "posix" and sys.platform == "darwin":
    from ctypes.macholib.dyld import dyld_find as _dyld_find
    def find_library(name):
        possible = ['lib%s.dylib' % name,
                    '%s.dylib' % name,
                    '%s.framework/%s' % (name, name)]
        for name in possible:
            try:
                return _dyld_find(name)
            except ValueError:
                continue
        return None

elif os.name == "posix":
    # Andreas Degert's find functions, using gcc, /sbin/ldconfig, objdump
    import re, tempfile, errno

    def _findLib_gcc(name):
        expr = '[^\(\)\s]*lib%s\.[^\(\)\s]*' % name
        fdout, ccout = tempfile.mkstemp()
        os.close(fdout)
        cmd = 'if type gcc &>/dev/null; then CC=gcc; else CC=cc; fi;' \
              '$CC -Wl,-t -o ' + ccout + ' 2>&1 -l' + name
        try:
            fdout, outfile =  tempfile.mkstemp()
            os.close(fdout)
            fd = os.popen(cmd)
            trace = fd.read()
            err = fd.close()
        finally:
            try:
                os.unlink(outfile)
            except OSError, e:
                if e.errno != errno.ENOENT:
                    raise
            try:
                os.unlink(ccout)
            except OSError, e:
                if e.errno != errno.ENOENT:
                    raise
        res = re.search(expr, trace)
        if not res:
            return None
        return res.group(0)

    def _findLib_ld(name):
        expr = '/[^\(\)\s]*lib%s\.[^\(\)\s]*' % name
        res = re.search(expr, os.popen('/sbin/ldconfig -p 2>/dev/null').read())
        if not res:
            # Hm, this works only for libs needed by the python executable.
            cmd = 'ldd %s 2>/dev/null' % sys.executable
            res = re.search(expr, os.popen(cmd).read())
            if not res:
                return None
        return res.group(0)

    def _get_soname(f):
        cmd = "objdump -p -j .dynamic 2>/dev/null " + f
        res = re.search(r'\sSONAME\s+([^\s]+)', os.popen(cmd).read())
        if not res:
            return None
        return res.group(1)

    def find_library(name):
        lib = _findLib_ld(name) or _findLib_gcc(name)
        if not lib:
            return None
        return _get_soname(lib)

'''

install_package('util', package_util)


