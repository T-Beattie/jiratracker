from PySide import QtGui, QtCore
import issue
import jira_backend

class SprintTracker(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.team = jira_backend.data['project']
        self.resize(700, 600)
        self.setWindowTitle('{0} Sprint Tracker'.format(self.team))
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
        for story_key, sub_task in self.user_story_tasks.iteritems():
            my_user_story = None
            for user_story in self.user_stories:
                if story_key in user_story['key']:
                    card_ui = CardUI(user_story, self.user_story_tasks[story_key])
                    my_item = QtGui.QListWidgetItem(self.list_widget)
                    my_item.setSizeHint(QtCore.QSize(200,100))
                    self.list_widget.addItem(my_item)
                    self.list_widget.setItemWidget(my_item, card_ui)
                    break
            



class CardUI(QtGui.QFrame):
    def __init__(self, user_story, sub_tasks):
        QtGui.QFrame.__init__(self)
        self.user_story = user_story
        self.sub_tasks = sub_tasks
        self.build_ui()

    def build_ui(self):
        vert_layout = QtGui.QVBoxLayout()

        sprint_label = QtGui.QLabel()
        sprint_label.setText('{key} - {summary}'.format(
            key=self.user_story['key'], 
            summary=self.user_story['fields']['summary']
            )
        )

        vert_layout.addWidget(sprint_label)
        self.setLayout(vert_layout)
