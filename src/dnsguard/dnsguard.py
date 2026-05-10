import SystemConfiguration
import dispatch
from PyObjCTools import AppHelper


def main():
    store = SystemConfiguration.SCDynamicStoreCreate(
        None, "DNSGuard", config_callback, None
    )

    dns_related_keys = SystemConfiguration.SCDynamicStoreCopyKeyList(store, ".*DNS")

    if SystemConfiguration.SCDynamicStoreSetNotificationKeys(
        store, dns_related_keys, None
    ):
        # dispatch_queue_create() does not seem to be usable at all.
        # Grab the main queue instead since we don't actually have
        # anything better to do.
        dispatch_queue = dispatch.dispatch_get_main_queue()

        if SystemConfiguration.SCDynamicStoreSetDispatchQueue(store, dispatch_queue):
            print("Now Watching: ")
            print(dns_related_keys)
            print(store)

            # dispatch.dispatch_main()
            AppHelper.runConsoleEventLoop(installInterrupt=True)


def config_callback(store, keys, context):
    print(f"Some shit changed in {keys}:")
    for key in keys:
        value = SystemConfiguration.SCDynamicStoreCopyValue(store, key)
        print(value)


if __name__ == "__main__":
    main()
