import AppKit
import ApplicationServices
import ImageIO
import ScreenCaptureKit
import UniformTypeIdentifiers
import Vision

struct WindowError: LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}

struct Request: Decodable {
    let action: String
    let frame: String?
    let x: Int?
    let y: Int?
}

struct Frame {
    let id: String
    let pid: pid_t
    let windowID: CGWindowID
    let title: String
    let bounds: CGRect
    let width: Int
    let height: Int
    let taken: Date
}

// Observe only the two events marked by this single diagnostic click, at the stream PID.
final class ClickTrace {
    let marker = Int64.random(in: 1...Int64.max)
    private let lock = NSLock()
    private var events: [String] = []
    private var tap: CFMachPort?
    private var source: CFRunLoopSource?

    func start(pid: pid_t) throws {
        let mask = (CGEventMask(1) << CGEventType.leftMouseDown.rawValue) |
                   (CGEventMask(1) << CGEventType.leftMouseUp.rawValue)
        let context = Unmanaged.passUnretained(self).toOpaque()
        guard let port = CGEvent.tapCreateForPid(pid: pid, place: .tailAppendEventTap,
            options: .listenOnly, eventsOfInterest: mask, callback: { _, kind, event, ref in
                if let ref, kind == .leftMouseDown || kind == .leftMouseUp {
                    let trace = Unmanaged<ClickTrace>.fromOpaque(ref).takeUnretainedValue()
                    if event.getIntegerValueField(.eventSourceUserData) == trace.marker {
                        trace.lock.lock()
                        trace.events.append(kind == .leftMouseDown ? "down" : "up")
                        trace.lock.unlock()
                    }
                }
                return Unmanaged.passUnretained(event)
            }, userInfo: context),
            let loopSource = CFMachPortCreateRunLoopSource(nil, port, 0)
        else { throw WindowError("当前桌面无法观察串流进程的点击队列；未发送测试点击。") }
        tap = port
        source = loopSource
        CFRunLoopAddSource(CFRunLoopGetMain(), loopSource, .commonModes)
        CGEvent.tapEnable(tap: port, enable: true)
    }

    func summary() -> String {
        lock.lock()
        defer { lock.unlock() }
        return "串流进程事件探针观测：" + (events.isEmpty ? "无标记事件" : events.joined(separator: ","))
    }

    func stop() {
        if let tap { CGEvent.tapEnable(tap: tap, enable: false); CFMachPortInvalidate(tap) }
        if let source { CFRunLoopRemoveSource(CFRunLoopGetMain(), source, .commonModes) }
    }
}

struct GameSettings: Decodable {
    struct Steam: Decodable {
        let appId: String
        let titles: [String]
        let nativeProcessNames: [String]?
        let warningReference: String?
        let warningCrop: [Double]?
        let remoteDesktopRecovery: Bool?
    }
    let name: String
    let steam: Steam
}

@main
struct SteamWindow {
    let game: GameSettings
    let profileURL: URL

    func targetIfPresent() async throws -> SCWindow? {
        let content = try await SCShareableContent.excludingDesktopWindows(true, onScreenWindowsOnly: false)
        let candidates = content.windows.filter { window in
            guard let app = window.owningApplication,
                  window.windowLayer == 0, window.frame.width >= 320, window.frame.height >= 180
            else { return false }
            let name = NSRunningApplication(processIdentifier: app.processID)?.executableURL?.lastPathComponent
            if let name, game.steam.nativeProcessNames?.contains(name) == true, isGame(window.title) { return true }
            return app.bundleIdentifier == "com.valvesoftware.steam.streamingclient" || name == "streaming_client"
        }
        let visible = candidates.filter(\.isOnScreen)
        let available = visible.isEmpty ? candidates : visible
        let named = available.filter { isGame($0.title) }
        let allowRecovery = game.steam.remoteDesktopRecovery == true
        let matches = named.isEmpty && allowRecovery ? available : named
        guard matches.count <= 1 else { throw WindowError("找到多个串流窗口，请只保留目标游戏的串流。") }
        return matches.first
    }

