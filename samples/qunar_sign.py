import logging
import posixpath
import sys

from unicorn import UcError, UC_HOOK_MEM_UNMAPPED, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_READ
from unicorn.arm_const import *

from androidemu.emulator import Emulator
from androidemu.java.java_class_def import JavaClassDef
from androidemu.java.java_method_def import java_method_def

from samples import debug_utils


# Create java class.
class ConfigurationActivity(metaclass=JavaClassDef, jvm_name='com/mqunar/atom/debugsetting/ConfigurationActivity'):
    pass


class QBugActivity(metaclass=JavaClassDef, jvm_name='com/qunar/qbug/sdk/ui/activity/QBugActivity'):
    pass


class ActivityThread(metaclass=JavaClassDef, jvm_name='android/app/ActivityThread'):

    @staticmethod
    @java_method_def(name='currentActivityThread', signature='()Landroid/app/ActivityThread;')
    def current_activity_thread(mu):
        return ActivityThread()

    @java_method_def(name='getApplication', signature='()Landroid/app/Application;')
    def get_application(self, mu):
        return Application()


class Application(metaclass=JavaClassDef, jvm_name='android/app/Application'):

    @java_method_def(name='getPackageName', signature='()Ljava/lang/String;')
    def get_package_name(self, mu):
        return "com.Qunar"


class EnvChecker(metaclass=JavaClassDef, jvm_name='com/mqunar/atom/defensive/utils/EnvChecker'):
    pass


class SDInfo(metaclass=JavaClassDef, jvm_name='com/mqunar/atom/defensive/utils/SDInfo'):
    pass


# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)7s %(name)34s | %(message)s",
)

logger = logging.getLogger(__name__)

# Initialize emulator
emulator = Emulator(
    vfp_inst_set=True,
    vfs_root=posixpath.join(posixpath.dirname(__file__), "vfs")
)

# Register Java class.
emulator.java_classloader.add_class(EnvChecker)
emulator.java_classloader.add_class(SDInfo)
emulator.java_classloader.add_class(ConfigurationActivity)
emulator.java_classloader.add_class(QBugActivity)
emulator.java_classloader.add_class(ActivityThread)
emulator.java_classloader.add_class(Application)

# Load all libraries.
emulator.load_library("example_binaries/libdl.so")
emulator.load_library("example_binaries/libc.so")
emulator.load_library("example_binaries/libstdc++.so")
emulator.load_library("example_binaries/libm.so")
emulator.load_library("example_binaries/libz.so")
emulator.load_library("example_binaries/liblog.so")
emulator.load_library("example_binaries/qunar/liblottie.so")
lib_module = emulator.load_library("example_binaries/qunar/libturbo.so")
# 修正malloc free地址
emulator.mu.mem_write(lib_module.base + 0x123388, b'\x49\x85\xbe\xcb')
emulator.mu.mem_write(lib_module.base + 0x12338C, b'\x09\x85\xbe\xcb')

# Show loaded modules.
logger.info("Loaded modules:")

for module in emulator.modules:
    logger.info("=> 0x%08x - %s" % (module.base, module.filename))

# Debug
# emulator.mu.hook_add(UC_HOOK_CODE, debug_utils.hook_code)
# emulator.mu.hook_add(UC_HOOK_MEM_UNMAPPED, debug_utils.hook_unmapped)
# emulator.mu.hook_add(UC_HOOK_MEM_WRITE, debug_utils.hook_mem_write)
# emulator.mu.hook_add(UC_HOOK_MEM_READ, debug_utils.hook_mem_read)

try:
    # 签名
    data = '{"usedCache":false,"lowestPrice":0,"adultCount":0,"arrCity":"上海","rnVersionInter":427,"depCity":"北京","goDate":"2020-07-13","rnVersionInland":692,"source":"homeClickSearch","isSearchDebug":0,"cabinType":"0","hasChildPrice":"0","uuid":"","queryId":"-1","scene":0,"bigTrafficCount":0,"qpInfos":{"flight_sell_rn":0,"flight_orderdetail_rn":228,"f_flight_fuwu_rn":78,"route_service_rn":156,"flight_seat_rn":262,"flight_booking_rn":323,"f_major_bundle_rn":692,"flight_package_rn":0,"f_flight_search_rn":427,"f_flight_additional_bundle_rn":80,"f_home_rn":318,"flight_routing_rn":0,"f_order_rn":128,"f_walkmap_rn":0},"hitType":0,"times":0,"rnVersion":318,"fromRecommend":false,"lowPrice":1,"cat":"FHCabinType0-RN_SEARCH","isChangeDate":false,"isPart":false,"planeDesc":"0","routeType":0,"searchType":0,"more":-1,"buyFlightPosition":0,"count":16,"doubleList":0,"firstRequest":true,"childCount":0,"priceSortType":0,"sort":5,"underageOption":"","preSearchAbTest":"a","bigTrafficQueryId":"-1","startNum":0}'
    debug_utils.libgoblin_addresss = lib_module.base
    ret = emulator.call_native(lib_module.base + 0x1186F5, emulator.java_vm.jni_env.address_ptr, 0, data)
    print(ret)
except UcError as e:
    print("Exit at %x" % emulator.mu.reg_read(UC_ARM_REG_PC))
    raise
