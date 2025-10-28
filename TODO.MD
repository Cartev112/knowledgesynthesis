BUGS

- Global view workspace cards/modal is showing 0 entities + 0 relationships [FIXED - NEEDS DEPLOY]
  * Added /api/workspaces/global/stats endpoint to get real counts
  * Updated frontend to call new endpoint
  * Fixed workspace stats query to count relationships properly
  * Files: workspaces.py, workspaces.js, workspace_service.py

- public workspaces are not appearing to others [FIXED - NEEDS DEPLOY]
  * Updated list_user_workspaces query to include public workspaces
  * File: workspace_service.py

- ingestion container looks much smaller on someone elses computer

- remove entity type ingestion

- graph context prompt should NOT assume goals; just incorporate the context

- graph is resetting node/document/relationship selections after moving to another tab (should not reset)

- when documents are selected, automatically select all of their nodes + relationships for graph context

- ingestion LLM is not generating enough triplets. should be very close to specificied maximum. (batch WHILE minimizing redundancy)

- figure out why email service is not working (sendgrid)

