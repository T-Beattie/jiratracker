from PySide import QtGui, QtCore
import issue
import jira_backend
import webbrowser

class RelevantIssues(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.team = jira_backend.data['project']
        self.resize(700, 600)
        self.setWindowTitle('{0} Relevant Issues for User'.format(self.team))
        self.sprint_issues = []

        self.user_stories = []
        self.user_story_tasks = {}

        self.list_widget = QtGui.QListWidget()

        self.retrieve_current_sprint()
        self.build_ui()
        self.show()
        self.exec_()

    def build_ui(self):       
        layout = QtGui.QHBoxLayout()
                       
        layout.addWidget(self.list_widget)
        self.build_cards()

        self.setLayout(layout)       

    
    def retrieve_current_sprint(self):
        self.sprint_issues = jira_backend.get_sprint_issues(self.team)
        self.sort_user_stories()

    def sort_user_stories(self):
        for issue in self.sprint_issues:
            issue_type = issue['fields']['issuetype']['name']
            issue_parent = ''
            if issue['fields'].has_key('parent'):
                issue_parent = issue['fields']['parent']['key']

            if 'Story' in issue_type:
                self.user_stories.append(issue)
            elif 'Sub-task' in issue_type:
                if self.user_story_tasks.has_key(issue_parent):
                    self.user_story_tasks[issue_parent].append(issue)
                else:
                    self.user_story_tasks[issue_parent] = [issue]


    def build_cards(self):
        relevant_issues = jira_backend.get_all_issues_user_has_commented_on(jira_backend.data['assignee'])

        for issue_id, issue_content in relevant_issues.iteritems():
            card_ui = CardUI(issue_content[0], [issue_content[1]])
            my_item = QtGui.QListWidgetItem(self.list_widget)
            my_item.setSizeHint(QtCore.QSize(200,100))
            self.list_widget.addItem(my_item)
            self.list_widget.setItemWidget(my_item, card_ui)          



class CardUI(QtGui.QFrame):
    def __init__(self, issue, comment):
        QtGui.QFrame.__init__(self)
        self.issue = issue
        self.comment = comment

        self.goto_link = '{1}{0}'.format(self.issue['key'], jira_backend.data['goto_link'])
        self.build_ui()

    def build_ui(self):
        vert_layout = QtGui.QVBoxLayout()

        sprint_label = QtGui.QLabel()
        sprint_label.setText('{key} - {summary}'.format(
            key=self.issue['key'], 
            summary=self.issue['fields']['summary']
            )
        )

        if len(self.comment) > 0:
            comment_date = QtGui.QLabel()
            comment_date.setText('Date you commented - {date}'.format(date=self.comment[0]['created']))

        goto_link_btn = QtGui.QPushButton('Go To Issue')
        goto_link_btn.clicked.connect(self.goto_issue)

        # comment_label = QtGui.QLabel()
        # try:
        #     comment_label.setText('Your Comment - {0}'.format(
        #         self.comment[0]['body']['content'][0]['content'][0]['text']
        #         )
        #     )
        # except UnicodeEncodeError:
        #     pass

        vert_layout.addWidget(sprint_label)
        if len(self.comment) > 0:
            vert_layout.addWidget(comment_date)
        vert_layout.addWidget(goto_link_btn)
        self.setLayout(vert_layout)

    def goto_issue(self):
        webbrowser.open(self.goto_link, new=2)
