import QtQuick
import QtQuick.Controls
import ElysiumTheme 1.0
import "."

ListView {
    id: root
    property bool darkMode: true

    clip: true
    spacing: 4
    boundsBehavior: Flickable.StopAtBounds
    ScrollBar.vertical: ScrollBar {
        implicitWidth: 6
        contentItem: Rectangle {
            radius: 3
            color: Theme.border(darkMode)
            opacity: 0.45
        }
        background: Rectangle { color: "transparent" }
    }

    model: Elysium.appsModel

    delegate: AppListRow {
        width: ListView.view.width
        darkMode: root.darkMode
        rowIndex: index
        appId: model.appId
        appName: model.name
        appDescription: model.description
        appTags: model.tags
        iconPath: model.iconPath
        statusText: model.status
        statusBg: model.statusBg
        statusFg: model.statusFg
    }
}
