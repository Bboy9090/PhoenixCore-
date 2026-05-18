import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import SddmComponents 2.0

Rectangle {
    id: root
    width: Screen.width
    height: Screen.height

    readonly property string editionName: "__EDITION_NAME__"
    readonly property string editionTagline: "__EDITION_TAGLINE__"

    readonly property color colorPrimary: "__COLOR_PRIMARY__"
    readonly property color colorSecondary: "__COLOR_SECONDARY__"
    readonly property color colorBackground: "__COLOR_BACKGROUND__"
    readonly property color colorSurface: "__COLOR_SURFACE__"
    readonly property color colorText: "__COLOR_TEXT__"
    readonly property color colorMuted: Qt.darker(colorText, 1.65)
    readonly property color colorField: Qt.darker(colorSurface, 1.16)

    color: colorBackground

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Diagonal
            GradientStop { position: 0.0; color: Qt.rgba(0, 0, 0, 0.0) }
            GradientStop { position: 0.65; color: Qt.rgba(colorSecondary.r, colorSecondary.g, colorSecondary.b, 0.10) }
            GradientStop { position: 1.0; color: Qt.rgba(colorPrimary.r, colorPrimary.g, colorPrimary.b, 0.22) }
        }
    }

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        anchors.topMargin: 24

        Text {
            text: sddm.hostName
            color: root.colorMuted
            font.pixelSize: 12
            font.family: "IBM Plex Mono"
        }

        Item { Layout.fillWidth: true }

        Clock {
            color: root.colorMuted
            fontSize: 12
        }
    }

    Item {
        id: loginPanel
        anchors.centerIn: parent
        width: 430
        height: loginColumn.implicitHeight + 56

        Rectangle {
            anchors.fill: parent
            color: Qt.rgba(root.colorSurface.r, root.colorSurface.g, root.colorSurface.b, 0.92)
            radius: 10
            border.width: 1
            border.color: Qt.rgba(root.colorPrimary.r, root.colorPrimary.g, root.colorPrimary.b, 0.42)
        }

        ColumnLayout {
            id: loginColumn
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.leftMargin: 36
            anchors.rightMargin: 36
            anchors.topMargin: 28
            spacing: 14

            Image {
                id: editionLogo
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 168
                Layout.preferredHeight: 96
                fillMode: Image.PreserveAspectFit
                source: "logo.svg"
                smooth: true
                mipmap: true
                onStatusChanged: {
                    if (status === Image.Error && source !== "logo.png") {
                        source = "logo.png"
                    }
                }
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: root.editionName
                color: root.colorPrimary
                font.family: "Rajdhani"
                font.pixelSize: 24
                font.weight: Font.DemiBold
                font.letterSpacing: 1.4
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: root.editionTagline
                color: root.colorMuted
                font.family: "IBM Plex Mono"
                font.pixelSize: 11
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Qt.rgba(root.colorSecondary.r, root.colorSecondary.g, root.colorSecondary.b, 0.28)
            }

            Text {
                text: "Username"
                color: root.colorMuted
                font.pixelSize: 12
                font.family: "IBM Plex Mono"
            }

            TextField {
                id: usernameField
                Layout.fillWidth: true
                text: userModel.lastUser
                placeholderText: "Enter username"
                focus: true
                KeyNavigation.tab: passwordField
                selectByMouse: true
                color: root.colorText
                font.family: "IBM Plex Mono"
                font.pixelSize: 14
                leftPadding: 12
                rightPadding: 12
                topPadding: 10
                bottomPadding: 10
                background: Rectangle {
                    color: root.colorField
                    radius: 5
                    border.width: 1
                    border.color: usernameField.activeFocus
                                  ? root.colorPrimary
                                  : Qt.rgba(root.colorSecondary.r, root.colorSecondary.g, root.colorSecondary.b, 0.36)
                }
                Keys.onReturnPressed: passwordField.forceActiveFocus()
            }

            Text {
                text: "Password"
                color: root.colorMuted
                font.pixelSize: 12
                font.family: "IBM Plex Mono"
            }

            TextField {
                id: passwordField
                Layout.fillWidth: true
                placeholderText: "Enter password"
                echoMode: TextInput.Password
                KeyNavigation.tab: sessionCombo
                selectByMouse: true
                color: root.colorText
                font.family: "IBM Plex Mono"
                font.pixelSize: 14
                leftPadding: 12
                rightPadding: 12
                topPadding: 10
                bottomPadding: 10
                background: Rectangle {
                    color: root.colorField
                    radius: 5
                    border.width: 1
                    border.color: passwordField.activeFocus
                                  ? root.colorPrimary
                                  : Qt.rgba(root.colorSecondary.r, root.colorSecondary.g, root.colorSecondary.b, 0.36)
                }
                Keys.onReturnPressed: loginButton.clicked()
            }

            ComboBox {
                id: sessionCombo
                Layout.fillWidth: true
                model: sessionModel
                currentIndex: sessionModel.lastIndex
                textRole: "name"
                font.family: "IBM Plex Mono"
                font.pixelSize: 12
                background: Rectangle {
                    color: root.colorField
                    radius: 5
                    border.width: 1
                    border.color: Qt.rgba(root.colorSecondary.r, root.colorSecondary.g, root.colorSecondary.b, 0.36)
                }
                contentItem: Text {
                    text: sessionCombo.displayText
                    color: root.colorMuted
                    leftPadding: 10
                    verticalAlignment: Text.AlignVCenter
                    font.family: "IBM Plex Mono"
                    font.pixelSize: 12
                }
            }

            Text {
                id: errorMessage
                Layout.fillWidth: true
                text: ""
                color: "#FF6B6B"
                font.family: "IBM Plex Mono"
                font.pixelSize: 11
                wrapMode: Text.WordWrap
                visible: text !== ""
            }

            Button {
                id: loginButton
                Layout.fillWidth: true
                text: "Sign In"
                KeyNavigation.tab: usernameField
                topPadding: 11
                bottomPadding: 11

                background: Rectangle {
                    radius: 5
                    color: loginButton.pressed
                           ? Qt.darker(root.colorPrimary, 1.20)
                           : loginButton.hovered
                             ? Qt.lighter(root.colorPrimary, 1.08)
                             : root.colorPrimary
                    Behavior on color {
                        ColorAnimation { duration: 120 }
                    }
                }

                contentItem: Text {
                    text: parent.text
                    color: Qt.darker(root.colorBackground, 1.6)
                    font.family: "Rajdhani"
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                onClicked: {
                    errorMessage.text = ""
                    sddm.login(usernameField.text, passwordField.text, sessionCombo.currentIndex)
                }
            }

            Item { height: 2 }
        }
    }

    RowLayout {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: 30
        anchors.bottomMargin: 20
        spacing: 18

        Text {
            text: "Restart"
            color: root.colorMuted
            font.pixelSize: 12
            font.family: "IBM Plex Mono"
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: sddm.reboot()
            }
        }

        Text {
            text: "Power Off"
            color: root.colorMuted
            font.pixelSize: 12
            font.family: "IBM Plex Mono"
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: sddm.powerOff()
            }
        }
    }

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