    func target() async throws -> SCWindow {
        guard let window = try await targetIfPresent() else { throw WindowError("等待 Steam 游戏串流窗口。") }
        return window
    }

    func matchesWarning(_ image: CGImage, reference: URL) -> Bool {
        guard let source = CGImageSourceCreateWithURL(reference as CFURL, nil),
              let example = CGImageSourceCreateImageAtIndex(source, 0, nil) else { return false }
        guard let box = game.steam.warningCrop, box.count == 4 else { return false }
        let width = Double(image.width), height = Double(image.height)
        let rect = CGRect(x: box[0] * width, y: box[1] * height,
                          width: box[2] * width, height: box[3] * height)
        guard let panel = image.cropping(to: rect.integral) else { return false }
        func grayscale(_ source: CGImage) -> [UInt8]? {
            let width = 144, height = 60
            var bytes = [UInt8](repeating: 0, count: width * height)
            let drawn = bytes.withUnsafeMutableBytes { buffer in
                guard let ctx = CGContext(data: buffer.baseAddress, width: width, height: height,
                                          bitsPerComponent: 8, bytesPerRow: width, space: CGColorSpaceCreateDeviceGray(),
                                          bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return false }
                ctx.interpolationQuality = .high
                ctx.draw(source, in: CGRect(x: 0, y: 0, width: width, height: height))
                return true
            }
            return drawn ? bytes : nil
        }
        guard let actual = grayscale(panel), let expected = grayscale(example) else { return false }
        let difference = zip(actual, expected).reduce(0) { $0 + abs(Int($1.0) - Int($1.1)) }
        return difference < 6 * actual.count
    }

