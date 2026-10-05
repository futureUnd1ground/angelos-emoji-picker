import QtQuick
import Quickshell
import Quickshell.Io
import qs.services

Item {
    id: root
    property var plugin
    property bool started: false
    readonly property bool wallpaperOn: plugin && plugin.get("theme", "system") === "wallpaper"
    function refreshWallpaper() {
        if (wallpaperOn && PaletteGenerator.wallpaper) PaletteGenerator.generateFrom(PaletteGenerator.wallpaper, false);
    }
    onWallpaperOnChanged: Qt.callLater(refreshWallpaper)
    Connections {
        target: PaletteGenerator
        function onWallpaperChanged() { if (root.wallpaperOn) wallpaperTimer.restart(); }
    }
    Timer { id: wallpaperTimer; interval: 900; onTriggered: root.refreshWallpaper() }
    readonly property string token: Date.now().toString() + "-" + Math.random().toString(36).slice(2)
    readonly property string helper: (Quickshell.env("XDG_DATA_HOME") || Quickshell.env("HOME") + "/.local/share") + "/angelos-emoji-picker/picker.py"
    function start() {
        if (!plugin || started) return;
        started = true;
        binding.command = ["python3", plugin.dir + "/picker.py", "enable", token];
        binding.running = true;
    }
    onPluginChanged: Qt.callLater(start)
    Component.onCompleted: Qt.callLater(start)
    Component.onDestruction: {
        if (started) Quickshell.execDetached(["python3", helper, "disable", token]);
    }
    Process {
        id: binding
        stdout: StdioCollector { id: output }
        stderr: StdioCollector { id: error }
        onExited: code => {
            if (root.plugin) root.plugin.set("status", code === 0 ? output.text.trim() : error.text.trim());
        }
    }
}
