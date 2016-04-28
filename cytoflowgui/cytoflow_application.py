#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on Mar 15, 2015

@author: brian
'''

import multiprocessing

from envisage.ui.tasks.api import TasksApplication
from pyface.tasks.api import TaskWindowLayout
from traits.api import Bool, Instance, List, Property

from preferences import CytoflowPreferences
import cytoflowgui.matplotlib_backend as mpl_backend
import cytoflowgui.workflow as workflow

class CytoflowApplication(TasksApplication):
    """ The cytoflow Tasks application.
    """

    # The application's globally unique identifier.
    id = 'edu.mit.synbio.cytoflow'

    # The application's user-visible name.
    name = 'Cytoflow'

    # Override two traits from TasksApplication so we can provide defaults, below

    # The default window-level layout for the application.
    default_layout = List(TaskWindowLayout)

    # Whether to restore the previous application-level layout when the
    # applicaton is started.
    always_use_default_layout = Property(Bool)
    
    def run(self):
        # set up the child process
        workflow_parent_conn, workflow_child_conn = multiprocessing.Pipe()
        mpl_parent_conn, mpl_child_conn = multiprocessing.Pipe()

        # connect the local pipes
        workflow.child_conn = workflow_child_conn       
        mpl_backend.child_conn = mpl_child_conn   

        # start the child process
        remote_process = multiprocessing.Process(target = self._remote_main,
                                                 args = (workflow_parent_conn, 
                                                         mpl_parent_conn))
        remote_process.daemon = True
        remote_process.start()

        # run the GUI
        super(CytoflowApplication, self).run()
        
    def _remote_main(self, workflow_parent_conn, mpl_parent_conn):
        # connect the remote pipes
        workflow.parent_conn = workflow_parent_conn
        mpl_backend.parent_conn = mpl_parent_conn
        
        # run the remote workflow
        workflow.RemoteWorkflow().run()
    

    #### 'AttractorsApplication' interface ####################################

    preferences_helper = Instance(CytoflowPreferences)

    ###########################################################################
    # Private interface.
    ###########################################################################
    
    #### Trait initializers ###################################################

    def _default_layout_default(self):
        active_task = self.preferences_helper.default_task
        tasks = [ factory.id for factory in self.task_factories ]
        return [ TaskWindowLayout(*tasks,
                                  active_task = active_task,
                                  size = (800, 600)) ]

    def _preferences_helper_default(self):
        return CytoflowPreferences(preferences = self.preferences)

    #### Trait property getter/setters ########################################

    def _get_always_use_default_layout(self):
        return self.preferences_helper.always_use_default_layout
