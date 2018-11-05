"""SODAR Taskflow API for Django apps"""
import requests
from uuid import UUID

from django.conf import settings

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


# Local constants
HEADERS = {'Content-Type': 'application/json'}
TARGETS = settings.TASKFLOW_TARGETS if \
    hasattr(settings, 'TASKFLOW_TARGETS') else ['sodar']
TEST_MODE = True if (
    hasattr(settings, 'TASKFLOW_TEST_MODE') and
    settings.TASKFLOW_TEST_MODE) else False

class TaskflowAPI:
    """Taskflow API to be used by Django apps"""

    class FlowSubmitException(Exception):
        """SODAR Taskflow submission exception"""
        pass

    class CleanupException(Exception):
        """SODAR Taskflow cleanup exception"""
        pass

    def __init__(self):
        self.taskflow_url = '{}:{}'.format(
            settings.TASKFLOW_BACKEND_HOST, settings.TASKFLOW_BACKEND_PORT)

    def submit(
            self, project_uuid, flow_name, flow_data, request=None,
            targets=TARGETS, request_mode='sync', timeline_uuid=None,
            force_fail=False, sodar_url=None):
        """
        Submit taskflow for project data modification.
        :param project_uuid: UUID of the project (UUID object or string)
        :param flow_name: Name of flow to be executed (string)
        :param flow_data: Input data for flow execution (dict)
        :param request: Request object (optional)
        :param targets: Names of backends to sync with (list)
        :param request_mode: "sync" or "async"
        :param timeline_uuid: UUID of corresponding timeline event (optional)
        :param force_fail: Make flow fail on purpose (boolean, default False)
        :param sodar_url: URL of SODAR server (optional, for testing)
        :return: Boolean, status info if failure (string)
        """
        url = self.taskflow_url + '/submit'

        # Format UUIDs in flow_data
        for k, v in flow_data.items():
            if type(v) == UUID:
                flow_data[k] = str(v)

        data = {
            'project_uuid': str(project_uuid),
            'flow_name': flow_name,
            'flow_data': flow_data,
            'request_mode': request_mode,
            'targets': targets,
            'force_fail': force_fail,
            'timeline_uuid': str(timeline_uuid)}

        # Add the "test_mode" parameter
        data['test_mode'] = TEST_MODE

        # HACK: Add overriding URL for test server
        if request:
            if request.POST and 'sodar_url' in request.POST:
                data['sodar_url'] = request.POST['sodar_url']

            elif request.GET and 'sodar_url' in request.GET:
                data['sodar_url'] = request.GET['sodar_url']

        elif sodar_url:
            data['sodar_url'] = sodar_url

        # print('DATA: {}'.format(data))  # DEBUG
        response = requests.post(url, json=data, headers=HEADERS)

        if response.status_code == 200 and bool(response.text) is True:
            return True

        else:
            print('Submit Response (url={}): {}'.format(
                url, response.text))    # DEBUG
            raise self.FlowSubmitException(
                self.get_error_msg(flow_name, response.text))

    def use_taskflow(self, project):
        """
        Return True/False regarding if taskflow should be used with a project
        :param project: Project object
        :return: bool
        """
        return True if project.type == PROJECT_TYPE_PROJECT else False

    def cleanup(self):
        """Send a cleanup command to SODAR Taskflow"""
        url = self.taskflow_url + '/cleanup'
        data = {'test_mode': TEST_MODE}

        response = requests.post(url, json=data, headers=HEADERS)

        if response.status_code == 200:
            return True

        else:
            # print('Cleanup Response: {}'.format(response.text))  # DEBUG
            raise self.FlowSubmitException(response.text)

    def get_error_msg(self, flow_name, submit_info):
        return 'Taskflow "{}" failed! Reason: "{}"'.format(
            flow_name, submit_info[:256])
