from PySide import QtGui, QtCore
import jira_backend
import urllib2

class IssueDetails(QtGui.QWidget):

    def __init__(self, issue):
        QtGui.QWidget.__init__(self)
        self.issue = issue
        self.resize(700, 600)
        self.setWindowTitle('{0} Details'.format(self.issue.key))
        self.comments = None
        self.comments_list = None
        self.send_public_comment = False    
        self.button_widget = QtGui.QWidget()
        self.comment_widget = QtGui.QWidget()
        self.comment_box = GrowingTextEdit()

        self.setup_ui()
        self.create_comment_stream()   

        self.show()
        self.exec_()

    def setup_ui(self):
        self.comments_list = QtGui.QListWidget(self)
        layout = QtGui.QVBoxLayout()
                       
        layout.addWidget(self.comments_list)  

        button_layout = QtGui.QHBoxLayout()
        internal_comment_btn = QtGui.QPushButton('Internal Comment')
        internal_comment_btn.clicked.connect(self.internal_btn_clicked)
        customer_comment_btn = QtGui.QPushButton('Customer Comment')
        customer_comment_btn.clicked.connect(self.customer_btn_clicked)

        button_layout.addWidget(internal_comment_btn)
        button_layout.addWidget(customer_comment_btn)

        self.button_widget.setLayout(button_layout)

        comment_layout = QtGui.QHBoxLayout()
        attach_image_btn = QtGui.QPushButton('Attach')
        send_btn = QtGui.QPushButton('Send')
        send_btn.clicked.connect(self.send_clicked)

        comment_layout.addWidget(self.comment_box)
        comment_layout.addWidget(attach_image_btn)
        comment_layout.addWidget(send_btn)
        self.comment_widget.setLayout(comment_layout)

        layout.addWidget(self.button_widget) 

        layout.addWidget(self.comment_widget)
        self.comment_widget.hide()

        self.setLayout(layout)


    def send_clicked(self):
        jira_backend.post_comment(
            self.issue.id, 
            self.comment_box.toPlainText(), 
            self.send_public_comment
        )
        self.button_widget.show()
        self.comment_widget.hide()
            
        self.create_comment_stream()

    def internal_btn_clicked(self):
        self.send_public_comment = False
        self.display_comment_widget()

    def customer_btn_clicked(self):
        self.send_public_comment = True
        self.display_comment_widget()
    
    def display_comment_widget(self):
        self.button_widget.hide()
        self.comment_widget.show()
    
    def create_comment_stream(self):
        self.comments_list.clear()
        self.comments = jira_backend.get_issue_comments(self.issue.id)

        for comment in self.comments['comments']:
            comment_ui = CommentUI(comment)
            my_item = QtGui.QListWidgetItem(self.comments_list)
            my_item.setSizeHint(QtCore.QSize(100,100))
            self.comments_list.addItem(my_item)
            self.comments_list.setItemWidget(my_item, comment_ui)     


class CommentUI(QtGui.QFrame):

    def __init__(self, comment):
        QtGui.QFrame.__init__(self)
        self.setStyleSheet('background-color:#b6b9e0;')
        self.setGeometry(30, 40, 50, 50)
        self.author = comment['author']['displayName']
        self.avatar = comment['author']['avatarUrls']['24x24']
        self.content = comment['body']['content'][0]['content'][0]['text']
        self.created = comment['created']
        self.updated = comment['updated']
        self.is_public = comment['jsdPublic']

        self.setup_ui()

    def setup_ui(self):
        self.grid_layout = QtGui.QGridLayout(self)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        self.grid_layout.setHorizontalSpacing(0)
        self.grid_layout.setVerticalSpacing(2)

        if self.avatar:
            data = urllib2.urlopen(self.avatar).read()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            
            avatar = QtGui.QLabel()
            avatar.setPixmap(pixmap.scaled(30, 30, QtCore.Qt.KeepAspectRatio) )
            avatar.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

            self.grid_layout.addWidget(avatar, 0, 0, 1, 1)
        
        author_label = QtGui.QLabel(self.author)
        self.grid_layout.addWidget(author_label, 0, 1 ,1, 2)

        date_label = QtGui.QLabel(self.created)
        self.grid_layout.addWidget(date_label, 0, 3 ,1, 2)

        internal_note_label = QtGui.QLabel('')
        if self.is_public:
            internal_note_label.setText('Public Note')
        else:
            internal_note_label.setText('Internal Note')
        self.grid_layout.addWidget(internal_note_label, 1,0, 1, 1)

        content_label = QtGui.QLabel(self.content)
        self.grid_layout.addWidget(content_label, 1,1,1,3)
        

        self.setLayout(self.grid_layout)


class GrowingTextEdit(QtGui.QTextEdit):

    def __init__(self, *args, **kwargs):
        super(GrowingTextEdit, self).__init__(*args, **kwargs)  
        self.document().contentsChanged.connect(self.sizeChange)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        self.setMinimumWidth(400)
        self.setMinimumHeight(50)
        self.heightMin = 0
        self.heightMax = 65000

    def sizeChange(self):
        docHeight = self.document().size().height()
        if self.heightMin <= docHeight <= self.heightMax:
            self.setMinimumHeight(docHeight)

