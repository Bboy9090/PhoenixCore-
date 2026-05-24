// Phoenix OS — SDDM Login Theme
// File: branding/sddm-theme/Main.qml
//
// KDE/Qt QML-based SDDM login screen theme.
// Design: Dark Forge Black background with Phoenix fire gradient,
//         centered login panel with Phoenix branding.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import SddmComponents 2.0

Rectangle {
    id: root
    width:  Screen.width
    height: Screen.height

    // ---- Phoenix color palette ----
    readonly property color colorForgeBlack:   "#0D0F12"
    readonly property color colorEmberDark:    "#161A1F"
    readonly property color colorAshGrey:      "#1E2329"
    readonly property color colorGraphite:     "#2A2F38"
    readonly property color colorBoneWhite:    "#E8EAF0"
    readonly property color colorSlate:        "#8A929E"
    readonly property color colorAmber:        "#F58C1F"
    readonly property color colorFlame:        "#D94215"

    // ---- Background ----
    color: colorForgeBlack

    // Fire gradient overlay — subtle, bottom-left glow
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Diagonal
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 0.7; color: Qt.rgba(0.102, 0.063, 0.020, 0.4) }
            GradientStop { position: 1.0; color: Qt.rgba(0.961, 0.549, 0.122, 0.08) }
        }
    }

    // ---- Hostname / session info (top-left) ----
    Text {
        anchors.top:   parent.top
        anchors.left:  parent.left
        anchors.margins: 32
        text:  config.ServerURL !== "" ? config.ServerURL : sddm.hostName
        color: root.colorSlate
        font.family: "IBM Plex Mono"
        font.pixelSize: 13
        opacity: 0.7
    }

    // ---- Time display (top-right) ----
    Clock {
        anchors.top:   parent.top
        anchors.right: parent.right
        anchors.margins: 32
        color: root.colorSlate
        fontSize: 13
    }

    // ---- Center login panel ----
    Item {
        anchors.centerIn: parent
        width:  380
        height: loginColumn.implicitHeight + 80

        // Panel background
        Rectangle {
            anchors.fill: parent
            color: root.colorEmberDark
            border.color: root.colorGraphite
            border.width: 1
            radius: 8
        }

        ColumnLayout {
            id: loginColumn
            anchors {
                top:     parent.top
                left:    parent.left
                right:   parent.right
                margins: 40
                topMargin: 40
            }
            spacing: 20

            // Phoenix OS logo wordmark
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "PHOENIX OS"
                color: root.colorAmber
                font.family:      "Rajdhani"
                font.pixelSize:   28
                font.weight:      Font.SemiBold
                font.letterSpacing: 4
            }

            // Hostname
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: sddm.hostName
                color: root.colorSlate
                font.family:  "IBM Plex Mono"
                font.pixelSize: 12
                topPadding: -12
            }

            // Separator
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: root.colorGraphite
            }

            // Username field
            Column {
                Layout.fillWidth: true
                spacing: 6

                Text {
                    text: "Username"
                    color: root.colorSlate
                    font.pixelSize: 12
                    font.family: "IBM Plex Mono"
                }

                TextField {
                    id: usernameField
                    width: parent.width
                    placeholderText: "Enter username"
                    text: userModel.lastUser
                    focus: true
                    KeyNavigation.tab: passwordField

                    background: Rectangle {
                        color: root.colorAshGrey
                        border.color: usernameField.activeFocus ? root.colorAmber : root.colorGraphite
                        border.width: 1
                        radius: 4
                    }
                    color: root.colorBoneWhite
                    font.family: "IBM Plex Mono"
                    font.pixelSize: 14
                    leftPadding: 12
                    rightPadding: 12
                    topPadding: 10
                    bottomPadding: 10

                    Keys.onReturnPressed: passwordField.forceActiveFocus()
                }
            }

            // Password field
            Column {
                Layout.fillWidth: true
                spacing: 6

                Text {
                    text: "Password"
                    color: root.colorSlate
                    font.pixelSize: 12
                    font.family: "IBM Plex Mono"
                }

                TextField {
                    id: passwordField
                    width: parent.width
                    placeholderText: "Enter password"
                    echoMode: TextInput.Password
                    KeyNavigation.tab: loginButton

                    background: Rectangle {
                        color: root.colorAshGrey
                        border.color: passwordField.activeFocus ? root.colorAmber : root.colorGraphite
                        border.width: 1
                        radius: 4
                    }
                    color: root.colorBoneWhite
                    font.family: "IBM Plex Mono"
                    font.pixelSize: 14
                    leftPadding: 12
                    rightPadding: 12
                    topPadding: 10
                    bottomPadding: 10

                    Keys.onReturnPressed: loginButton.clicked()
                }
            }

            // Error message
            Text {
                id: errorMessage
                Layout.fillWidth: true
                text: ""
                color: "#E03A3A"
                font.pixelSize: 12
                font.family: "IBM Plex Mono"
                wrapMode: Text.WordWrap
                visible: text !== ""
            }

            // Login button
            Button {
                id: loginButton
                Layout.fillWidth: true
                text: "Sign In"

                background: Rectangle {
                    color: loginButton.pressed ? root.colorFlame :
                           loginButton.hovered ? root.colorAmber :
                           Qt.darker(root.colorAmber, 1.2)
                    radius: 4

                    Behavior on color {
                        ColorAnimation { duration: 120 }
                    }
                }

                contentItem: Text {
                    text: parent.text
                    color: root.colorForgeBlack
                    font.family: "Rajdhani"
                    font.pixelSize: 15
                    font.weight: Font.SemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                topPadding: 12
                bottomPadding: 12

                onClicked: {
                    errorMessage.text = ""
                    sddm.login(usernameField.text, passwordField.text, sessionModel.currentIndex)
                }
            }

            // Session selector (compact)
            ComboBox {
                id: sessionCombo
                Layout.fillWidth: true
                model: sessionModel
                currentIndex: sessionModel.lastIndex
                textRole: "name"

                background: Rectangle {
                    color: root.colorAshGrey
                    border.color: root.colorGraphite
                    radius: 4
                }

                contentItem: Text {
                    leftPadding: 12
                    text: sessionCombo.displayText
                    color: root.colorSlate
                    font.family: "IBM Plex Mono"
                    font.pixelSize: 12
                    verticalAlignment: Text.AlignVCenter
                }
            }

            // Bottom padding
            Item { height: 4 }
        }
    }

    // ---- Bottom bar: power controls ----
    RowLayout {
        anchors.bottom:  parent.bottom
        anchors.right:   parent.right
        anchors.margins: 32
        spacing: 20

        Text {
            text: "Restart"
            color: root.colorSlate
            font.pixelSize: 13
            font.family: "IBM Plex Mono"
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: sddm.reboot()
            }
        }

        Text {
            text: "Power Off"
            color: root.colorSlate
            font.pixelSize: 13
            font.family: "IBM Plex Mono"
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: sddm.powerOff()
            }
        }
    }

    // ---- SDDM signal handlers ----
    Connections {
        target: sddm

        function onLoginFailed() {
            passwordField.text = ""
            errorMessage.text = "Login failed. Check username and password."
            passwordField.forceActiveFocus()
        }

        function onLoginSucceeded() {
            errorMessage.text = ""
        }
    }
}
