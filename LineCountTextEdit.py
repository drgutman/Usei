from PyQt6.QtCore import Qt, QEvent, pyqtSignal # , QSize
from PyQt6.QtWidgets import QTextEdit #, QWidget, QLabel
from PyQt6.QtGui import QTextOption
from PyQt6.QtGui import QColor, QPainter, QFontMetrics, QFont, QTextCursor, QTextCharFormat, QPalette

from signals import global_signals
from utils import settings_manager

class LineCountTextEdit(QTextEdit):
    lineCount = 0
    textModified = pyqtSignal()

    def __init__(self, tts_editor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptRichText(False)
        
        self.tts_editor = tts_editor


        is_wrapped = settings_manager.get("EDITOR/Wrapped") == "true"

        if is_wrapped:
            self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        else:
            self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
            self.setWordWrapMode(QTextOption.WrapMode.NoWrap)

        self.textChanged.connect(self.updateLineNumbers)
        self.textChanged.connect(self.onTextModified)
        self.textChanged.connect(self.update_text_stats)
        self.verticalScrollBar().rangeChanged.connect(self.update)
        self.verticalScrollBar().valueChanged.connect(self.update)
        self.updateLineNumbers()

        self.setStyleSheet("""
            QTextEdit {
                border: none;
            }
            QTextEdit:focus {
                border: 1px solid rgba(125, 125, 125, 0.2);
            }
        """)

        # Initialize palette
        self.default_palette = QPalette()
        self.set_selection_color(focused=False)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.set_selection_color(focused=True)
        self.update_text_stats

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.set_selection_color(focused=False)
        # global_signals.text_stats_signal.emit(" ")

    def set_selection_color(self, focused):
        palette = QPalette(self.default_palette)

        if focused:
            # Focused selection color
            palette.setColor(QPalette.ColorRole.Highlight, QColor(173, 216, 230))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        else:
            # Unfocused selection color
            palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 255, 0))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

        # Force the palette to update
        self.setPalette(palette)
        self.update()  # Trigger a repaint

    def onTextModified(self):
        self.document().setModified(True)
        self.textModified.emit()

    def update_text_stats(self):
        lineCount = 1 
        longest_line_index = 0
        longest_line_chars = 0
        block = self.document().begin()
        line_index = 0
        while block.isValid():
            block_text = block.text()
            if len(block_text) > longest_line_chars:
                longest_line_chars = len(block_text)
                longest_line_index = line_index
            line_index += 1
            block = block.next()
        global_signals.text_stats_signal.emit(f" lines: {lineCount} - longest: {longest_line_index} with {longest_line_chars} chars.")

    def copy(self):
        super().copy()

    def cut(self):
        super().cut()

    def paste(self):
        super().paste()

    def delete(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        else:
            cursor.deleteChar()

    def selectAllText(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        self.setTextCursor(cursor)

    def getCurrentFontFamily(self):
        # Use the document's default font as a fallback
        default_font = self.document().defaultFont()
        return default_font.family()

    def editorSetFontFamily(self, font_family):
        current_font = self.font()
        new_font = QFont(font_family)
        new_font.setPointSize(current_font.pointSize())
        document = self.document()
        document.setDefaultFont(new_font)
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        char_format = QTextCharFormat()
        char_format.setFont(new_font)
        cursor.mergeCharFormat(char_format)
        cursor.clearSelection()
        self.setFont(new_font)
        self.updateMarginWidth()
        self.updateLineNumbers()

    def setExactFontSize(self, size):
        if size > 8:
            current_font = self.font()
            new_font = QFont(current_font.family())
            new_font.setPointSize(size)
            document = self.document()
            document.setDefaultFont(new_font)
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            char_format = QTextCharFormat()
            char_format.setFont(new_font)
            cursor.mergeCharFormat(char_format)
            cursor.clearSelection()
            self.setFont(new_font)
            self.updateMarginWidth()
            self.updateLineNumbers()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            current_font = self.font()
            current_size = current_font.pointSize()
            if event.angleDelta().y() > 0:
                new_size = current_size + 1
            else:
                new_size = current_size - 1
            self.setExactFontSize(new_size)
        else:
            super().wheelEvent(event)


    def updateMarginWidth(self):
        countLength = len(str(self.lineCount))
        if self.lineCount < 10000:
            countLength = max(countLength, 2)

        fm = QFontMetrics(self.font())
        margin = fm.horizontalAdvance('  ' + '0' * countLength)
        self.setViewportMargins(margin, 0, 0, 0)
        self.update()

    def event(self, event):
        if event.type() == QEvent.Type.Paint:
            super().event(event)
            self.paintLineNumbers()
            return True
        return super().event(event)

    def paintLineNumbers(self):
        qp = QPainter(self)
        fm = self.fontMetrics()
        margins = self.contentsMargins()
        left = margins.left()
        viewMargin = self.viewportMargins().left()
        rightMargin = viewMargin - (fm.horizontalAdvance(' ') + left)
        qp.fillRect(0, 0, self.viewportMargins().left(), self.height(), QColor(128, 128, 128, 40))
        qp.setPen(QColor(150, 150, 150, 255))
        qp.setFont(self.font())
        viewTop = margins.top()
        viewHeight = self.height() - (viewTop + margins.bottom())
        qp.setClipRect(viewTop, margins.left(), viewMargin, viewHeight)
        qp.translate(margins.left(), 0)
        top = self.verticalScrollBar().value()
        bottom = top + viewHeight
        offset = viewTop - self.verticalScrollBar().value()
        lineCount = 1
        doc = self.document()
        docLayout = doc.documentLayout()
        block = doc.begin()

        while block.isValid():
            blockRect = docLayout.blockBoundingRect(block)
            blockTop = blockRect.y()
            blockLayout = block.layout()
            blockLineCount = blockLayout.lineCount()
            if blockRect.bottom() >= top and blockTop + offset <= bottom:
                for l in range(blockLineCount):
                    line = blockLayout.lineAt(l)
                    qp.drawText(left, int(offset + blockTop + line.y()), int(rightMargin), int(line.height()),
                                Qt.AlignmentFlag.AlignRight, str(lineCount))
                    lineCount += 1
            else:
                lineCount += blockLineCount

            block = block.next()

    def updateLineNumbers(self):
        lineCount = 0
        block = self.document().begin()
        while block.isValid():
            lineCount += block.layout().lineCount()
            block = block.next()
        if lineCount < 1:
            lineCount = 1

        if self.lineCount != lineCount:
            self.lineCount = lineCount
            self.updateMarginWidth()

        self.update()

    def find_text(self, text):
        cursor = self.textCursor()
        results = []
        while cursor:
            cursor = self.document().find(text, cursor)
            if cursor:
                results.append(cursor)
                cursor.movePosition(QTextCursor.MoveOperation.NextCharacter)
        if results:
            self.setTextCursor(results[0])
            return True
        else:
            return False

    def replace_text(self, text, replacement):
        cursor = self.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == text:
            cursor.insertText(replacement)
            return True
        return False

    def replace_all_text(self, text, replacement):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        while self.find_text(text):
            self.replace_text(text, replacement)
        cursor.endEditBlock()

    def set_word_wrap(self, wrapped):
        if wrapped == True or wrapped == "true":
            self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            self.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        else:
            self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
            self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        
        self.document().setPlainText(self.document().toPlainText())
        self.updateLineNumbers()
        self.updateMarginWidth()
        self.updateGeometry()
        self.update()
