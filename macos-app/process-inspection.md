# Reading other processes

For an app that finds other processes, their parents, their paths or the app that owns them. Same user unless a line says otherwise. All calls are in `Darwin` except `NSRunningApplication` (AppKit).

| Need | Use | Do not use |
|---|---|---|
| All pids | `proc_listallpids` | |
| Short name | `proc_name` | |
| Parent pid | `sysctl` `[CTL_KERN, KERN_PROC, KERN_PROC_PID, pid]`, `kinfo_proc.kp_eproc.e_ppid`; it also reads root processes, as `ps` does | `proc_pidinfo`: it cannot read root processes (such as `login` between a terminal and its shell), so the walk up stops there |
| Executable path, arguments, environment | `sysctl` `[CTL_KERN, KERN_PROCARGS2, pid]` | `proc_pidpath`: it returns empty over SSH |
| The app a process runs in | Walk up the parents to the first `NSRunningApplication` with `.regular` activation policy; else the app around the executable (below) | |

## `KERN_PROCARGS2` layout

One buffer: `argc` (Int32), the executable path, zero padding, `argc` argument strings, then the environment strings until an empty one. All strings end with a zero byte. Ask for the size first (call with a nil buffer), then read.

```swift
var mib: [Int32] = [CTL_KERN, KERN_PROCARGS2, pid]
var size = 0
guard sysctl(&mib, 3, nil, &size, nil, 0) == 0, size > 4 else { return nil }
var bytes = [UInt8](repeating: 0, count: size)
guard sysctl(&mib, 3, &bytes, &size, nil, 0) == 0 else { return nil }
let argc = Int(bytes.withUnsafeBytes { $0.load(as: Int32.self) })
// From offset 4: path, skip zero bytes, argc strings, then "NAME=value" strings until an empty one.
```

A process can change its name: Node sets `process.title`, so `proc_name` says `node` and `argv[0]` has the real name.

## Helper apps inside another app

Some apps run their shells or workers in a helper app inside their bundle (for example `X.app/Contents/Helpers/X-helper.app`). The helper is not in `NSRunningApplication`, or it is not `.regular`, and it can outlive a restart of the main app (it then runs under launchd). So the walk up the parents does not find the main app. Take the outermost `.app` in the process's executable path, read its bundle id, and find the running regular app with that id:

```swift
func appAround(_ pid: pid_t) -> NSRunningApplication? {
    let path = executablePath(of: pid)  // from KERN_PROCARGS2
    guard let end = path.range(of: ".app/")?.lowerBound,
          let id = Bundle(path: path[..<end] + ".app")?.bundleIdentifier else { return nil }
    return NSRunningApplication.runningApplications(withBundleIdentifier: id).first { $0.activationPolicy == .regular }
}
```

Example: a terminal multiplexer (herdr) that runs in rootshell. Its shells are children of rootshell-helper, so the walk finds no regular app until `appAround` gives rootshell. A process over SSH has no app above it.
