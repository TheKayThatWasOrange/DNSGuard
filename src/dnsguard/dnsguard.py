import typer
import re
import SystemConfiguration
import dispatch
from ordered_set import OrderedSet
from PyObjCTools import AppHelper
from rich import print

IS_IP_ADDRESS = re.compile(r"^(((?!25?[6-9])[12]\d|[1-9])?\d\.?\b){4}$", re.IGNORECASE)


def main(preferred_servers: list[str]):

    for server in preferred_servers:
        if not IS_IP_ADDRESS.match(server):
            print(f"'{server}' is not an IPv4 address.")
            raise typer.Abort()

    valid_servers = OrderedSet(preferred_servers)

    def config_callback(store, keys, context=None):
        for key in keys:
            value = SystemConfiguration.SCDynamicStoreCopyValue(store, key)

            try:
                stored_servers = value.get("ServerAddresses", None)

                if stored_servers is None:
                    stored_servers = [value.get("ServerAddress", None)]

                if set(stored_servers) != valid_servers:
                    print(f"[red]{key}: {stored_servers} != {valid_servers}[/red]")
                else:
                    print(f"[green]{key} is in compliance.[/green]")
            except Exception:
                print(
                    f"[yellow]{key} cannot be verified and is probably irrelevant.[/yellow]"
                )
                pass

    store = SystemConfiguration.SCDynamicStoreCreate(
        None, "DNSGuard", config_callback, None
    )

    dns_related_keys = SystemConfiguration.SCDynamicStoreCopyKeyList(store, ".*DNS")

    # Manually fire the callback once to pick up any non-compliance
    # without waiting around for something to change.
    config_callback(store, dns_related_keys)

    # Then start watching those same keys for future changes.
    if SystemConfiguration.SCDynamicStoreSetNotificationKeys(
        store, dns_related_keys, None
    ):
        # dispatch_queue_create() does not seem to be usable at all.
        # Grab the main queue instead since we don't actually have
        # anything better to do.
        dispatch_queue = dispatch.dispatch_get_main_queue()

        if SystemConfiguration.SCDynamicStoreSetDispatchQueue(store, dispatch_queue):
            print("Watching the store for changes...")
            # This handles keyboard input. dispatch_main() does not.
            AppHelper.runConsoleEventLoop(installInterrupt=True)


if __name__ == "__main__":
    typer.run(main)
