# Jira Cloud Provider Design

## Scope

The first Jira provider targets Jira Cloud, one configured project, and personal
API-token authentication. OAuth, Jira Data Center, board administration, custom
fields, sprints, and issue creation metadata discovery are outside the MVP.

## Authentication and configuration

WorkForge uses Basic Auth with `JIRA_EMAIL` and `JIRA_API_TOKEN` against the
configured Jira Cloud `site_url`.

```yaml
providers:
  jira:
    site_url: https://example.atlassian.net
    project_key: WF
    issue_type: Task
    labels:
      feature: enhancement
    versions:
      v1: "10000"
    status:
      values:
        todo: To Do
        doing: In Progress
        review: In Review
        done: Done
```

`providers test` verifies `/rest/api/3/myself` and the configured project.

## Contract mapping

| WorkForge | Jira Cloud |
| --- | --- |
| Item | Issue |
| Item ID | Issue key, for example `WF-12` |
| Labels | Issue labels |
| Milestone | `fixVersions` ID |
| Status | Workflow transition destination |
| Assignee | Jira account ID or `currentUser()` for `@me` discovery |
| Comment | ADF issue comment |
| Discovery | Enhanced JQL search |

Jira boards are not configured because issue membership is determined by the
board's JQL filter.

## Managed tasks

The description is stored as Atlassian Document Format. WorkForge owns the
`taskList` whose `localId` is `workforge-tasks`; each `taskItem` has a stable
`workforge-task-N` ID and a `TODO` or `DONE` state. Only tasks inside that list
are read or changed by `status` and `complete-task`.

## Provider operations

- `check`: authenticate and verify project access.
- `create_requirement`: create one issue with ADF description, labels, version,
  and managed tasks.
- `get_item_status`: read issue state and managed tasks.
- `complete_task`: update one managed task marker in the description.
- `comment_item`: add an ADF paragraph comment.
- `move_item`: select an available transition by ID, name, or configured target
  status and execute it.
- `discover_items`: use paginated `POST /rest/api/3/search/jql`, filtering the
  configured project, non-Done issues, label, assignee, and status.

## Delivery slices

1. Connectivity and configuration validation.
2. Issue creation and ADF task rendering.
3. Status reading and task completion.
4. Comments and workflow transitions.
5. JQL discovery filters and real dogfooding.
6. Public example workspace, documentation, and release hardening.
