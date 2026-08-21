# Trello Provider Design

## Scope

The Trello provider targets one board inferred from a configured destination
list. It manages cards, a WorkForge-owned `Tasks` checklist, comments, members,
labels, and list movement. Board, list, label, and member administration are
outside the scope.

## Authentication and configuration

WorkForge sends `TRELLO_API_KEY` and `TRELLO_API_TOKEN` as Trello API query
parameters.

```yaml
providers:
  trello:
    list_id: trello-todo-list-id
    lists:
      todo: trello-todo-list-id
      doing: trello-doing-list-id
      done: trello-done-list-id
    labels:
      docs: trello-label-id
```

Lists and labels must already exist. `providers test` currently validates that
the credentials and destination list are configured; it does not make a Trello
request.

## Contract mapping

| WorkForge | Trello |
| --- | --- |
| Item | Card |
| Item ID | Card ID |
| Labels | Existing label IDs |
| Milestone | Text in the card description |
| Status | Board list |
| Assignee | Board member ID, username, full name, or `@me` |
| Comment | Card action comment |
| Discovery | Open cards on the inferred board |

## Managed tasks

Requirement tasks are stored in a checklist named `Tasks`. Task references
accept a checklist item ID, an exact title, or a unique title substring. Task
synchronization recreates WorkForge-owned `Tasks` checklists and retains the
completion state of tasks with unchanged titles; other checklists are preserved.

## Provider operations

- `check`: validate required local configuration.
- `create_requirement`: create a card with mapped labels and a `Tasks` checklist.
- `get_item_status`: read card state and all checklist items.
- `update_requirement_tasks`: rebuild managed tasks while preserving completion.
- `complete_task`: complete one checklist item.
- `comment_item`: add a card comment.
- `move_item`: move the card to a list ID or configured status alias.
- `claim_item`: add a resolved board member to the card.
- `discover_items`: list open board cards and filter by label, member, and list.

## Failure behavior and limits

HTTP failures propagate without exposing credentials in WorkForge-generated
messages. Card creation and subsequent checklist creation are separate Trello
operations: if checklist creation fails, the card remains and retrying creation
can create a duplicate. Discovery fetches the board's open cards in one request;
there is no background synchronization or webhook support.
