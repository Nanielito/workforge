# GitHub Projects Provider Design

## Scope

The GitHub provider targets GitHub Issues in one repository and one personal
GitHub Project v2. Organization-owned projects, Projects classic, pull requests,
draft items, sub-issues, resource administration, and webhooks are outside the
current scope.

## Authentication and configuration

WorkForge uses `GITHUB_TOKEN` for REST and GraphQL requests. The token needs
read/write access to repository issues and the configured Project v2.

```yaml
providers:
  github:
    owner: github-user
    repository: workforge
    project_number: 1
    labels:
      docs: documentation
    milestones:
      v2: 1
    status:
      field: Status
      values:
        todo: Todo
        doing: In Progress
        done: Done
```

Labels, milestones, project fields, and status options must already exist.
`providers test` validates the token, repository, and project without mutating
GitHub.

## Contract mapping

| WorkForge | GitHub |
| --- | --- |
| Item | Repository issue added to a Project v2 |
| Item ID | Issue number |
| Labels | Existing repository label names |
| Milestone | Existing repository milestone number |
| Status | Project v2 single-select option |
| Assignee | GitHub login or the authenticated user for `@me` |
| Comment | Issue comment |
| Discovery | Project v2 items |

## Managed tasks

Tasks are Markdown checkboxes under a `## Tasks` heading in the issue body.
WorkForge reads and updates only that section and preserves other body content.
Task references accept a generated index, an exact title, or a unique title
substring.

## Provider operations

- `check`: authenticate and verify repository and Project v2 access.
- `create_requirement`: create an issue, map configured labels and milestone,
  render tasks, and add the issue to the project.
- `get_item_status`: read issue state and managed task checkboxes.
- `update_requirement_tasks`: replace the managed task list while retaining
  completion state for tasks with unchanged titles.
- `complete_task`: mark one managed checkbox complete.
- `comment_item`: add an issue comment.
- `move_item`: update the configured Project v2 Status field.
- `claim_item`: assign the issue to a login or the authenticated user.
- `discover_items`: paginate project items and filter open issues by repository,
  label, assignee, and configured status.

## Failure behavior and limits

Configuration is validated before requests and GraphQL errors are converted to
secret-safe messages. If issue creation succeeds but adding it to the project
fails, WorkForge reports the created issue URL for manual recovery; it does not
delete or close the issue. Creation is not idempotent, so retrying that partial
failure can create another issue.
