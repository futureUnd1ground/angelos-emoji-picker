import QtQuick
import Quickshell
import qs.config
import qs.widgets

Column {
    id: root
    property var plugin
    width: parent ? parent.width : 400
    spacing: Theme.u * 4
    PxGroup {
        title: "Emoji Picker"
        icon: "smile"
        width: parent.width
        PxText {
            width: parent.width
            wrapMode: Text.Wrap
            text: I18n.t("Meta + . открывает поиск эмодзи на русском и английском. Enter копирует выбранный эмодзи; Ctrl + V вставляет его в приложение. Esc закрывает окно.", "Meta + . opens emoji search in Russian and English. Enter copies the selected emoji; Ctrl + V pastes it into an app. Esc closes the picker.")
        }
        SettingRow {
            label: I18n.t("Тема окна", "Window theme")
            PxSegmented {
                model: [{label: "Auto", value: "system"}, {label: "Dark", value: "dark"}, {label: "Light", value: "light"}, {label: "Rose", value: "rose"}, {label: "Обои", value: "wallpaper"}, {label: "Custom", value: "custom"}]
                currentValue: root.plugin ? root.plugin.get("theme", "system") : "system"
                onActivated: v => root.plugin.set("theme", v)
            }
        }
        Repeater {
            model: [{key: "background", label: "Фон / Background", fallback: "#1e1e2e"}, {key: "foreground", label: "Текст / Text", fallback: "#cdd6f4"}, {key: "accent", label: "Акцент / Accent", fallback: "#cba6f7"}]
            delegate: SettingRow {
                required property var modelData
                width: parent.width
                visible: root.plugin && root.plugin.get("theme", "system") === "custom"
                label: modelData.label
                PxField {
                    width: Theme.u * 40
                    text: root.plugin ? root.plugin.get(modelData.key, modelData.fallback) : modelData.fallback
                    onAccepted: {
                        if (/^#[0-9a-fA-F]{6}$/.test(text.trim())) root.plugin.set(modelData.key, text.trim());
                    }
                }
            }
        }
        SettingRow {
            label: I18n.t("Стиль эмодзи", "Emoji style")
            PxSegmented {
                model: [{label: "Auto", value: "system"}, {label: "Google", value: "google"}, {label: "Twemoji", value: "twemoji"}, {label: "Custom", value: "custom"}]
                currentValue: root.plugin ? root.plugin.get("emojiStyle", "system") : "system"
                onActivated: v => root.plugin.set("emojiStyle", v)
            }
        }
        SettingRow {
            visible: root.plugin && root.plugin.get("emojiStyle", "system") === "custom"
            label: I18n.t("Установленный шрифт эмодзи", "Installed emoji font")
            PxField {
                width: Theme.u * 55
                text: root.plugin ? root.plugin.get("emojiFont", "") : ""
                onAccepted: if (/^[\w ()-]{1,80}$/.test(text.trim())) root.plugin.set("emojiFont", text.trim())
            }
        }
        SettingRow {
            label: I18n.t("Размер текста", "Text size")
            PxSegmented {
                model: [{label: "12", value: 12}, {label: "16", value: 16}, {label: "20", value: 20}]
                currentValue: root.plugin ? root.plugin.get("fontSize", 16) : 16
                onActivated: v => root.plugin.set("fontSize", v)
            }
        }
        PxText {
            width: parent.width
            wrapMode: Text.Wrap
            dim: true
            text: I18n.t("Стиль эмодзи меняется в этом окне. После вставки внешний вид определяет приложение. Новые символы, которых нет в Twemoji, используют системный шрифт. В Custom укажи название установленного шрифта; цвета — #RRGGBB и Enter.", "Emoji style changes in this picker. After pasting, the app determines appearance. Emoji absent from Twemoji fall back to system fonts. In Custom enter an installed font family; colors use #RRGGBB and Enter.")
        }
        PxButton {
            text: I18n.t("Выбрать эмодзи", "Choose emoji")
            icon: "smile"
            onClicked: if (root.plugin) Quickshell.execDetached(["python3", root.plugin.dir + "/picker.py", "launch"])
        }
        PxText {
            width: parent.width
            wrapMode: Text.Wrap
            dim: true
            text: root.plugin ? root.plugin.get("status", "") : ""
        }
    }
}
