import typer
import re
import SystemConfiguration
import dispatch
from ordered_set import OrderedSet
from PyObjCTools import AppHelper
from rich import print

DNS_KEY_PATTERN = ".*DNS"
IS_IP_ADDRESS = re.compile(r"^(((?!25?[6-9])[12]\d|[1-9])?\d\.?\b){4}$", re.IGNORECASE)

app = typer.Typer(pretty_exceptions_show_locals=True)


@app.command()
def main(preferred_servers: list[str]):
    """
    Pass a list of IPv4 addresses for the nameservers
    you would like MacOS to use on EVERY network interface without question.
    If you're the one person in the world who cares about IPv6 then you
    can go ahead and add that to the regex. NAT won a long, long time ago.

    Example:

        dnsguard 192.168.1.2, 9.9.9.9, 1.1.1.1
    """
    for i, server in enumerate(preferred_servers):
        # Strip commas and anything else that isn't
        # part of an IPv4 address.
        preferred_servers[i] = re.sub(r"[^0-9\.]", "", server)
        if not IS_IP_ADDRESS.match(preferred_servers[i]):
            print(f"'{preferred_servers[i]}' is not an IPv4 address.")
            raise typer.Abort()

    valid_servers = OrderedSet(preferred_servers)

    def compliance_enforcer(store, keys, context=None):
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
        None, "DNSGuard", compliance_enforcer, None
    )

    dns_related_keys = SystemConfiguration.SCDynamicStoreCopyKeyList(
        store, DNS_KEY_PATTERN
    )

    # Manually fire the callback once to pick up any non-compliance
    # without waiting around for something to change.
    compliance_enforcer(store, dns_related_keys)

    # Then start watching all present (and future) keys for changes.
    if SystemConfiguration.SCDynamicStoreSetNotificationKeys(
        store, None, [DNS_KEY_PATTERN]
    ):
        # dispatch_queue_create() does not seem to be usable at all.
        # Grab the main queue instead since we don't actually have
        # anything better to do in our run loop.
        dispatch_queue = dispatch.dispatch_get_main_queue()

        if SystemConfiguration.SCDynamicStoreSetDispatchQueue(store, dispatch_queue):
            print("Watching the store for changes...")
            # This handles keyboard input. dispatch_main() does not.
            AppHelper.runConsoleEventLoop(installInterrupt=True)
        else:
            print("What the hell, man?")
            raise typer.Abort()
    else:
        print("Couldn't set notification keys.")
        raise typer.Abort()


if __name__ == "__main__":
    app()
