from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt #, QCoreApplication, QObject
from PyQt6.QtGui import QIcon, QTextDocument, QTextCursor #, QGuiApplication

import os
import sys

from core.utils import SettingsManager

settings_manager = SettingsManager()

class SearchDialog(QDialog):
    _instance = None

    def __init__(self, settings_manager, parent, state='collapsed'):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setGeometry(100, 100, 422, 400)

        self.settings_manager = settings_manager
        self.state = state

        self.initialized = True

        self.setStyleSheet("""
            QDialog {
                border-top: none;
                border-left: 1px solid rgba(125 , 125 , 125, 0.5);
                border-right: 1px solid rgba(125 , 125 , 125, 0.5);
                border-bottom: 1px solid rgba(125 , 125 , 125, 0.5);
                padding: 0px;
                margin: 0px;
            }
        """)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Create widgets once
        self.toggle_replace = QPushButton()
        self.toggle_replace.setStyleSheet(
            "border-left: 3px solid rgba(125, 125, 125, 0.5); border-top: none; "
            "border-right: 1px solid rgba(125, 125, 125, 0.5); border-bottom: none; "
            "padding: 0px; margin: 0px;"
        )
        self.toggle_replace.setProperty("tooltip", "Toggle replace")

        self.toggle_replace.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.toggle_replace.clicked.connect(lambda: self.toggle_state('expanded' if self.state == 'collapsed' else 'collapsed'))

        self.search_field = QLineEdit(self)
        self.search_field.setPlaceholderText("Search...")
        self.search_field.setStyleSheet(
            "border: 1px solid rgba(125, 125, 125, 0.5);"
            "padding: 0px; margin: 0px; height: 22px;"
            )
        self.search_field.setProperty("tooltip", "Find")
        self.search_field.setFixedSize(200, 22)
        self.search_field.textChanged.connect(self.on_search_field_changed)

        self.results_label = QLabel("No results")
        self.results_label.setFixedWidth(78)
        self.results_label.setStyleSheet("color: rgba(125, 125, 125, 1); margin-left: 5px;")

        self.up_button = QPushButton()
        self.up_button.setFixedSize(26, 26)
        self.up_button.setStyleSheet("border: 1px solid rgba(125, 125, 125, 0.5); padding: 0px; margin-top: 2px;")
        self.up_button.setProperty("tooltip", "Previous match (Shift+F3)")
        self.up_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.up_button.setEnabled(False)  # Disable by default
        self.up_button.clicked.connect(self.on_up_button_clicked)

        self.down_button = QPushButton()
        self.down_button.setFixedSize(26, 26)
        self.down_button.setStyleSheet("border: 1px solid rgba(125, 125, 125, 0.5); padding: 0px; margin-top: 2px;")
        self.down_button.setProperty("tooltip", "Next match (F3)")
        self.down_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.down_button.setEnabled(False)  # Disable by default
        self.down_button.clicked.connect(self.on_down_button_clicked)

        self.match_case_button = QPushButton()
        self.match_case_button.setFixedSize(28, 26)
        self.match_case_button.setStyleSheet("border: 1px solid rgba(125, 125, 125, 0.5); padding: 0px; margin-left: 4px; margin-top: 2px;")
        self.match_case_button.setProperty("tooltip", "Match case")
        self.match_case_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.match_case_button.setCheckable(True)
        self.match_case_button.clicked.connect(self.toggle_match_case)

        self.close_button = QPushButton()
        self.close_button.setFixedSize(28, 26)
        self.close_button.setStyleSheet("border: 1px solid rgba(125, 125, 125, 0.5); padding: 0px; margin-left: 4px; margin-top: 2px;")
        self.close_button.setProperty("tooltip", "Close (Esc)")
        self.close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_button.clicked.connect(self.close)

        self.replace_button = QPushButton()
        self.replace_button.setFixedSize(28, 26)
        self.replace_button.setStyleSheet("border: 1px solid rgba(125, 125, 125, 0.5); padding: 0px; margin-left: 4px; margin-top: 2px;")
        self.replace_button.setProperty("tooltip", "Replace")
        self.replace_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.replace_button.setEnabled(False)  # Disable by default
        self.replace_button.clicked.connect(self.on_replace_button_clicked)

        self.replace_all_button = QPushButton()
        self.replace_all_button.setFixedSize(28, 26)
        self.replace_all_button.setStyleSheet("border: 1px solid rgba(125, 125, 125, 0.5); padding: 0px; margin-left: 4px; margin-top: 2px;")
        self.replace_all_button.setProperty("tooltip", "Replace all")
        self.replace_all_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.replace_all_button.setEnabled(False)  # Disable by default
        self.replace_all_button.clicked.connect(self.on_replace_all_button_clicked)

        self.update_icons()

        self.replace_field = QLineEdit(self)
        self.replace_field.setPlaceholderText("Replace...")
        self.replace_field.setStyleSheet(
            "border: 1px solid rgba(125, 125, 125, 0.5);"
            "padding: 0px; margin: 0px; height: 22px;"
        )
        self.replace_field.setProperty("tooltip", "Replace")
        self.replace_field.setFixedSize(200, 22)

        self.current_index = -1  # Initialize current_index
        self.results = []  # Initialize results

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.horizontal_layout = QHBoxLayout()
        self.horizontal_layout.setContentsMargins(0, 0, 0, 0)
        self.horizontal_layout.setSpacing(4)
        self.horizontal_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.horizontal_layout.addWidget(self.toggle_replace)

        self.fields_layout = QVBoxLayout()
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        self.fields_layout.setSpacing(0)
        self.fields_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # --- Search Layout ---
        self.search_layout = QHBoxLayout()
        self.search_layout.setContentsMargins(0, 0, 0, 1) # Keep vertical margins/spacing
        self.search_layout.setSpacing(0)
        self.search_layout.addWidget(self.search_field)
        self.search_layout.addWidget(self.results_label)
        self.search_layout.addWidget(self.up_button)
        self.search_layout.addWidget(self.down_button)
        self.search_layout.addWidget(self.match_case_button)
        self.search_layout.addWidget(self.close_button)
        self.search_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # --- Replace Layout ---
        self.replace_layout = QHBoxLayout()
        self.replace_layout.setContentsMargins(0, 0, 0, 0) # Keep vertical margins/spacing
        self.replace_layout.setSpacing(0)
        self.replace_layout.addWidget(self.replace_field)
        self.replace_layout.addWidget(self.replace_button)
        self.replace_layout.addWidget(self.replace_all_button)
        self.replace_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # --- Add layouts to parent layouts ---
        self.fields_layout.addLayout(self.search_layout)
        self.fields_layout.addLayout(self.replace_layout) # Add replace layout permanently
        self.horizontal_layout.addLayout(self.fields_layout)
        self.main_layout.addLayout(self.horizontal_layout)
        self.setLayout(self.main_layout)
        # --- End of layout building ---

        self.initialized = True

        # Set the initial state based on the passed argument
        self.toggle_state(state, initialize=True) # Pass the initial state and a flag




    def toggle_state(self, new_state, initialize=False): # Add initialize flag
        # Only proceed if state changes or if it's the initial call
        if self.state != new_state or initialize:
            self.state = new_state

            if self.state == 'collapsed':
                # Hide replace widgets
                self.replace_field.hide()
                self.replace_button.hide()
                self.replace_all_button.hide()

                # Set fixed heights for collapsed state
                self.setFixedHeight(33)
                self.toggle_replace.setFixedSize(24, 32)

            elif self.state == 'expanded':
                # Show replace widgets BEFORE setting height
                self.replace_field.show()
                self.replace_button.show()
                self.replace_all_button.show()

                # Set fixed heights for expanded state
                self.setFixedHeight(60)
                self.toggle_replace.setFixedSize(24, 58)

            # Update icons based on the new state
            self.update_icons()

            # Optional: Force layout update if still flickering. Usually not needed
            # when only visibility changes within existing layouts.
            # self.layout().activate()
            # self.adjustSize() # Might not be needed with setFixedHeight


    def iconpath(self, icon):
        theme = self.settings_manager.get('SETTINGS/Theme')

        # print(f"theme {theme.lower()}")
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            res_folder = os.path.join(base_dir, '_internal', 'ui', 'res')
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            res_folder = os.path.join(base_dir, 'ui', 'res')

        icon_folder = os.path.join(res_folder, theme.lower())

        return os.path.join(icon_folder, icon)
    
    def update_icons(self):

        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
            res_folder = os.path.join(base_dir, '_internal', 'ui', 'res')
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            res_folder = os.path.join(base_dir, 'ui', 'res')

        # Update toggle_replace icon
        toggle_icon_path = self.iconpath('down.ico') if self.state == 'expanded' else self.iconpath('right.ico')


        self.toggle_replace.setIcon(QIcon(toggle_icon_path))

        # Update up and down button icons

        self.up_button.setIcon(QIcon(self.iconpath('arrow_up.ico')))
        self.down_button.setIcon(QIcon(self.iconpath('arrow_down.ico')))
        self.close_button.setIcon(QIcon(self.iconpath('close.ico')))
        self.match_case_button.setIcon(QIcon(self.iconpath('case.ico')))
        self.replace_button.setIcon(QIcon(self.iconpath('swap.ico')))
        self.replace_all_button.setIcon(QIcon(self.iconpath('swap_all.ico')))

    def showEvent(self, event):
        super().showEvent(event)
        editor = self.parent().tts_editor
        editor_rect = editor.geometry()
        toolbar_height = self.parent().toolbar.height()
        self.move(editor_rect.right() - self.width() - 30, editor_rect.top() + toolbar_height + 1)
        self.parent().resizeEvent = self.updatePosition


    def updatePosition(self, event):
        super().resizeEvent(event)
        editor_rect = self.parent().tts_editor.geometry()
        toolbar_height = self.parent().toolbar.height()
        self.move(editor_rect.right() - self.width() - 30, editor_rect.top() + toolbar_height + 1)


    def on_search_field_changed(self):
        current_text = self.search_field.text()
        editor = self.parent().tts_editor
        cursor = editor.textCursor()

        # Reset search results
        self.results = []
        self.current_index = -1

        flags = QTextDocument.FindFlag.FindCaseSensitively if self.match_case_button.isChecked() else QTextDocument.FindFlag(0)

        # Start search from beginning
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        editor.setTextCursor(cursor)

        # Find all matches
        while editor.find(current_text, flags):
            cur = editor.textCursor()  # Get the updated cursor after find
            self.results.append((cur.selectionStart(), cur.selectionEnd()))

        # Update UI based on results
        if self.results:
            self.current_index = 0
            self.move_to_result(0)
            self.results_label.setText(f"1 of {len(self.results)}")
            self.up_button.setEnabled(True)
            self.down_button.setEnabled(True)
            self.replace_button.setEnabled(True)
            self.replace_all_button.setEnabled(True)
            self.results_label.setStyleSheet("color: rgba(125, 125, 125, 1); margin-left: 5px;")  # Reset to gray
        else:
            self.results_label.setText("No results")
            if current_text:
                self.results_label.setStyleSheet("color: rgba(198, 118, 118, 1); margin-left: 5px;")  # Reddish color
            else:
                self.results_label.setStyleSheet("color: rgba(125, 125, 125, 1); margin-left: 5px;")  # Reset to gray
            self.up_button.setEnabled(False)
            self.down_button.setEnabled(False)
            self.replace_button.setEnabled(False)
            self.replace_all_button.setEnabled(False)



    def on_down_button_clicked(self):
        if not self.results:
            return
        
        # Cycle forward through matches
        self.current_index = (self.current_index + 1) % len(self.results)
        self.move_to_result(self.current_index)

    def on_up_button_clicked(self):
        if not self.results:
            return
        
        # Cycle backward through matches
        self.current_index = (self.current_index - 1) % len(self.results)
        self.move_to_result(self.current_index)

    def move_to_result(self, index):
        editor = self.parent().tts_editor
        cursor = editor.textCursor()
        start, end = self.results[index]
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        self.results_label.setText(f"{index + 1} of {len(self.results)}")    


    def on_replace_button_clicked(self):
        current_text = self.search_field.text()
        replace_text = self.replace_field.text()
        editor = self.parent().tts_editor
        cursor = editor.textCursor()

        # Check if there is a current selection matching the search text
        if cursor.hasSelection() and cursor.selectedText() == current_text:
            cursor.insertText(replace_text)  # Replace the selected text
            self.on_search_field_changed()  # Refresh the search results


    def on_replace_all_button_clicked(self):
        current_text = self.search_field.text()
        replace_text = self.replace_field.text()
        editor = self.parent().tts_editor
        cursor = editor.textCursor()

        # Start from the beginning of the document
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        editor.setTextCursor(cursor)

        flags = QTextDocument.FindFlag.FindCaseSensitively if self.match_case_button.isChecked() else QTextDocument.FindFlag(0)

        replaced_count = 0
        while editor.find(current_text, flags):
            # Replace found occurrence
            cursor = editor.textCursor()
            cursor.insertText(replace_text)
            replaced_count += 1

        # Update label with the number of replacements made
        self.results_label.setText(f"{replaced_count} occurrences replaced")
        self.on_search_field_changed()  # Refresh the search results


    def toggle_match_case(self):
        self.match_case = self.match_case_button.isChecked()
        self.on_search_field_changed()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F3 and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:  # Shift+F3 first
            if not hasattr(self, 'search_dialog_instance'):
                self.search_dialog_instance = show_search_dialog(self, 'collapsed')
            if hasattr(self, 'search_dialog_instance') and self.search_dialog_instance.isVisible():
                self.search_dialog_instance.on_up_button_clicked()
        elif event.key() == Qt.Key.Key_F3:  # Regular F3
            if not hasattr(self, 'search_dialog_instance'):
                self.search_dialog_instance = show_search_dialog(self, 'collapsed')
            visible = self.search_dialog_instance.isVisible()
            if hasattr(self, 'search_dialog_instance') and self.search_dialog_instance.isVisible():
                self.search_dialog_instance.on_down_button_clicked()
            else:
                show_search_dialog(self, 'collapsed')
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.set_focus_in_tts_editor()
        super().closeEvent(event)

    def set_focus_in_tts_editor(self):
        editor = self.parent().tts_editor
        editor.setFocus()




def show_search_dialog(main_window, state, selection=None):
    global search_dialog_instance
    if 'search_dialog_instance' not in globals():
        search_dialog_instance = SearchDialog(settings_manager, main_window, state)
    dialog = search_dialog_instance

    if dialog.isVisible():
        if selection:
            dialog.search_field.setText(selection)
        if dialog.state != state:
            dialog.toggle_state(state)
        else:
            dialog.hide()
    else:
        dialog.toggle_state(state)
        if selection:
            dialog.search_field.setText(selection)
        dialog.show()
        dialog.search_field.setFocus() 

    return search_dialog_instance
