# DNS Guard

Most operating systems with TCP/IP support baked right into the crust realize that DNS is of such critical importance to everything else in the stack that a single, unambiguous source of truth is a hard requirement for keeping track of name resolvers. Almost 30 years ago, some lonely little boy with a chip on his shoulder at Apple decided that this wasn't complicated enough so he invented the "System Configuration" K/V store which curates a potentially endless number of sources of truth in an extremely opaque way, clumsily backporting its many conflicting, concurrent states into `/etc/resolv.conf` for compatibility with all the tools that do not give a shit what Apple thinks is shippable.

The results of this architectural choice have yielded no tangible benefit to anyone, anywhere, but the design persists to this day because nobody else wants to go near that butthurt little boy's bullshit-ass code. Things being what they are, you can frequently find yourself in frustrating situations where something resolves in Safari but not in Chrome. Or maybe it resolves in Chrome but not Safari. Or maybe it resolves in Chrome *and* Safari but not in `dig`. Or maybe it resolves everywhere perfectly and then you connect to a VPN and suddenly link-local names break even though the routing table looks perfectly fine and System Settings shows you the expected resolver addresses in its UI. All this turmoil because of one boy's love of résumé-driven-development coupled with his fear of being replaced by one of Steve's friends if he didn't use every single thing he ever learned in CS clown college. Verily, Millennials took much from his tutelage.

# I'm Real Tired, Hoss

This tool's purpose is to serve as a cast iron middle finger you can shove up Johnny Applequeef's diabetic ass whenever you get tired of deciphering what `scutil` says and just want **one specific set of nameservers consulted at all times on all interfaces.** It does this by watching all of the DNS-related keys in the System Configuration data store for changes. When one occurrs that brings the list of active resolvers out of compliance with your wishes it snaps it back in line by force. No mercy. 

This will *definitely* leave your System Settings UI out of sync and there is tremendous potential for competition with some other piece of software's attempt to do the exact same thing in which case you'd have two or more System Configuration observers repeatedly flipping the same switches back and forth over and over ad infinitum. For this reason, most normal people should never even attempt to run this tool. If you want to do it anyway, here it is. Add it to `launchd` if you want it to run all the time. 

Apple has recently exposed a new app extension interface which lets you write your own **DNS Proxy** capable of diverting all DNS traffic to one specific location. This would probably be a much better way of accomplishing things than my approach here, but you can't even build a **DNS Proxy** extension without joining their paid developer program so fuck them.

# Installation

This might not actually require Python 3.11.10, that's just all I've tested it on because I'm too lazy to keep up with what the cool kids are doing with their trendy Rust editors that don't work at all without Node for some reason. I'm also not installing Tahoe for any amount of money. Y'all can miss me with that noise.

If you'd rather not clone anything: 

```
pip install https://raw.githubusercontent.com/TheKayThatWasOrange/DNSGuard/master/dist/dnsguard-0.1.0-py3-none-any.whl
```

Otherwise, clone and `uv build`. 

Note that `pyobjc` is **HUGE**. There's probably a way to only drag in the modules you care about but I couldn't get it to work and gave up. 

# Usage

This stupid trick only works with escalated privileges. Sorry.

```
sudo dnsguard 192.168.192.108, 1.1.1.1, 9.9.9.9
```

```
Password: ****
State:/Network/Service/1B48DC4B-2BF3-4097-A936-3FBDF6903D23/DNS is in compliance.
State:/Network/Global/DNS is in compliance.
Watching the store for changes...
```

# Fixing Broken Shit

If this tool does something unexpected and you need to put it back the way it was but have never suffered through `scutil` before, here's an example of what that looks like:

```
sudo scutil
get State:/Network/Global/DNS
d.remove ServerAddresses
d.add ServerAddresses * 192.168.192.108 1.1.1.1 9.9.9.9
set State:/Network/Global/DNS
exit

killall -HUP mDNSResponder
```

