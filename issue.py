from PySide import QtGui, QtCore, QtSvg
import urllib2
import json
import jira_backend
import datetime
import issue_details
import webbrowser

class IssueCard(QtGui.QFrame):

    def __init__(self, issue_dict):
        QtGui.QFrame.__init__(self)

        self.id = issue_dict['id']
        self.key = issue_dict['key']
        self.me = issue_dict['self']
        self.assignee = issue_dict['fields']['assignee']
        if self.assignee is not None and self.assignee.has_key('avatarUrls'):
            self.assignee_avatar = self.assignee['avatarUrls']['24x24']
        self.created = issue_dict['fields']['created']
        self.creator = issue_dict['fields']['creator']
        self.creator = issue_dict['fields']['creator']
        self.project = issue_dict['fields']['project']
        self.status = issue_dict['fields']['status']
        self.summary = issue_dict['fields']['summary']
        self.issue_type = issue_dict['fields']['issuetype']
        self.goto_link = '{1}{0}'.format(self.key, jira_backend.data['goto_link'])

        self.resolution_date = issue_dict['fields']['resolutiondate']

        self.issue_dict = issue_dict
        self.issue_transition = jira_backend.get_issue_transistions(self.id)
        self.transition_statuses = {}
        self.get_transition_status()

        self.timer_display = None

        self.session_time_start = None
        self.session_time_end = None

        if issue_dict['fields'].has_key('parent'):
            self.parent = issue_dict['fields']['parent']
            self.parent_fields = self.parent['fields']

        self.grid_layout = None
 
        self.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
        self.setGeometry(30, 40, 200, 100)
        self.setup_ui()
        self.set_card_color()

    def GetData(self):
        return self.issue_dict

    def log_start_time(self):
        self.session_time_start = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.issue_dict['session_time_start'] = self.session_time_start
        print 'test'

    def log_end_time(self, comment=None):
        if self.issue_dict.has_key('session_time_start'):
            self.session_time_start = self.issue_dict['session_time_start']
            if self.session_time_start:
                diff = datetime.datetime.now() - datetime.datetime.strptime(self.session_time_start, '%d/%m/%Y %H:%M:%S')
                # Turn time into seconds and log to jira
                time_in_seconds = int(diff.total_seconds())
                if comment is None:
                    comment = "Automated from Jira Tracker App"
                jira_backend.log_time_against_issue(self.id, time_in_seconds, comment)
                self.session_time_start = None

    def get_time(self, seconds):
        return str(datetime.timedelta(seconds=seconds))

    def set_status(self, requested_status):
        status_to_set = ''
        print requested_status
        print self.transition_statuses
        self.timer_display.hide()
        if 'In Progress' in requested_status:
            self.log_start_time()
            if self.transition_statuses.has_key('In Progress'):
                status_to_set = self.transition_statuses['In Progress']
            else:
                status_to_set = self.transition_statuses['Start work']

            self.timer_display.show()
        
        if 'To Do' in requested_status:
            self.log_end_time()
            if self.transition_statuses.has_key('To Do'):
                status_to_set = self.transition_statuses['To Do']
            elif self.transition_statuses.has_key('Open'):
                status_to_set = self.transition_statuses['Open']
            elif self.transition_statuses.has_key('Reopened'):
                status_to_set = self.transition_statuses['Reopened']
            elif self.transition_statuses.has_key('Set as open'):
                status_to_set = self.transition_statuses['Set as open']
        
        if 'Done' in requested_status:
            self.log_end_time()
            if self.transition_statuses.has_key('Done'):
                status_to_set = self.transition_statuses['Done']
            else:
                status_to_set = self.transition_statuses['Set as done']
            
        status_to_set = status_to_set.encode('ascii', 'ignore')
        jira_backend.set_issue_status(self.id, status_to_set)

    def get_transition_status(self):
        for transition in self.issue_transition['transitions']:
            self.transition_statuses[transition['name']] = transition['id']
        
    def set_card_color(self):
        task_type = self.issue_type['name']
        if 'Sub-task' in task_type:
            self.setStyleSheet("background-color:#b6b9e0;border: 1px solid black;")
        elif 'Story' in task_type:
            self.setStyleSheet("background-color:#6f73ad;border: 1px solid black;")
        else:
            self.setStyleSheet("background-color:#b6e0cb;border: 1px solid black;")
            
    def setup_ui(self):
        self.grid_layout = QtGui.QGridLayout(self)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)
        self.grid_layout.setHorizontalSpacing(0)
        self.grid_layout.setVerticalSpacing(2)

        summary = QtGui.QLabel(self.summary)
        summary.setWordWrap(True)
        key = QtGui.QLabel(self.key)
        key.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        if self.issue_dict['fields'].has_key('timespent') and type(self.issue_dict['fields']['timespent']) is int:
            time_spent = QtGui.QLabel(self.get_time(self.issue_dict['fields']['timespent']))
        else:
             time_spent = QtGui.QLabel('None')
        time_spent.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.timer_display = QtGui.QLabel('0 s')
        self.timer_display.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        if self.assignee is not None:
            data = urllib2.urlopen(self.assignee_avatar).read()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            
            avatar = QtGui.QLabel()
            avatar.setPixmap(pixmap.scaled(30, 30, QtCore.Qt.KeepAspectRatio) )
            avatar.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            self.grid_layout.addWidget(avatar, 2, 3, 1, 1)

        if self.issue_type is not None:
            data = urllib2.urlopen(self.issue_type['iconUrl']).read()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(data)
            
            type_icon = QtGui.QLabel()
            type_icon.setPixmap(pixmap.scaled(20, 20, QtCore.Qt.KeepAspectRatio) )
            type_icon.setGeometry(QtCore.QRect(10, 40, 15, 15))

            self.grid_layout.addWidget(type_icon, 2, 0, 1, 1)

        goto_link_btn = QtGui.QPushButton('Go To Issue')
        goto_link_btn.clicked.connect(self.goto_issue)

        self.grid_layout.addWidget(summary, 0, 0, 1, 4)
        self.grid_layout.addWidget(time_spent, 1, 0, 1, 2)
        self.grid_layout.addWidget(key, 2, 1, 1, 2)
        self.grid_layout.addWidget(goto_link_btn, 1,2,1,1)
        

        self.setLayout(self.grid_layout)

    def goto_issue(self):
        webbrowser.open(self.goto_link, new=2)

    def mouseDoubleClickEvent(self, event):
        details_window = issue_details.IssueDetails(self)