    func capture(_ window: SCWindow, in directory: URL, requireGame: Bool = false) throws -> Frame {
        guard let app = window.owningApplication else { throw WindowError("串流进程已退出。") }
        let raw = directory.appendingPathComponent("capture-\(UUID().uuidString).png")
        defer { try? FileManager.default.removeItem(at: raw) }
        let capture = Process()
        capture.executableURL = URL(fileURLWithPath: "/usr/sbin/screencapture")
        capture.arguments = ["-x", "-o", "-l\(window.windowID)", raw.path]
        try capture.run()
        capture.waitUntilExit()
        guard capture.terminationStatus == 0,
              let source = CGImageSourceCreateWithURL(raw as CFURL, nil) else {
            throw WindowError("未能截取串流窗口 \(window.windowID)；等待下一次尝试。")
        }
        let options: [CFString: Any] = [kCGImageSourceCreateThumbnailFromImageAlways: true,
                                        kCGImageSourceThumbnailMaxPixelSize: 1600]
        guard let image = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary)
        else { throw WindowError("无法解码串流窗口截图。") }
        if requireGame && !isGame(window.title) {
            guard let reference = game.steam.warningReference,
                  matchesWarning(image, reference: profileURL.deletingLastPathComponent().appendingPathComponent(reference)) else {
                throw WindowError("标题未匹配，当前画面也未识别为已知游戏提示页。")
            }
        }
        let data = NSMutableData()
        guard let writer = CGImageDestinationCreateWithData(data, UTType.png.identifier as CFString, 1, nil)
        else { throw WindowError("无法创建窗口截图。") }
        CGImageDestinationAddImage(writer, image, nil)
        guard CGImageDestinationFinalize(writer) else { throw WindowError("无法编码截图。") }
        try (data as Data).write(to: directory.appendingPathComponent("frame.png"), options: .atomic)
        return Frame(id: UUID().uuidString, pid: app.processID, windowID: window.windowID, title: window.title ?? "",
                     bounds: window.frame, width: image.width, height: image.height, taken: Date())
    }

    func isGame(_ title: String?) -> Bool {
        let name = (title ?? "").lowercased().replacingOccurrences(of: " ", with: "")
        return game.steam.titles.contains { name.contains($0.lowercased().replacingOccurrences(of: " ", with: "")) }
    }

    func remoteTitle(_ title: String?) -> String {
        (title ?? "").replacingOccurrences(of: "[Streaming]", with: "")
            .trimmingCharacters(in: .whitespaces)
    }

    func postKey(_ code: CGKeyCode, flags: CGEventFlags = [], to pid: pid_t) async throws {
        guard let source = CGEventSource(stateID: .hidSystemState),
              let down = CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: true),
              let up = CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: false)
        else { throw WindowError("无法构造串流按键。") }
        down.flags = flags
        up.flags = flags
        down.postToPid(pid)
        try await Task.sleep(for: .milliseconds(45))
        up.postToPid(pid)
        try await Task.sleep(for: .milliseconds(35))
    }

    func readLabels(from image: URL, frame: Frame, to output: URL) throws {
        let request = VNRecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.recognitionLanguages = ["zh-Hans", "en-US"]
        request.usesLanguageCorrection = false
        try VNImageRequestHandler(url: image).perform([request])
        let labels: [[String: Any]] = (request.results ?? []).compactMap { item in
            guard let text = item.topCandidates(1).first else { return nil }
            let box = item.boundingBox
            return ["text": text.string, "confidence": text.confidence,
                    "x": Int(box.midX * Double(frame.width)),
                    "y": Int((1 - box.midY) * Double(frame.height))]
        }
        try JSONSerialization.data(withJSONObject: ["frame": frame.id, "labels": labels])
            .write(to: output, options: .atomic)
    }

    func input(_ request: Request, frame: Frame?, window: SCWindow, trace: ClickTrace? = nil) async throws {
        guard let f = frame, f.id == request.frame, Date().timeIntervalSince(f.taken) < 90,
              f.pid == window.owningApplication?.processID, f.windowID == window.windowID,
              f.bounds == window.frame, f.title == (window.title ?? "") else {
            throw WindowError("截图已失效或远端窗口已切换，请重新截图。")
        }
        if !AXIsProcessTrusted() {
            let prompt = kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String
            guard AXIsProcessTrustedWithOptions([prompt: true] as CFDictionary) else {
                throw WindowError("请按 macOS 提示允许辅助功能，再重试点击。")
            }
        }
        guard let app = NSRunningApplication(processIdentifier: f.pid) else { throw WindowError("串流进程已退出。") }
        if !app.isActive {
            _ = app.activate()
            try await Task.sleep(for: .milliseconds(450))
        }
        guard app.isActive else { throw WindowError("请将游戏串流窗口切到前台。") }
        let focused = try await target()
        guard focused.windowID == f.windowID, focused.owningApplication?.processID == f.pid,
              focused.frame == f.bounds, focused.isOnScreen, f.title == (focused.title ?? "") else {
            throw WindowError("窗口状态已变化，请重新截图。")
        }
        let recovery = game.steam.remoteDesktopRecovery == true
        let gameActions = ["trace-click", "click", "click-window", "click-hold", "hover", "enter", "escape", "space", "tab"]
        if !recovery && (!isGame(focused.title) || !gameActions.contains(request.action)) {
            throw WindowError("当前窗口或操作与所选游戏不符，请重新核对现场。")
        }
        if request.action == "previous-window" || request.action == "window-picker" {
            guard !isGame(focused.title), f.title.hasSuffix("[Streaming]") else {
                throw WindowError("远端窗口已经变化，已取消切换。")
            }
            guard let source = CGEventSource(stateID: .hidSystemState),
                  let altDown = CGEvent(keyboardEventSource: source, virtualKey: 58, keyDown: true),
                  let tabDown = CGEvent(keyboardEventSource: source, virtualKey: 48, keyDown: true),
                  let tabUp = CGEvent(keyboardEventSource: source, virtualKey: 48, keyDown: false),
                  let altUp = CGEvent(keyboardEventSource: source, virtualKey: 58, keyDown: false)
            else { throw WindowError("无法构造窗口切换快捷键。") }
            let picker = request.action == "window-picker"
            let held: CGEventFlags = picker ? [.maskControl, .maskAlternate] : .maskAlternate
            altDown.flags = held
            tabDown.flags = held
            tabUp.flags = held
            altUp.flags = picker ? .maskControl : []
            var events = [altDown, tabDown, tabUp, altUp]
            if picker {
                guard let ctrlDown = CGEvent(keyboardEventSource: source, virtualKey: 59, keyDown: true),
                      let ctrlUp = CGEvent(keyboardEventSource: source, virtualKey: 59, keyDown: false)
                else { throw WindowError("无法构造任务切换快捷键。") }
                ctrlDown.flags = .maskControl
                ctrlUp.flags = []
                events.insert(ctrlDown, at: 0)
                events.append(ctrlUp)
            }
            for event in events {
                event.postToPid(f.pid)
                try await Task.sleep(for: .milliseconds(90))
            }
            return
        }
        if request.action == "windows-start" {
            guard isGame(focused.title) else { throw WindowError("游戏未在前台，已取消打开 Windows 开始菜单。") }
            guard let source = CGEventSource(stateID: .hidSystemState),
                  let ctrlDown = CGEvent(keyboardEventSource: source, virtualKey: 59, keyDown: true),
                  let escDown = CGEvent(keyboardEventSource: source, virtualKey: 53, keyDown: true),
                  let escUp = CGEvent(keyboardEventSource: source, virtualKey: 53, keyDown: false),
                  let ctrlUp = CGEvent(keyboardEventSource: source, virtualKey: 59, keyDown: false)
            else { throw WindowError("无法构造开始菜单快捷键。") }
            for event in [ctrlDown, escDown, escUp, ctrlUp] {
                event.flags = event === ctrlUp ? [] : .maskControl
                event.postToPid(f.pid)
                try await Task.sleep(for: .milliseconds(80))
            }
            return
        }
        let title = remoteTitle(focused.title)
        if request.action == "mouse-keys-shortcut" {
            guard isGame(title),
                  let alt = CGEvent(keyboardEventSource: nil, virtualKey: 58, keyDown: true),
                  let shift = CGEvent(keyboardEventSource: nil, virtualKey: 56, keyDown: true),
                  let endShift = CGEvent(keyboardEventSource: nil, virtualKey: 56, keyDown: false),
                  let endAlt = CGEvent(keyboardEventSource: nil, virtualKey: 58, keyDown: false)
            else { throw WindowError("目标游戏未在前台，已取消鼠标键快捷键。") }
            let both: CGEventFlags = [.maskAlternate, .maskShift]
            alt.flags = .maskAlternate
            shift.flags = both
            alt.postToPid(f.pid)
            shift.postToPid(f.pid)
            defer {
                endShift.flags = .maskAlternate
                endAlt.flags = []
                endShift.postToPid(f.pid)
                endAlt.postToPid(f.pid)
            }
            try await Task.sleep(for: .milliseconds(90))
            try await postKey(71, flags: [both, .maskNumericPad], to: f.pid)
            return
        }
        if request.action == "open-run" {
            guard isGame(title),
                  let down = CGEvent(keyboardEventSource: nil, virtualKey: 55, keyDown: true),
                  let up = CGEvent(keyboardEventSource: nil, virtualKey: 55, keyDown: false) else {
                throw WindowError("目标游戏未在前台，已取消快捷键。")
            }
            down.flags = .maskCommand
            down.postToPid(f.pid)
            defer { up.flags = []; up.postToPid(f.pid) }
            try await Task.sleep(for: .milliseconds(80))
            try await postKey(15, flags: .maskCommand, to: f.pid)
            return
        }
        if request.action == "type-mouse-settings" {
            guard ["运行", "Run"].contains(title) else { throw WindowError("未识别到 Windows 运行对话框。") }
            // The only text this action can enter is the Windows mouse accessibility settings URI.
            let letters: [Character: CGKeyCode] = ["m":46, "s":1, "-":27, "e":14, "t":17, "i":34, "n":45,
                "g":5, ":":41, "a":0, "o":31, "f":3, "c":8, "u":32]
            for character in "ms-settings:easeofaccess-mouse" {
                guard let code = letters[character] else { throw WindowError("设置地址包含未知按键。") }
                try await postKey(code, flags: character == ":" ? .maskShift : [], to: f.pid)
            }
            return
        }
        if request.action == "mouse-keys-click" {
            guard isGame(title) else { throw WindowError("游戏未在前台，已取消小键盘输入。") }
            try await postKey(75, flags: .maskNumericPad, to: f.pid)
            try await postKey(87, flags: .maskNumericPad, to: f.pid)
            return
        }
        let gameKeys: [String: CGKeyCode] = ["enter": 36, "escape": 53, "tab": 48, "space": 49]
        if let code = gameKeys[request.action] {
            let startMenu = ["搜索", "开始", "Search", "Start"].contains(title)
            let runDialog = ["运行", "Run"].contains(title)
            let mouseKeysPrompt = ["鼠标键", "Mouse Keys"].contains(title)
            let settings = ["设置", "Settings"].contains(title)
            guard isGame(focused.title) || (request.action == "escape" && startMenu) ||
                    ((runDialog || mouseKeysPrompt) && ["escape", "enter"].contains(request.action)) ||
                    (settings && ["tab", "space"].contains(request.action))
            else { throw WindowError("目标界面未在前台，已取消按键。") }
            guard let source = CGEventSource(stateID: .hidSystemState),
                  let down = CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: true),
                  let up = CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: false)
            else { throw WindowError("无法创建按键事件。") }
            down.postToPid(f.pid)
            try await Task.sleep(for: .milliseconds(90))
            up.postToPid(f.pid)
            return
        }
        guard let x = request.x, let y = request.y, (0..<f.width).contains(x), (0..<f.height).contains(y)
        else { throw WindowError("点击坐标越界。") }
        let location = CGPoint(x: f.bounds.minX + (CGFloat(x) + 0.5) * f.bounds.width / CGFloat(f.width),
                               y: f.bounds.minY + (CGFloat(y) + 0.5) * f.bounds.height / CGFloat(f.height))
        try await sendClick(at: location, pid: f.pid, windowID: f.windowID, mode: request.action, trace: trace)
    }

    func isTopWindow(at location: CGPoint, pid: pid_t, windowID: CGWindowID) -> Bool {
        guard let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID)
              as? [[String: Any]] else { return false }
        for info in windows {
            guard let bounds = info[kCGWindowBounds as String] as? NSDictionary,
                  let rect = CGRect(dictionaryRepresentation: bounds),
                  rect.contains(location), (info[kCGWindowAlpha as String] as? Double ?? 1) > 0
            else { continue }
            return (info[kCGWindowNumber as String] as? NSNumber)?.uint32Value == windowID &&
                (info[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid
        }
        return false
    }

    func sendClick(at location: CGPoint, pid: pid_t, windowID: CGWindowID, mode: String, trace: ClickTrace?) async throws {
        guard isTopWindow(at: location, pid: pid, windowID: windowID) else {
            throw WindowError("点击位置被其他窗口覆盖，已暂停。")
        }
        guard let source = CGEventSource(stateID: .hidSystemState),
              let move = CGEvent(mouseEventSource: source, mouseType: .mouseMoved, mouseCursorPosition: location, mouseButton: .left),
              let down = CGEvent(mouseEventSource: source, mouseType: .leftMouseDown, mouseCursorPosition: location, mouseButton: .left),
              let up = CGEvent(mouseEventSource: source, mouseType: .leftMouseUp, mouseCursorPosition: location, mouseButton: .left)
        else { throw WindowError("无法构造点击事件。") }
        down.setIntegerValueField(.mouseEventClickState, value: 1)
        up.setIntegerValueField(.mouseEventClickState, value: 1)
        let sequence = Int64(DispatchTime.now().uptimeNanoseconds % UInt64(Int32.max))
        for event in [down, up] {
            if let trace { event.setIntegerValueField(.eventSourceUserData, value: trace.marker) }
            event.setIntegerValueField(.mouseEventNumber, value: sequence)
            event.setIntegerValueField(.mouseEventWindowUnderMousePointer, value: Int64(windowID))
            event.setIntegerValueField(.mouseEventWindowUnderMousePointerThatCanHandleThisEvent, value: Int64(windowID))
            event.flags = []
        }
        down.setDoubleValueField(.mouseEventPressure, value: 1)
        up.setDoubleValueField(.mouseEventPressure, value: 0)
        func post(_ event: CGEvent) {
            event.timestamp = DispatchTime.now().uptimeNanoseconds
            if mode == "click-window" { event.postToPid(pid) }
            else { event.post(tap: .cghidEventTap) }
        }
        post(move)
        if mode == "hover" { return }
        try await Task.sleep(for: .milliseconds(160))
        guard isTopWindow(at: location, pid: pid, windowID: windowID) else {
            throw WindowError("移动鼠标后前台窗口已变化，已取消点击。")
        }
        post(down)
        try await Task.sleep(for: .milliseconds(mode == "click-hold" ? 650 : 100))
        post(up)
    }

    func run(in directory: URL) async throws {
        let lock = open(directory.appendingPathComponent("session.lock").path, O_CREAT | O_RDWR, 0o600)
        guard lock >= 0 else { throw WindowError("无法创建运行锁。") }
        defer { close(lock) }
        guard flock(lock, LOCK_EX | LOCK_NB) == 0 else { throw WindowError("已有一个窗口工具在运行。") }
        let files = FileManager.default
        let requestURL = directory.appendingPathComponent("request.json")
        let statusURL = directory.appendingPathComponent("status.json")
        let frameURL = directory.appendingPathComponent("frame.png")
        func report(_ message: String, frame: Frame? = nil, state: String? = nil) throws {
            var value: [String: Any] = ["message": message, "time": ISO8601DateFormatter().string(from: Date()), "game": game.name]
            if let state { value["state"] = state }
            if let f = frame {
                value["frame"] = f.id
                value["width"] = f.width
                value["height"] = f.height
                value["windowID"] = f.windowID
                value["title"] = f.title
                value["pid"] = f.pid
            }
            try JSONSerialization.data(withJSONObject: value).write(to: statusURL, options: .atomic)
            print(message)
        }
        for url in [requestURL, frameURL, statusURL] where files.fileExists(atPath: url.path) {
            try files.removeItem(at: url)
        }
        guard CGSessionCopyCurrentDictionary() != nil else {
            try report("当前进程无法访问 Mac 图形桌面。请从访达打开 Steam-Window.command。")
            return
        }
        guard CGPreflightScreenCaptureAccess() || CGRequestScreenCaptureAccess() else {
            try report("等待屏幕录制权限。请按系统提示授权，随后重新打开 Steam-Window.command。")
            return
        }
        let idleTimeout: TimeInterval = 15 * 60
        var deadline = Date().addingTimeInterval(idleTimeout)
        var frame: Frame?
        var reportedWindow: CGWindowID?
        var lastError = ""
        var checkedLaunch = false
        while Date() < deadline {
            let hasRequest = files.fileExists(atPath: requestURL.path)
            if frame == nil || hasRequest {
                do {
                    var request: Request?
                    if hasRequest {
                        let bytes = try Data(contentsOf: requestURL)
                        try files.removeItem(at: requestURL)
                        request = try JSONDecoder().decode(Request.self, from: bytes)
                    }
                    let possibleWindow = try await targetIfPresent()
                    let reconnect = request?.action == "connect"
                    if !checkedLaunch || reconnect {
                        checkedLaunch = true
                        let running = NSWorkspace.shared.runningApplications.contains { app in
                            app.bundleIdentifier == "com.valvesoftware.steam.streamingclient" ||
                                app.executableURL?.lastPathComponent == "streaming_client"
                        }
                        if possibleWindow == nil && (!running || reconnect) {
                            let launchURL = URL(string: "steam://rungameid/\(game.steam.appId)")!
                            guard NSWorkspace.shared.open(launchURL) else {
                                throw WindowError("系统未能把游戏启动请求交给 Steam。")
                            }
                            try report("已向 Steam 请求启动《\(game.name)》，等待游戏窗口。")
                            frame = nil
                            try await Task.sleep(for: .seconds(2))
                            continue
                        }
                    }
                    guard let window = possibleWindow else { throw WindowError("等待 Steam 游戏串流窗口。") }
                    if reportedWindow != window.windowID {
                        try report("已定位串流窗口 \(window.windowID)，正在截取首帧。")
                        reportedWindow = window.windowID
                    }
                    var trace: ClickTrace?
                    defer { trace?.stop() }
                    if request?.action == "trace-click", let pid = window.owningApplication?.processID {
                        guard isGame(window.title) else { throw WindowError("当前不是目标游戏，未发送测试点击。") }
                        trace = ClickTrace()
                        try trace?.start(pid: pid)
                    }
                    if let request {
                        switch request.action {
                        case "trace-click", "click", "click-window", "click-hold", "hover", "enter", "escape", "space", "tab", "previous-window", "window-picker", "windows-start", "open-run", "type-mouse-settings", "mouse-keys-click", "mouse-keys-shortcut":
                            try await input(request, frame: frame, window: window, trace: trace)
                            frame = nil
                            try await Task.sleep(for: .milliseconds(550))
                        case "capture-game", "capture", "read-labels", "connect": break
                        default: throw WindowError("不支持此窗口操作。")
                        }
                    }
                    let needGame = request?.action == "capture-game" || request?.action == "read-labels"
                    let result = try capture(window, in: directory, requireGame: needGame)
                    frame = result
                    if request?.action == "read-labels" {
                        try readLabels(from: frameURL, frame: result, to: directory.appendingPathComponent("labels.json"))
                    }
                    try report(trace?.summary() ?? "串流窗口截图已就绪。", frame: result)
                    if hasRequest { deadline = Date().addingTimeInterval(idleTimeout) }
                    lastError = ""
                } catch {
                    if lastError != error.localizedDescription || hasRequest {
                        try report(error.localizedDescription)
                        lastError = error.localizedDescription
                    }
                }
            }
            try await Task.sleep(for: .seconds(frame == nil ? 2 : 1))
        }
        try report("连续 15 分钟没有成功执行请求，桌面工具已退出。", state: "stopped")
    }

    static func main() async {
        let args = CommandLine.arguments
        guard (2...3).contains(args.count) else {
            print("请从项目根目录打开 Steam-Window.command [游戏标识]。")
            return
        }
        do {
            let directory = URL(fileURLWithPath: args[1], isDirectory: true)
            let url = args.count == 3 ? URL(fileURLWithPath: args[2]) :
                directory.deletingLastPathComponent().appendingPathComponent("games/cats/game.json")
            let config = try JSONDecoder().decode(GameSettings.self, from: Data(contentsOf: url))
            guard config.steam.appId.range(of: #"^[0-9]+$"#, options: .regularExpression) != nil,
                  !config.steam.titles.isEmpty,
                  config.steam.titles.allSatisfy({ !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }) else {
                throw WindowError("请在游戏配置中填写 Steam 编号和可识别的窗口标题。")
            }
            if args[1] == "--check-profile" { print(config.name); return }
            try await SteamWindow(game: config, profileURL: url).run(in: directory)
        } catch { FileHandle.standardError.write(Data((error.localizedDescription + "\n").utf8)); exit(1) }
    }
}
