import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ElysiumTheme 1.0
import "pages"
import "components"

ApplicationWindow {
    id: root
    visible: true
    title: "Elysium"
    width: Elysium.initialWidth
    height: Elysium.initialHeight
    x: Elysium.initialX >= 0 ? Elysium.initialX : Screen.width / 2 - width / 2
    y: Elysium.initialY >= 0 ? Elysium.initialY : Screen.height / 2 - height / 2
    minimumWidth: bubbleMode ? Theme.bubbleSize : 720
    minimumHeight: bubbleMode ? Theme.bubbleSize : 560
    color: Theme.bgTop(Elysium.darkMode)

    property bool darkMode: Elysium.darkMode
    property bool bubbleMode: false
    property bool bubbleRestoring: false
    property var homePageRef: null
    property var savedGeometry: null

    readonly property int normalMinWidth: 720
    readonly property int normalMinHeight: 560

    function enterBubble() {
        if (bubbleMode || bubbleRestoring)
            return
        savedGeometry = { x: x, y: y, width: width, height: height }
        bubbleMode = true
        Elysium.enterBubbleMode(root)

        bubbleAnimX.to = Screen.width - Theme.bubbleSize - 24
        bubbleAnimY.to = Screen.height - Theme.bubbleSize - 80
        bubbleAnimW.to = Theme.bubbleSize
        bubbleAnimH.to = Theme.bubbleSize
        bubbleShrink.start()
    }

    function exitBubble() {
        if (!bubbleMode || bubbleRestoring)
            return
        bubbleRestoring = true
        if (savedGeometry) {
            restoreAnimX.to = savedGeometry.x
            restoreAnimY.to = savedGeometry.y
            restoreAnimW.to = savedGeometry.width
            restoreAnimH.to = savedGeometry.height
            restoreExpand.start()
        } else {
            finishBubbleRestore()
        }
    }

    function finishBubbleRestore() {
        minimumWidth = normalMinWidth
        minimumHeight = normalMinHeight
        bubbleMode = false
        bubbleRestoring = false
        Elysium.exitBubbleMode(root)
    }

    ParallelAnimation {
        id: bubbleShrink
        NumberAnimation { id: bubbleAnimX; target: root; property: "x"; duration: Theme.animNormal; easing.type: Easing.OutCubic }
        NumberAnimation { id: bubbleAnimY; target: root; property: "y"; duration: Theme.animNormal; easing.type: Easing.OutCubic }
        NumberAnimation { id: bubbleAnimW; target: root; property: "width"; duration: Theme.animNormal; easing.type: Easing.OutCubic }
        NumberAnimation { id: bubbleAnimH; target: root; property: "height"; duration: Theme.animNormal; easing.type: Easing.OutCubic }
    }

    ParallelAnimation {
        id: restoreExpand
        NumberAnimation { id: restoreAnimX; target: root; property: "x"; duration: Theme.animNormal; easing.type: Easing.OutCubic }
        NumberAnimation { id: restoreAnimY; target: root; property: "y"; duration: Theme.animNormal; easing.type: Easing.OutCubic }
        NumberAnimation { id: restoreAnimW; target: root; property: "width"; duration: Theme.animNormal; easing.type: Easing.OutCubic }
        NumberAnimation { id: restoreAnimH; target: root; property: "height"; duration: Theme.animNormal; easing.type: Easing.OutCubic }
        onFinished: finishBubbleRestore()
    }

    onClosing: {
        if (!bubbleMode)
            Elysium.saveWindowGeometry(x, y, width, height)
    }

    Component.onCompleted: {
        Elysium.applyTitleBar(root)
        Elysium.startInit()
    }

    Connections {
        target: Elysium
        function onDarkModeChanged() {
            root.darkMode = Elysium.darkMode
            if (!root.bubbleMode)
                Elysium.applyTitleBar(root)
        }
        function onToastRequested(message, level) {
            if (!root.bubbleMode)
                toast.show(message, level)
        }
        function onErrorOccurred(title, message) {
            errorDialog.openWith(title, message)
        }
        function onBubbleMinimizeRequested() {
            root.enterBubble()
        }
    }

    Shortcut {
        sequence: "Ctrl+F"
        enabled: !bubbleMode && !Elysium.isLoading && homePageRef
        onActivated: if (homePageRef) homePageRef.focusSearch()
    }
    Shortcut {
        sequence: "Ctrl+,"
        enabled: !bubbleMode
        onActivated: Elysium.openSettings()
    }
    Shortcut {
        sequence: "F5"
        enabled: !bubbleMode
        onActivated: Elysium.refreshStatuses()
    }
    Shortcut {
        sequence: "Escape"
        onActivated: {
            if (root.bubbleMode)
                root.exitBubble()
            else if (Elysium.settingsDrawerOpen)
                Elysium.closeSettings()
        }
    }

    AmbientBackground {
        anchors.fill: parent
        darkMode: root.darkMode
        visible: !root.bubbleMode
        z: -1
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0
        visible: !bubbleMode && !Elysium.isLoading
        opacity: visible ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: Theme.animNormal } }

        SidebarRail {
            Layout.fillHeight: true
            darkMode: root.darkMode
        }

        HomePage {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 16
            Component.onCompleted: root.homePageRef = this
        }
    }

    LoadingPage {
        anchors.fill: parent
        visible: !bubbleMode && Elysium.isLoading
        opacity: visible ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: Theme.animNormal } }
    }

    SettingsDrawer {
        anchors.fill: parent
        darkMode: root.darkMode
        visible: !bubbleMode
    }

    BubbleShell {
        anchors.fill: parent
        visible: bubbleMode
        enabled: bubbleMode
        restoring: root.bubbleRestoring
        window: root
        darkMode: root.darkMode
        z: 500
        onRestoreRequested: root.exitBubble()
    }

    Toast {
        id: toast
        darkMode: root.darkMode
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        visible: !bubbleMode
        z: 200
    }

    ThemedDialog {
        id: errorDialog
        darkMode: root.darkMode
        z: 300
    }
}
