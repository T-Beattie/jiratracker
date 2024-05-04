import jira_backend
import issue
import os
import sys
import json
from PySide import QtGui, QtCore
import settings
import sprint_tracker
import relevant_issues
import requests
import datetime
import utilities

class JiraTracker(QtGui.QMainWindow):

    def __init__(self):
        super(JiraTracker, self).__init__()
        self.setGeometry(300, 100, 900, 900)
        self.setWindowTitle('Jira Tracker')
        self.meeting_mode_active = False
        self.lunch_mtg_button = None
        self.active_issues_while_in_meeting = []

        self.issues = []

        self.todo_list = []
        self.in_progress_list = []
        self.done_list = []

        self.todo_list_Widget = IssuesListWidget(self, 'To Do')
        self.in_progress_list_widget = IssuesListWidget(self, 'In Progress')
        self.done_list_widget = IssuesListWidget(self, 'Done')

        # jira_backend.get_all_issues_user_has_commented_on('Thomas Beattie')

        self.retrieve_issues()
        self.organize_cards()

        self.setup_ui()
        self.show()


    def organize_cards(self):
        for my_issue in self.issues:
            issue_status = my_issue.status['name'].encode('ascii', 'ignore')
            if 'To Do' in issue_status or 'Open' in issue_status or 'Reopened' in issue_status:
                self.todo_list.append(my_issue)
            elif 'In Progress' in issue_status or 'Work in progress' in issue_status:
                self.in_progress_list.append(my_issue)
            elif 'Done' in issue_status: 
                # Only show cards where resolution date is within 2 weeks
                resolution_date = my_issue.resolution_date
                if resolution_date:
                    dt_resolution_date = utilities.ConvertStringToDateTime(resolution_date).replace(tzinfo=None)
                    time_between_resoltuion = datetime.datetime.now() - dt_resolution_date
                    if time_between_resoltuion.days < 15:
                        self.done_list.append(my_issue)

        for my_issue in self.todo_list:
            self.add_card_to_lane(my_issue, self.todo_list_Widget)
        for my_issue in self.in_progress_list:
            self.add_card_to_lane(my_issue, self.in_progress_list_widget)
        for my_issue in self.done_list:
            self.add_card_to_lane(my_issue, self.done_list_widget)
    
    def add_card_to_lane(self, issue_card, lane):
        my_item = QtGui.QListWidgetItem(lane)
        my_item.setData(QtCore.Qt.UserRole, json.dumps(issue_card.issue_dict))
        my_item.setSizeHint(QtCore.QSize(200,100))

        if lane:
            lane.addItem(my_item)
            lane.setItemWidget(my_item, issue_card)

    def setup_ui(self):
        widget = QtGui.QWidget()

        self.setup_menu()
        v_layout = QtGui.QVBoxLayout()
       
        layout = QtGui.QHBoxLayout()

        todo_wid = QtGui.QWidget()
        todo_layout = QtGui.QVBoxLayout()
        todo_label = QtGui.QLabel('TODO')
        todo_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        todo_layout.addWidget(todo_label)
        todo_layout.addWidget(self.todo_list_Widget)
        todo_wid.setLayout(todo_layout)

        ip_wid = QtGui.QWidget()
        ip_layout = QtGui.QVBoxLayout()
        ip_label = QtGui.QLabel('In Progress')
        ip_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.in_progress_list_widget)
        ip_wid.setLayout(ip_layout)

        done_wid = QtGui.QWidget()
        done_layout = QtGui.QVBoxLayout()
        done_label = QtGui.QLabel('Done')
        done_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        done_layout.addWidget(done_label)
        done_layout.addWidget(self.done_list_widget)
        done_wid.setLayout(done_layout)
                       
        layout.addWidget(todo_wid)
        layout.addWidget(ip_wid)
        layout.addWidget(done_wid)  


        self.lunch_mtg_button = QtGui.QPushButton()  
        self.lunch_mtg_button.setMinimumHeight(50)
        self.lunch_mtg_button.setText('Lunch/Meeting Mode')    
        self.lunch_mtg_button.setToolTip('When enabled it will pause all timers')
        self.lunch_mtg_button.clicked.connect(self.trigger_meeting_mode)

        widget.setLayout(layout)

        v_layout.addWidget(self.lunch_mtg_button)
        v_layout.addWidget(widget)

        v_widget = QtGui.QWidget()
        v_widget.setLayout(v_layout)
        
        self.setCentralWidget(v_widget)

    def trigger_meeting_mode(self):
        self.meeting_mode_active = not self.meeting_mode_active

        if self.meeting_mode_active:
            self.lunch_mtg_button.setText('Lunch/Meeting Mode - ACTIVE')
            self.lunch_mtg_button.setStyleSheet('background-color: #b1ff75')

            for item in self.in_progress_list:
                item.log_end_time(comment="Logging time due to meeting/Lunch")
        else:

            self.lunch_mtg_button.setText('Lunch/Meeting Mode')
            self.lunch_mtg_button.setStyleSheet('background-color: #d4d4d4') 

            for item in self.in_progress_list:
                item.log_start_time()           

    def setup_menu(self):
        exitAction = QtGui.QAction('Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        credentials_action = QtGui.QAction('Credentials', self)
        credentials_action.setShortcut('Shift+C')
        credentials_action.setStatusTip('Edit Credentials')
        credentials_action.triggered.connect(self.open_credential_manager)

        show_sprint_action = QtGui.QAction('Sprint', self)
        show_sprint_action.setShortcut('Shift+S')
        show_sprint_action.setStatusTip('Exit application')
        show_sprint_action.triggered.connect(self.open_sprint_tracker)

        show_unassigned_action = QtGui.QAction('Unassigned', self)
        show_unassigned_action.setShortcut('Shift+U')
        show_unassigned_action.setStatusTip('Exit application')
        show_unassigned_action.triggered.connect(self.open_sprint_tracker)

        show_relevant_tickets_action = QtGui.QAction('Relevant Tickets', self)
        show_relevant_tickets_action.setShortcut('Shift+R')
        show_relevant_tickets_action.setStatusTip('Exit application')
        show_relevant_tickets_action.triggered.connect(self.open_relevant_issues)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Settings')
        fileMenu.addAction(credentials_action)
        fileMenu.addAction(exitAction)

        menubar.addAction(show_sprint_action)
        menubar.addAction(show_unassigned_action)
        menubar.addAction(show_relevant_tickets_action)

    def open_credential_manager(self):
        credentials = CredentialsWidget()

    def open_sprint_tracker(self):
        s_tracker = sprint_tracker.SprintTracker()    

    def open_relevant_issues(self):
        s_tracker = relevant_issues.RelevantIssues()           

    def retrieve_issues(self):
        my_issues_raw =  jira_backend.get_issues_from_filter()

        for my_issue_raw in my_issues_raw:
            self.issues.append(issue.IssueCard(my_issue_raw))


class IssuesListWidget(QtGui.QListWidget):
    def __init__(self, type, status_name, parent=None):
        super(IssuesListWidget, self).__init__(parent)
        self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setStyleSheet("QListWidget::item { margin-bottom: 5px; }")

        self.status_name = status_name

    def startDrag(self, supportedActions):
        drag = QtGui.QDrag(self)
        test = self.selectedItems()[0].data(QtCore.Qt.UserRole)
        mimeData = self.model().mimeData(self.selectedIndexes())
        mimeData.setText(test)
        drag.setMimeData(mimeData)
        if drag.start(QtCore.Qt.MoveAction) == QtCore.Qt.MoveAction:
            for item in self.selectedItems():
                self.takeItem(self.row(item))
    
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.ignore()
        if isinstance(event.source(), IssuesListWidget):
            event.setDropAction(QtCore.Qt.MoveAction)
            self.populate_drop(event.mimeData().text())
        else:
            event.ignore()

    def populate_drop(self, data):
        my_issue = json.loads(data)
        issue_card = issue.IssueCard(my_issue)

        issue_card.set_status(self.status_name)

        item = QtGui.QListWidgetItem()
        item.setSizeHint(QtCore.QSize(200,100))
        item.setData(QtCore.Qt.UserRole, json.dumps(issue_card.issue_dict))
        item.setText(data)

        self.addItem(item)
        self.setItemWidget(item,issue_card)

class CredentialsWidget(QtGui.QWidget):    
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.issue = issue
        self.resize(400, 200)
        self.setWindowTitle('Credential Manager')
        self.email_edit = QtGui.QLineEdit()
        self.api_key_edit = QtGui.QLineEdit()
        self.setup_ui()
        

        self.show()
        self.exec_()
    
    def setup_ui(self):
        layout = QtGui.QVBoxLayout()

        email, api_key = jira_backend.load_credentials()

        email_label = QtGui.QLabel('Email')
        layout.addWidget(email_label)
        self.email_edit.setText(email)
        layout.addWidget(self.email_edit)

        api_key_label = QtGui.QLabel('API Key')
        layout.addWidget(api_key_label)
        self.api_key_edit.setText(api_key)
        layout.addWidget(self.api_key_edit)

        api_key_info = QtGui.QLabel('How to get your Key: Navigate to https://id.atlassian.com/manage-profile/security/api-tokens and generate your key. Once created copy and paste it here')
        layout.addWidget(api_key_info)

        update_btn = QtGui.QPushButton('Update')
        update_btn.clicked.connect(self.save_credentials)
        layout.addWidget(update_btn)

        self.setLayout(layout)

    def save_credentials(self):
        cred_dict = {}

        cred_dict['email'] = self.email_edit.text()
        cred_dict['api_key'] = self.api_key_edit.text()

        with open('credentials.json', 'w') as outfile:
            json.dump(cred_dict, outfile)


def main():
    application = QtGui.QApplication(sys.argv)
    window = JiraTracker()
    window.show()
    sys.exit(application.exec_())


if __name__ == '__main__':
    main()